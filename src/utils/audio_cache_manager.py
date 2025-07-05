"""
Audio Cache Manager
Intelligent audio loading with multiple fallback strategies
"""

import os
import tempfile
import threading
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import pygame
import ffmpeg
import io

class AudioCacheManager:
    """
    Manages audio loading with intelligent caching and fallback strategies
    
    Priority:
    1. Existing temp audio (from LLM transcription) - 0ms
    2. Persistent cache - 50-100ms  
    3. Direct FFmpeg stream to memory - 300-500ms
    4. Full extraction (fallback) - 2-5s
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=16000, size=-16, channels=1, buffer=1024)
        pygame.mixer.init()
        
        # Cache management
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".live_video_editor" / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Active audio tracking
        self.active_videos: Dict[str, Dict[str, Any]] = {}
        self.temp_audio_registry: Dict[str, str] = {}  # video_path -> temp_audio_path
        
        # Loading state
        self.loading_threads: Dict[str, threading.Thread] = {}
        
        print(f"🎵 AudioCacheManager initialized, cache dir: {self.cache_dir}")
    
    def register_temp_audio(self, video_path: str, temp_audio_path: str):
        """
        Register temporary audio file from LLM processor
        This prevents cleanup and allows reuse
        
        Args:
            video_path: Original video file path
            temp_audio_path: Path to temporary audio file
        """
        video_key = self._get_video_key(video_path)
        self.temp_audio_registry[video_key] = temp_audio_path
        print(f"📝 Registered temp audio: {video_path} -> {temp_audio_path}")
    
    def load_audio_for_video(self, video_path: str) -> threading.Thread:
        """
        Load audio for video using best available strategy
        
        Args:
            video_path: Path to video file
            
        Returns:
            Thread handling the loading process
        """
        video_key = self._get_video_key(video_path)
        
        def load_worker():
            try:
                audio_data = None
                load_method = "unknown"
                start_time = time.time()
                
                # Strategy 1: Use existing temp audio (fastest)
                if video_key in self.temp_audio_registry:
                    temp_path = self.temp_audio_registry[video_key]
                    if os.path.exists(temp_path):
                        audio_data = self._load_from_file(temp_path)
                        load_method = "existing_temp"
                        print(f"⚡ Using existing temp audio: {temp_path}")
                
                # Strategy 2: Load from persistent cache
                if audio_data is None:
                    cache_path = self._get_cache_path(video_path)
                    if cache_path.exists():
                        audio_data = self._load_from_file(str(cache_path))
                        load_method = "persistent_cache"
                        print(f"📂 Using cached audio: {cache_path}")
                
                # Strategy 3: Direct FFmpeg stream (faster than file extraction)
                if audio_data is None:
                    audio_data = self._stream_audio_direct(video_path)
                    load_method = "direct_stream"
                    print(f"🌊 Using direct audio stream")
                    
                    # Save to cache for future use
                    if audio_data:
                        self._save_to_cache(video_path, audio_data)
                
                # Strategy 4: Fallback to file extraction (slowest)
                if audio_data is None:
                    audio_data = self._extract_audio_fallback(video_path)
                    load_method = "file_extraction"
                    print(f"🐌 Using file extraction fallback")
                
                if audio_data:
                    # Create pygame Sound object
                    audio_buffer = io.BytesIO(audio_data)
                    pygame_sound = pygame.mixer.Sound(audio_buffer)
                    
                    # Store in active videos
                    load_time = time.time() - start_time
                    self.active_videos[video_key] = {
                        'pygame_sound': pygame_sound,
                        'raw_data': audio_data,
                        'load_method': load_method,
                        'load_time': load_time,
                        'sample_rate': 16000
                    }
                    
                    print(f"✅ Audio loaded in {load_time:.3f}s using {load_method}")
                else:
                    print(f"❌ Failed to load audio for {video_path}")
                    
            except Exception as e:
                print(f"❌ Error loading audio: {e}")
                import traceback
                traceback.print_exc()
        
        # Start loading thread
        thread = threading.Thread(target=load_worker, daemon=True)
        thread.start()
        self.loading_threads[video_key] = thread
        
        return thread
    
    def get_audio_for_video(self, video_path: str) -> Optional[pygame.mixer.Sound]:
        """
        Get loaded audio for video (non-blocking)
        
        Args:
            video_path: Path to video file
            
        Returns:
            pygame.mixer.Sound if loaded, None otherwise
        """
        video_key = self._get_video_key(video_path)
        video_data = self.active_videos.get(video_key)
        
        if video_data:
            return video_data['pygame_sound']
        return None
    
    def is_audio_ready(self, video_path: str) -> bool:
        """Check if audio is ready for playback"""
        video_key = self._get_video_key(video_path)
        return video_key in self.active_videos
    
    def is_loading(self, video_path: str) -> bool:
        """Check if audio is currently loading"""
        video_key = self._get_video_key(video_path)
        thread = self.loading_threads.get(video_key)
        return thread is not None and thread.is_alive()
    
    def create_audio_segment(self, video_path: str, start_seconds: float, duration_seconds: float) -> Optional[pygame.mixer.Sound]:
        """
        Create audio segment for specific time range
        
        Args:
            video_path: Path to video file
            start_seconds: Start time in seconds
            duration_seconds: Duration in seconds
            
        Returns:
            pygame.mixer.Sound for the segment
        """
        video_key = self._get_video_key(video_path)
        video_data = self.active_videos.get(video_key)
        
        if not video_data:
            return None
        
        try:
            raw_data = video_data['raw_data']
            sample_rate = video_data['sample_rate']
            
            # Calculate byte positions (assuming 16-bit mono WAV)
            wav_header_size = 44
            bytes_per_second = sample_rate * 2  # 16-bit = 2 bytes per sample
            
            start_byte = wav_header_size + int(start_seconds * bytes_per_second)
            end_byte = start_byte + int(duration_seconds * bytes_per_second)
            
            # Extract segment data
            segment_data = raw_data[start_byte:min(end_byte, len(raw_data))]
            
            # Create WAV header for segment
            segment_wav = self._create_wav_segment(segment_data, sample_rate)
            
            # Create pygame Sound
            segment_buffer = io.BytesIO(segment_wav)
            return pygame.mixer.Sound(segment_buffer)
            
        except Exception as e:
            print(f"❌ Error creating audio segment: {e}")
            return None
    
    def cleanup_video_audio(self, video_path: str):
        """Clean up audio data for video"""
        video_key = self._get_video_key(video_path)
        
        # Remove from active videos
        if video_key in self.active_videos:
            del self.active_videos[video_key]
        
        # Cancel loading thread if running
        if video_key in self.loading_threads:
            # Note: Can't force cancel thread, but it will finish and clean itself
            del self.loading_threads[video_key]
        
        # Keep temp audio registered for potential reuse
        # Don't clean up temp_audio_registry unless explicitly requested
        
        print(f"🧹 Cleaned up audio for {video_path}")
    
    def _get_video_key(self, video_path: str) -> str:
        """Generate unique key for video file"""
        # Use file path + size + mtime for unique identification
        try:
            stat = os.stat(video_path)
            key_string = f"{video_path}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(key_string.encode()).hexdigest()
        except:
            # Fallback to path hash
            return hashlib.md5(video_path.encode()).hexdigest()
    
    def _get_cache_path(self, video_path: str) -> Path:
        """Get cache file path for video"""
        video_key = self._get_video_key(video_path)
        return self.cache_dir / f"{video_key}.wav"
    
    def _load_from_file(self, file_path: str) -> Optional[bytes]:
        """Load audio data from file"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error loading from file {file_path}: {e}")
            return None
    
    def _stream_audio_direct(self, video_path: str) -> Optional[bytes]:
        """Stream audio directly from video to memory"""
        try:
            process = (
                ffmpeg
                .input(video_path)
                .audio
                .output(
                    'pipe:', 
                    format='wav',
                    acodec='pcm_s16le',
                    ac=1,  # Mono
                    ar='16000',  # 16kHz
                    **{'threads': 'auto'}
                )
                .run_async(pipe_stdout=True, pipe_stderr=True, quiet=True)
            )
            
            audio_data, stderr = process.communicate()
            
            if process.returncode == 0:
                return audio_data
            else:
                print(f"❌ FFmpeg streaming error: {stderr.decode()}")
                return None
                
        except Exception as e:
            print(f"❌ Error in direct streaming: {e}")
            return None
    
    def _extract_audio_fallback(self, video_path: str) -> Optional[bytes]:
        """Fallback: Extract audio to temp file then load"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            (
                ffmpeg
                .input(video_path)
                .output(
                    temp_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar='16000'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Load data
            audio_data = self._load_from_file(temp_path)
            
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return audio_data
            
        except Exception as e:
            print(f"❌ Error in fallback extraction: {e}")
            return None
    
    def _save_to_cache(self, video_path: str, audio_data: bytes):
        """Save audio data to persistent cache"""
        try:
            cache_path = self._get_cache_path(video_path)
            with open(cache_path, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Saved audio to cache: {cache_path}")
        except Exception as e:
            print(f"⚠️ Failed to save to cache: {e}")
    
    def _create_wav_segment(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Create WAV file with proper header for audio segment"""
        import struct
        
        # WAV header parameters
        channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        data_size = len(audio_data)
        file_size = 36 + data_size
        
        # Create WAV header
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', file_size, b'WAVE', b'fmt ', 16,
            1, channels, sample_rate, byte_rate, block_align, bits_per_sample,
            b'data', data_size
        )
        
        return header + audio_data
