"""
Thumbnail Cache Manager
Manages video frame extraction and caching for cuts display
"""

import cv2
import threading
from typing import Dict, Optional, List, Tuple
from PIL import Image
import time


class ThumbnailCache:
    """
    Manages thumbnail extraction and caching for video cuts
    Generates thumbnails once and shares them between components
    """
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cache: Dict[float, Image.Image] = {}  # time_seconds -> PIL.Image
        self.is_loading = False
        self.load_progress = 0.0
        self.total_thumbnails = 0
        self._lock = threading.Lock()
        
    def preload_cut_thumbnails(self, cuts_data: List[dict]) -> bool:
        """
        Pre-generate all frames for the given cuts (original size)
        
        Args:
            cuts_data: List of cut dictionaries with start_time
            
        Returns:
            True if successful, False otherwise
        """
        if not cuts_data:
            return True
            
        self.total_thumbnails = len(cuts_data)
        self.is_loading = True
        self.load_progress = 0.0
        
        try:
            # Open video capture
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"❌ Error: Cannot open video file: {self.video_path}")
                return False
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                print(f"❌ Error: Invalid FPS: {fps}")
                cap.release()
                return False
            
            print(f"🎬 Starting frame generation for {len(cuts_data)} cuts...")
            
            for i, cut in enumerate(cuts_data):
                try:
                    # Parse start time
                    start_time = cut.get("start_time", cut.get("start", "00:00:00"))
                    time_seconds = self._parse_time_to_seconds(start_time)
                    
                    # Skip if already cached
                    if time_seconds in self.cache:
                        continue
                    
                    # Extract frame at specific time (original size)
                    frame_image = self._extract_frame_at_time(cap, time_seconds, fps)
                    
                    if frame_image:
                        with self._lock:
                            self.cache[time_seconds] = frame_image
                        print(f"✅ Generated frame for {start_time} (Cut {i+1}/{len(cuts_data)})")
                    else:
                        print(f"⚠️ Failed to generate frame for {start_time}")
                        
                except Exception as e:
                    print(f"❌ Error generating frame for cut {i+1}: {e}")
                    
                # Update progress
                self.load_progress = (i + 1) / len(cuts_data)
            
            cap.release()
            self.is_loading = False
            
            print(f"🎯 Frame generation complete: {len(self.cache)}/{len(cuts_data)} successful")
            return True
            
        except Exception as e:
            print(f"❌ Error in frame preloading: {e}")
            self.is_loading = False
            return False
    def get_thumbnail(self, start_time: str) -> Optional[Image.Image]:
        """
        Get frame for a specific start time (original size)
        Components should resize as needed for their display requirements
        
        Args:
            start_time: Time string in HH:MM:SS format
            
        Returns:
            PIL Image in original video resolution or None if not available
        """
        try:
            time_seconds = self._parse_time_to_seconds(start_time)
            with self._lock:
                return self.cache.get(time_seconds)
        except Exception as e:
            print(f"❌ Error getting thumbnail for {start_time}: {e}")
            return None
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "cached_thumbnails": len(self.cache),
            "is_loading": self.is_loading,
            "load_progress": self.load_progress,
            "total_thumbnails": self.total_thumbnails
        }
    
    def clear_cache(self):
        """Clear all cached thumbnails"""
        with self._lock:
            self.cache.clear()
        print("🗑️ Thumbnail cache cleared")
    
    def _extract_frame_at_time(self, cap: cv2.VideoCapture, time_seconds: float, fps: float) -> Optional[Image.Image]:
        """
        Extract frame at specific time (original size)
        
        Args:
            cap: OpenCV VideoCapture object
            time_seconds: Time in seconds
            fps: Video FPS
            
        Returns:
            PIL Image or None
        """
        try:
            # Calculate frame number
            frame_number = int(time_seconds * fps)
            
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read frame
            ret, frame = cap.read()
            if not ret or frame is None:
                return None
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image (original size)
            pil_image = Image.fromarray(frame_rgb)
            
            return pil_image
            
        except Exception as e:
            print(f"❌ Error extracting frame at {time_seconds}s: {e}")
            return None
    
    def _parse_time_to_seconds(self, time_str: str) -> float:
        """
        Parse time string to seconds
        
        Args:
            time_str: Time in HH:MM:SS format
            
        Returns:
            Time in seconds
        """
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:
                return float(parts[0])
        except Exception as e:
            print(f"❌ Error parsing time '{time_str}': {e}")
            return 0.0

    def regenerate_thumbnail(self, start_time: str) -> bool:
        """
        Regenerate a specific thumbnail after time change
        
        Args:
            start_time: New start time in HH:MM:SS format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            time_seconds = self._parse_time_to_seconds(start_time)
            
            # Open video capture
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                print(f"❌ Error: Cannot open video file for regeneration: {self.video_path}")
                return False
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                print(f"❌ Error: Invalid FPS for regeneration: {fps}")
                cap.release()
                return False
            
            # Extract new frame
            frame_image = self._extract_frame_at_time(cap, time_seconds, fps)
            cap.release()
            
            if frame_image:
                with self._lock:
                    self.cache[time_seconds] = frame_image
                print(f"🔄 Regenerated frame for {start_time}")
                return True
            else:
                print(f"⚠️ Failed to regenerate frame for {start_time}")
                return False
                
        except Exception as e:
            print(f"❌ Error regenerating frame for {start_time}: {e}")
            return False
    
    def remove_thumbnail(self, start_time: str):
        """
        Remove a thumbnail from cache (useful for cleanup after time changes)
        
        Args:
            start_time: Time in HH:MM:SS format to remove
        """
        try:
            time_seconds = self._parse_time_to_seconds(start_time)
            with self._lock:
                if time_seconds in self.cache:
                    del self.cache[time_seconds]
                    print(f"🗑️ Removed old frame for {start_time}")
        except Exception as e:
            print(f"❌ Error removing frame for {start_time}: {e}")


def create_thumbnail_cache(video_path: str, cuts_data: List[dict]) -> Optional[ThumbnailCache]:
    """
    Factory function to create and populate a thumbnail cache
    
    Args:
        video_path: Path to video file
        cuts_data: List of cut data dictionaries
        
    Returns:
        ThumbnailCache instance or None if failed
    """
    try:
        cache = ThumbnailCache(video_path)
        success = cache.preload_cut_thumbnails(cuts_data)
        
        if success:
            return cache
        else:
            print("❌ Failed to create thumbnail cache")
            return None
            
    except Exception as e:
        print(f"❌ Error creating thumbnail cache: {e}")
        return None
