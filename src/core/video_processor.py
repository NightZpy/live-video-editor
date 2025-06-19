"""
Video Processor
FFmpeg-based video cutting and processing system with progress tracking
"""

import os
import ffmpeg
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime


class VideoExportProgress:
    """Progress tracking for video export operations"""
    
    def __init__(self):
        self.current_file = ""
        self.current_index = 0
        self.total_files = 0
        self.progress_percent = 0.0
        self.status = "idle"  # idle, processing, completed, error, cancelled
        self.error_message = ""
        self.start_time: Optional[float] = None
        self.estimated_time_remaining = 0
        self.output_files: List[str] = []
        
    def reset(self):
        """Reset progress tracking"""
        self.current_file = ""
        self.current_index = 0
        self.total_files = 0
        self.progress_percent = 0.0
        self.status = "idle"
        self.error_message = ""
        self.start_time = None
        self.estimated_time_remaining = 0
        self.output_files: List[str] = []


class VideoProcessor:
    """
    FFmpeg-based video processor for cutting and exporting video segments
    """
    
    def __init__(self):
        self.progress = VideoExportProgress()
        self.cancel_requested = False
        self._progress_callback: Optional[Callable] = None
        self._completion_callback: Optional[Callable] = None
        
    def set_progress_callback(self, callback: Callable[[VideoExportProgress], None]):
        """Set callback function for progress updates"""
        self._progress_callback = callback
        
    def set_completion_callback(self, callback: Callable[[bool, str], None]):
        """Set callback function for completion (success, message)"""
        self._completion_callback = callback
        
    def cancel_export(self):
        """Request cancellation of current export operation"""
        self.cancel_requested = True
        self.progress.status = "cancelled"
        
    def export_single_cut(self, video_path: str, cut_data: Dict, output_dir: str, 
                         quality: str = "original") -> bool:
        """
        Export a single video cut
        
        Args:
            video_path: Path to source video file
            cut_data: Cut data with start, end, title, etc.
            output_dir: Directory to save the exported file
            quality: Export quality setting
            
        Returns:
            True if export successful, False otherwise
        """
        # Reset progress
        self.progress.reset()
        self.cancel_requested = False
        
        # Set up progress tracking
        self.progress.total_files = 1
        self.progress.current_index = 1
        self.progress.status = "processing"
        self.progress.start_time = time.time()
        
        # Generate output filename
        safe_title = self._sanitize_filename(cut_data.get("title", f"Cut_{cut_data.get('id', 1)}"))
        output_filename = f"{safe_title}.mp4"
        output_path = str(Path(output_dir) / output_filename)
        
        self.progress.current_file = output_filename
        self._notify_progress()
        
        try:
            # Execute the export
            success = self._execute_cut(video_path, cut_data, output_path, quality)
            
            if success and not self.cancel_requested:
                self.progress.output_files.append(output_path)
                self.progress.progress_percent = 100.0
                self.progress.status = "completed"
                self._notify_progress()
                self._notify_completion(True, f"Successfully exported: {output_filename}")
                return True
            else:
                if self.cancel_requested:
                    self.progress.status = "cancelled"
                    self._notify_completion(False, "Export cancelled by user")
                else:
                    self.progress.status = "error"
                    self._notify_completion(False, f"Failed to export: {output_filename}")
                return False
                
        except Exception as e:
            self.progress.status = "error"
            self.progress.error_message = str(e)
            self._notify_progress()
            self._notify_completion(False, f"Error during export: {str(e)}")
            return False
            
    def export_batch_cuts(self, video_path: str, cuts_data: List[Dict], output_dir: str,
                         quality: str = "original") -> bool:
        """
        Export multiple video cuts in batch
        
        Args:
            video_path: Path to source video file
            cuts_data: List of cut data dictionaries
            output_dir: Directory to save the exported files
            quality: Export quality setting
            
        Returns:
            True if all exports successful, False if any failed
        """
        # Reset progress
        self.progress.reset()
        self.cancel_requested = False
        
        # Set up progress tracking
        self.progress.total_files = len(cuts_data)
        self.progress.status = "processing"
        self.progress.start_time = time.time()
        
        all_successful = True
        failed_files = []
        
        for index, cut_data in enumerate(cuts_data, 1):
            if self.cancel_requested:
                self.progress.status = "cancelled"
                self._notify_completion(False, "Batch export cancelled by user")
                return False
                
            # Update progress
            self.progress.current_index = index
            safe_title = self._sanitize_filename(cut_data.get("title", f"Cut_{cut_data.get('id', index)}"))
            output_filename = f"{safe_title}.mp4"
            output_path = str(Path(output_dir) / output_filename)
            
            self.progress.current_file = output_filename
            self.progress.progress_percent = ((index - 1) / len(cuts_data)) * 100
            self._notify_progress()
            
            try:
                # Execute the export
                success = self._execute_cut(video_path, cut_data, output_path, quality)
                
                if success and not self.cancel_requested:
                    self.progress.output_files.append(output_path)
                else:
                    all_successful = False
                    failed_files.append(output_filename)
                    
            except Exception as e:
                print(f"Error exporting {output_filename}: {e}")
                all_successful = False
                failed_files.append(output_filename)
                
        # Final status update
        if self.cancel_requested:
            self.progress.status = "cancelled"
            self._notify_completion(False, "Batch export cancelled")
        elif all_successful:
            self.progress.progress_percent = 100.0
            self.progress.status = "completed"
            self._notify_progress()
            self._notify_completion(True, f"Successfully exported {len(cuts_data)} cuts")
        else:
            self.progress.status = "error"
            failed_count = len(failed_files)
            success_count = len(cuts_data) - failed_count
            message = f"Exported {success_count}/{len(cuts_data)} cuts. Failed: {failed_count}"
            self._notify_completion(False, message)
            
        return all_successful
        
    def _execute_cut(self, video_path: str, cut_data: Dict, output_path: str, quality: str) -> bool:
        """
        Execute a single video cut using FFmpeg
        
        Args:
            video_path: Source video file path
            cut_data: Cut information (start, end times)
            output_path: Output file path
            quality: Quality settings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Input video file not found: {video_path}")
            
            # Convert time format to seconds for FFmpeg
            start_seconds = self._time_to_seconds(cut_data["start"])
            end_seconds = self._time_to_seconds(cut_data["end"])
            duration_seconds = end_seconds - start_seconds
            
            if duration_seconds <= 0:
                raise ValueError(f"Invalid time range: {cut_data['start']} to {cut_data['end']}")
            
            print(f"🎬 FFmpeg: Cutting {start_seconds}s to {end_seconds}s (duration: {duration_seconds}s)")
            print(f"📁 Input: {video_path}")
            print(f"📁 Output: {output_path}")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command based on quality
            input_stream = ffmpeg.input(video_path)
            
            # Apply quality settings
            output_kwargs = self._get_quality_settings(quality)
            
            # Add timing parameters
            output_kwargs['ss'] = start_seconds
            output_kwargs['t'] = duration_seconds
            
            print(f"🔧 FFmpeg parameters: {output_kwargs}")
            
            # Output stream
            output_stream = ffmpeg.output(input_stream, output_path, **output_kwargs)
            
            # Run with overwrite and capture output for error handling
            print("🚀 Starting FFmpeg process...")
            try:
                ffmpeg.run(output_stream, overwrite_output=True, quiet=False, capture_stdout=True, capture_stderr=True)
                print("✅ FFmpeg process completed successfully")
            except ffmpeg.Error as e:
                print(f"❌ FFmpeg error: {e}")
                if e.stderr:
                    print(f"FFmpeg stderr: {e.stderr.decode()}")
                return False
            
            # Verify output file was created and has reasonable size
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"📊 Output file size: {file_size} bytes")
                if file_size > 1000:  # At least 1KB
                    return True
                else:
                    print(f"❌ Output file too small: {file_size} bytes")
                    return False
            else:
                print("❌ Output file was not created")
                return False
                
        except Exception as e:
            print(f"❌ Error in _execute_cut: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def _get_quality_settings(self, quality: str) -> Dict[str, Any]:
        """
        Get FFmpeg output parameters based on quality setting
        
        Args:
            quality: Quality preset name
            
        Returns:
            Dictionary of FFmpeg parameters
        """
        quality_presets = {
            "original": {
                "c:v": "copy",  # Copy video stream without re-encoding
                "c:a": "copy"   # Copy audio stream without re-encoding
            },
            "high": {
                "c:v": "libx264",
                "crf": 18,
                "preset": "medium",
                "c:a": "aac",
                "b:a": "192k"
            },
            "medium": {
                "c:v": "libx264", 
                "crf": 23,
                "preset": "medium",
                "c:a": "aac",
                "b:a": "128k"
            },
            "low": {
                "c:v": "libx264",
                "crf": 28,
                "preset": "fast",
                "c:a": "aac",
                "b:a": "96k"
            }
        }
        
        return quality_presets.get(quality, quality_presets["original"])
        
    def _time_to_seconds(self, time_str: str) -> float:
        """
        Convert HH:MM:SS format to seconds
        
        Args:
            time_str: Time in HH:MM:SS format
            
        Returns:
            Time in seconds as float
        """
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                raise ValueError(f"Invalid time format: {time_str}")
                
            hours = int(parts[0])
            minutes = int(parts[1]) 
            seconds = int(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Cannot parse time '{time_str}': {e}")
            
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to be safe for file system
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
            
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(". ")
        
        # Ensure it's not empty
        if not filename:
            filename = "Untitled"
            
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
            
        return filename
        
    def _notify_progress(self):
        """Notify progress callback if set"""
        if self._progress_callback:
            self._progress_callback(self.progress)
            
    def _notify_completion(self, success: bool, message: str):
        """Notify completion callback if set"""
        if self._completion_callback:
            self._completion_callback(success, message)


# Threaded wrapper for non-blocking exports
class ThreadedVideoProcessor:
    """
    Wrapper for VideoProcessor that runs exports in background threads
    """
    
    def __init__(self):
        self.processor = VideoProcessor()
        self.current_thread = None
        
    def set_progress_callback(self, callback: Callable[[VideoExportProgress], None]):
        """Set callback function for progress updates"""
        self.processor.set_progress_callback(callback)
        
    def set_completion_callback(self, callback: Callable[[bool, str], None]):
        """Set callback function for completion"""
        self.processor.set_completion_callback(callback)
        
    def export_single_cut_async(self, video_path: str, cut_data: Dict, output_dir: str,
                               quality: str = "original"):
        """Export single cut in background thread"""
        if self.current_thread and self.current_thread.is_alive():
            return False  # Another export is running
            
        self.current_thread = threading.Thread(
            target=self.processor.export_single_cut,
            args=(video_path, cut_data, output_dir, quality)
        )
        self.current_thread.daemon = True
        self.current_thread.start()
        return True
        
    def export_batch_cuts_async(self, video_path: str, cuts_data: List[Dict], output_dir: str,
                               quality: str = "original"):
        """Export batch cuts in background thread"""
        if self.current_thread and self.current_thread.is_alive():
            return False  # Another export is running
            
        self.current_thread = threading.Thread(
            target=self.processor.export_batch_cuts,
            args=(video_path, cuts_data, output_dir, quality)
        )
        self.current_thread.daemon = True
        self.current_thread.start()
        return True
        
    def cancel_export(self):
        """Cancel current export operation"""
        self.processor.cancel_export()
        
    def is_exporting(self) -> bool:
        """Check if an export is currently running"""
        return bool(self.current_thread and self.current_thread.is_alive())
        
    def get_progress(self) -> VideoExportProgress:
        """Get current progress information"""
        return self.processor.progress
