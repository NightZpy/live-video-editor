"""
Video Player Manager
Handles video playback using OpenCV with memory optimization
"""

import cv2
import threading
import time
from typing import Optional, Callable, Tuple, Any
from pathlib import Path
import tkinter as tk

# Import PIL with proper error handling
PIL_AVAILABLE = False
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✅ PIL/Pillow imported successfully")
except ImportError as e:
    print(f"❌ PIL not available: {e}")
    # Create placeholder classes to avoid NameError
    class _DummyPIL:
        pass
    Image = _DummyPIL()
    ImageTk = _DummyPIL()


class VideoPlayerManager:
    """
    Efficient video player that loads video once and handles multiple cut previews
    """
    
    def __init__(self):
        self.video_path: Optional[str] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_loaded = False
        
        # Video properties
        self.fps = 0
        self.total_frames = 0
        self.duration_seconds = 0
        self.frame_width = 0
        self.frame_height = 0
        
        # Playback state
        self.is_playing = False
        self.current_frame = 0
        self.current_time = 0.0
        
        # Cut boundaries for playback
        self.cut_start_time = 0.0
        self.cut_end_time = 0.0
        
        # Threading for playback
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback_flag = False
        
        # Callbacks
        self.frame_callback: Optional[Callable] = None
        self.time_callback: Optional[Callable] = None
        self.end_callback: Optional[Callable] = None
    
    def load_video(self, video_path: str) -> bool:
        """
        Load video file (only once for efficiency)
        
        Args:
            video_path: Path to the video file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if self.video_path == video_path and self.is_loaded:
            # Video already loaded, no need to reload
            return True
        
        # Release previous video if any
        self.release()
        
        try:
            self.cap = cv2.VideoCapture(video_path)
            
            if not self.cap.isOpened():
                return False
            
            # Get video properties
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            self.duration_seconds = self.total_frames / self.fps if self.fps > 0 else 0
            
            self.video_path = video_path
            self.is_loaded = True
            
            return True
            
        except Exception as e:
            print(f"Error loading video: {e}")
            return False
    
    def set_cut_boundaries(self, start_time: float, end_time: float):
        """
        Set the boundaries for cut playback
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
        """
        self.cut_start_time = max(0, start_time)
        self.cut_end_time = min(self.duration_seconds, end_time)
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """
        Seek to specific time in the video
        
        Args:
            time_seconds: Time to seek to in seconds
            
        Returns:
            True if seek was successful
        """
        if not self.is_loaded or not self.cap:
            return False
        
        # Clamp time to cut boundaries
        time_seconds = max(self.cut_start_time, min(self.cut_end_time, time_seconds))
        
        frame_number = int(time_seconds * self.fps)
        frame_number = max(0, min(self.total_frames - 1, frame_number))
        
        success = self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        if success:
            self.current_frame = frame_number
            self.current_time = time_seconds
            
            # Read and return current frame
            ret, frame = self.cap.read()
            if ret and self.frame_callback:
                self.frame_callback(frame, time_seconds)
        
        return success
    
    def get_current_frame(self) -> Optional[Tuple[bool, Any]]:
        """
        Get the current frame without advancing
        
        Returns:
            Tuple of (success, frame) or None if not loaded
        """
        if not self.is_loaded or not self.cap:
            return None
        
        # Store current position
        current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        
        # Read frame
        ret, frame = self.cap.read()
        
        # Restore position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
        
        return ret, frame
    
    def play(self):
        """Start playback from current position"""
        if not self.is_loaded or self.is_playing:
            return
        
        self.is_playing = True
        self.stop_playback_flag = False
        
        # Start playback thread
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
        self.stop_playback_flag = True
    
    def stop(self):
        """Stop playback and seek to cut start"""
        self.is_playing = False
        self.stop_playback_flag = True
        
        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        
        # Seek to cut start
        self.seek_to_time(self.cut_start_time)
    
    def _playback_loop(self):
        """Main playback loop (runs in separate thread)"""
        if not self.is_loaded or not self.cap:
            return
        
        frame_time = 1.0 / self.fps if self.fps > 0 else 1.0 / 30.0
        
        while self.is_playing and not self.stop_playback_flag:
            start_time = time.time()
            
            # Read next frame
            ret, frame = self.cap.read()
            
            if not ret:
                # End of video or error
                self.is_playing = False
                if self.end_callback:
                    self.end_callback()
                break
            
            # Update current position
            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.current_time = self.current_frame / self.fps
            
            # Check if we've reached the end of the cut
            if self.current_time >= self.cut_end_time:
                self.is_playing = False
                if self.end_callback:
                    self.end_callback()
                break
            
            # Send frame to callback
            if self.frame_callback:
                self.frame_callback(frame, self.current_time)
            
            # Send time update to callback
            if self.time_callback:
                self.time_callback(self.current_time)
            
            # Frame rate control
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def set_callbacks(self, 
                     frame_callback: Optional[Callable] = None,
                     time_callback: Optional[Callable] = None, 
                     end_callback: Optional[Callable] = None):
        """
        Set callback functions for video events
        
        Args:
            frame_callback: Called with (frame, time_seconds) for each frame
            time_callback: Called with current time_seconds
            end_callback: Called when playback ends
        """
        self.frame_callback = frame_callback
        self.time_callback = time_callback  
        self.end_callback = end_callback
    
    def get_video_info(self) -> dict:
        """
        Get video information
        
        Returns:
            Dictionary with video properties
        """
        return {
            "is_loaded": self.is_loaded,
            "video_path": self.video_path,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration_seconds": self.duration_seconds,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "current_time": self.current_time,
            "is_playing": self.is_playing
        }
    
    def release(self):
        """Release video resources"""
        # Stop playback first
        self.stop()
        
        # Release video capture
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Reset state
        self.is_loaded = False
        self.video_path = None
        self.current_frame = 0
        self.current_time = 0.0


def cv2_frame_to_tkinter(frame, target_size: Optional[Tuple[int, int]] = None):
    """
    Convert OpenCV frame to tkinter-compatible PhotoImage
    
    Args:
        frame: OpenCV frame (BGR format)
        target_size: Optional (width, height) tuple for resizing
        
    Returns:
        tkinter PhotoImage object or None if PIL not available
    """
    print(f"🔧 cv2_frame_to_tkinter called, PIL_AVAILABLE: {PIL_AVAILABLE}")
    
    if not PIL_AVAILABLE:
        print("Cannot convert frame: PIL not available")
        return None
    
    try:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize if target size specified
        if target_size:
            pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to tkinter PhotoImage
        tk_image = ImageTk.PhotoImage(pil_image)
        
        print(f"✅ Frame converted successfully, size: {tk_image.width()}x{tk_image.height()}")
        return tk_image
        
    except Exception as e:
        print(f"❌ Error in cv2_frame_to_tkinter: {e}")
        return None
