"""
Video Utilities
Functions for handling video file operations and metadata extraction
"""

import cv2
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union


class VideoFile:
    """
    Video file handler that loads the file once and provides validation and metadata extraction
    """
    
    def __init__(self, file_path: str):
        self.file_path = str(Path(file_path))
        self.path_obj = Path(file_path)
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_loaded = False
        self._metadata = None
        
    def __enter__(self):
        """Context manager entry"""
        self.load()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.release()
        
    def load(self):
        """Load the video file with OpenCV"""
        if self._is_loaded:
            return
            
        try:
            self._cap = cv2.VideoCapture(self.file_path)
            self._is_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load video file: {e}")
    
    def release(self):
        """Release the video capture object"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self._is_loaded = False
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate if the file is a valid MP4 video file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not self.path_obj.exists():
            return False, "File does not exist"
        
        # Check file extension
        if self.path_obj.suffix.lower() != '.mp4':
            return False, "Only MP4 files are supported"
        
        # Ensure video is loaded
        if not self._is_loaded:
            self.load()
        
        # Check if OpenCV can open the file
        if self._cap is None or not self._cap.isOpened():
            return False, "Cannot open video file - file may be corrupted"
        
        # Try to read first frame to ensure it's a valid video
        try:
            ret, _ = self._cap.read()
            if not ret:
                return False, "Video file appears to be empty or corrupted"
            
            # Reset to beginning for metadata extraction
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return True, ""
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"
    
    def get_metadata(self) -> Optional[Dict]:
        """
        Extract metadata from the loaded video file
        
        Returns:
            Dictionary with video metadata or None if extraction fails
        """
        if not self._is_loaded or self._cap is None or not self._cap.isOpened():
            return None
        
        try:
            # Get video properties
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Calculate duration
            duration_seconds = frame_count / fps if fps > 0 else 0
            duration_formatted = format_duration(duration_seconds)
            
            # Get file size
            file_size_bytes = self.path_obj.stat().st_size
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            self._metadata = {
                "file_path": self.file_path,
                "filename": self.path_obj.name,
                "duration": duration_formatted,
                "duration_seconds": int(duration_seconds),
                "resolution": f"{width}x{height}",
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "file_size": f"{file_size_mb:.1f} MB",
                "file_size_bytes": file_size_bytes
            }
            
            return self._metadata
            
        except Exception as e:
            print(f"Error extracting video metadata: {e}")
            return None


def validate_and_extract_metadata(file_path: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validate and extract metadata in a single operation (most efficient)
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Tuple of (is_valid, error_message, metadata)
    """
    if not file_path:
        return False, "No file selected", None
    
    try:
        with VideoFile(file_path) as video:
            is_valid, error_msg = video.validate()
            if not is_valid:
                return False, error_msg, None
            
            metadata = video.get_metadata()
            return True, "", metadata
            
    except Exception as e:
        return False, f"Error processing video file: {str(e)}", None


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to HH:MM:SS format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted file size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"
