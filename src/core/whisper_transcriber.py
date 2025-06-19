"""
Whisper Transcriber
Handles both OpenAI API and local Whisper transcription with automatic fallback
"""

import os
import whisper
import torch
from typing import Dict, Optional, Callable, Any


class WhisperTranscriber:
    """
    Manages transcription using both OpenAI Whisper API and local Whisper model
    Automatically chooses the best method based on file size and availability
    """
    
    def __init__(self, openai_client):
        """
        Initialize the transcriber
        
        Args:
            openai_client: OpenAI client for API transcription
        """
        self.openai_client = openai_client
        self.local_model: Optional[Any] = None  # Whisper model type
        self.max_api_size = 24_000_000  # 24MB safe limit for API
        
        # Detect available device for local processing
        self.device = self._detect_device()
        
        # Optimize PyTorch for better CPU performance
        self._optimize_pytorch()
        
        print(f"🔧 Whisper transcriber initialized with device: {self.device}")
    
    def transcribe(self, audio_path: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Transcribe audio using the best available method
        
        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transcription result with timestamps
        """
        file_size = self._get_file_size(audio_path)
        print(f"🎙️ Audio file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        # Decide transcription method
        if file_size <= self.max_api_size:
            print(f"📡 Using OpenAI API for transcription (file size within limit)")
            try:
                return self._transcribe_api(audio_path)
            except Exception as e:
                print(f"⚠️ API transcription failed: {str(e)}")
                print(f"🔄 Falling back to local Whisper...")
                return self._transcribe_local(audio_path, progress_callback)
        else:
            print(f"🏠 Using local Whisper for transcription (file too large for API)")
            return self._transcribe_local(audio_path, progress_callback)
    
    def transcribe_with_video_info(self, audio_path: str, video_info: Dict, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Transcribe audio using video info for optimal model selection
        
        Args:
            audio_path: Path to audio file
            video_info: Video metadata containing duration_seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transcription result with timestamps
        """
        file_size = self._get_file_size(audio_path)
        duration = video_info.get('duration_seconds', 0.0)
        
        print(f"🎙️ Audio file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        print(f"⏱️ Video duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # Decide transcription method
        if file_size <= self.max_api_size:
            print(f"📡 Using OpenAI API for transcription (file size within limit)")
            try:
                return self._transcribe_api(audio_path)
            except Exception as e:
                print(f"⚠️ API transcription failed: {str(e)}")
                print(f"🔄 Falling back to local Whisper...")
                return self._transcribe_local_with_duration(audio_path, duration, progress_callback)
        else:
            print(f"🏠 Using local Whisper for transcription (file too large for API)")
            return self._transcribe_local_with_duration(audio_path, duration, progress_callback)
    
    def _transcribe_api(self, audio_path: str) -> Dict:
        """
        Transcribe using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription result
        """
        print(f"📡 Starting API transcription...")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
                
            result = transcript.model_dump()
            print(f"✅ API transcription successful")
            print(f"📝 Text length: {len(result.get('text', ''))}")
            print(f"📝 Segments: {len(result.get('segments', []))}")
            
            return result
            
        except Exception as e:
            print(f"❌ API transcription error: {str(e)}")
            raise
    
    def _transcribe_local(self, audio_path: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Transcribe using local Whisper model
        
        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transcription result formatted like API response
        """
        print(f"🏠 Starting local transcription...")
        
        try:
            # Load model if not already loaded
            if self.local_model is None:
                if progress_callback:
                    progress_callback("generating_transcription", 35.0, "Loading Whisper model...")
                self._load_local_model()
            
            if progress_callback:
                progress_callback("generating_transcription", 45.0, "Transcribing with local Whisper...")
            
            # Transcribe with local model
            print(f"🎙️ Processing audio with local Whisper...")
            result = self.local_model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )
            
            if progress_callback:
                progress_callback("generating_transcription", 65.0, "Formatting transcription results...")
            
            # Format result to match API response
            formatted_result = self._format_local_result(result)
            
            print(f"✅ Local transcription successful")
            print(f"📝 Text length: {len(formatted_result.get('text', ''))}")
            print(f"📝 Segments: {len(formatted_result.get('segments', []))}")
            
            return formatted_result
            
        except Exception as e:
            print(f"❌ Local transcription error: {str(e)}")
            raise Exception(f"Local Whisper transcription failed: {str(e)}")
    
    def _transcribe_local_with_duration(self, audio_path: str, duration: float, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Transcribe using local Whisper model with adaptive model selection
        
        Args:
            audio_path: Path to audio file
            duration: Video duration in seconds
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transcription result formatted like API response
        """
        print(f"🏠 Starting local transcription with adaptive model selection...")
        
        try:
            # Choose optimal model based on duration
            optimal_model = self._choose_optimal_model(duration)
            
            # Load model if not already loaded or if we need a different model
            if self.local_model is None:
                if progress_callback:
                    progress_callback("generating_transcription", 35.0, f"Loading optimal Whisper model ({optimal_model})...")
                self._load_local_model(optimal_model)
            
            if progress_callback:
                progress_callback("generating_transcription", 45.0, "Transcribing with local Whisper...")
            
            # Decide whether to use word timestamps based on duration
            use_word_timestamps = self._should_use_word_timestamps(duration)
            
            # Transcribe with local model
            print(f"🎙️ Processing audio with local Whisper (word_timestamps={use_word_timestamps})...")
            result = self.local_model.transcribe(
                audio_path,
                word_timestamps=use_word_timestamps,
                verbose=False
            )
            
            if progress_callback:
                progress_callback("generating_transcription", 65.0, "Formatting transcription results...")
            
            # Format result to match API response
            formatted_result = self._format_local_result(result)
            
            print(f"✅ Local transcription successful")
            print(f"📝 Text length: {len(formatted_result.get('text', ''))}")
            print(f"📝 Segments: {len(formatted_result.get('segments', []))}")
            
            return formatted_result
            
        except Exception as e:
            print(f"❌ Local transcription error: {str(e)}")
            raise Exception(f"Local Whisper transcription failed: {str(e)}")
    
    def _choose_optimal_model(self, duration: float) -> str:
        """
        Choose optimal Whisper model based on video duration
        
        Args:
            duration: Video duration in seconds
            
        Returns:
            Optimal model name
        """
        if duration < 300:  # < 5 minutes
            model = "small"
            reason = "short video"
        elif duration < 1200:  # < 20 minutes  
            model = "medium"
            reason = "medium-length video"
        else:
            model = "large"
            reason = "long video"
        
        print(f"🎯 Selected '{model}' model for {reason} ({duration/60:.1f} min)")
        return model

    def _should_use_word_timestamps(self, duration: float) -> bool:
        """
        Decide whether to use word-level timestamps based on duration
        Word timestamps are more accurate but slower - only use for shorter videos
        
        Args:
            duration: Video duration in seconds
            
        Returns:
            True if word timestamps should be used
        """
        use_word_timestamps = duration < 600  # Only for videos < 10 minutes
        
        if use_word_timestamps:
            print(f"📍 Using word-level timestamps for precise cuts (video < 10 min)")
        else:
            print(f"📍 Using segment-level timestamps for faster processing (video >= 10 min)")
            
        return use_word_timestamps
    
    def _load_local_model(self, preferred_model: Optional[str] = None):
        """Load the local Whisper model"""
        print(f"📥 Loading local Whisper model...")
        
        # Use preferred model or fall back to default order
        if preferred_model:
            models_to_try = [preferred_model, "medium", "small", "base"]
        else:
            models_to_try = ["large", "medium", "small", "base"]
        devices_to_try = [self.device, "cpu"]  # Always fallback to CPU if device fails
        
        for model_name in models_to_try:
            for device in devices_to_try:
                try:
                    print(f"📥 Trying Whisper '{model_name}' model on {device}...")
                    self.local_model = whisper.load_model(model_name, device=device)
                    self.device = device  # Update device if we had to fallback
                    print(f"✅ Local Whisper model '{model_name}' loaded successfully on {device}")
                    return
                    
                except Exception as e:
                    print(f"⚠️ Failed to load '{model_name}' on {device}: {str(e)}")
                    continue
        
        # If we get here, all attempts failed
        raise Exception("Failed to load any Whisper model on any device")
    
    def _format_local_result(self, whisper_result: Dict) -> Dict:
        """
        Format local Whisper result to match OpenAI API format
        
        Args:
            whisper_result: Raw result from local Whisper
            
        Returns:
            Formatted result matching API structure
        """
        # Extract segments with timestamps
        segments = []
        for i, segment in enumerate(whisper_result.get('segments', [])):
            formatted_segment = {
                "id": i,
                "start": segment.get('start', 0.0),
                "end": segment.get('end', 0.0),
                "text": segment.get('text', '').strip(),
                "tokens": segment.get('tokens', []),
                "temperature": 0.0,
                "avg_logprob": segment.get('avg_logprob', 0.0),
                "compression_ratio": segment.get('compression_ratio', 0.0),
                "no_speech_prob": segment.get('no_speech_prob', 0.0)
            }
            segments.append(formatted_segment)
        
        # Build result in API format
        formatted_result = {
            "text": whisper_result.get('text', ''),
            "segments": segments,
            "language": whisper_result.get('language', 'en')
        }
        
        return formatted_result
    
    def _detect_device(self) -> str:
        """Detect the best available device for processing"""
        if torch.cuda.is_available():
            print(f"🚀 CUDA GPU detected")
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"🍎 Apple Metal (MPS) detected, but using CPU for Whisper compatibility")
            # Note: MPS has compatibility issues with Whisper's sparse operations
            return "cpu"
        else:
            print(f"💻 Using CPU for processing")
            return "cpu"
    
    def _optimize_pytorch(self):
        """Optimize PyTorch for better CPU performance"""
        # Use all available CPU cores
        cpu_count = os.cpu_count() or 1  # Fallback to 1 if None
        torch.set_num_threads(cpu_count)
        print(f"⚡ PyTorch optimized: using {cpu_count} CPU threads")
        
        # Additional optimizations for ARM (Apple Silicon)
        if hasattr(torch.backends, 'quantized'):
            torch.backends.quantized.engine = 'qnnpack'
            print(f"⚡ ARM optimization enabled (qnnpack)")
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def cleanup(self):
        """Clean up resources"""
        if self.local_model is not None:
            print(f"🧹 Cleaning up local Whisper model...")
            del self.local_model
            self.local_model = None
            
            # Clear GPU memory based on device
            if self.device == "cuda":
                torch.cuda.empty_cache()
            elif self.device == "mps":
                # Clear MPS cache if available
                if hasattr(torch.mps, 'empty_cache'):
                    torch.mps.empty_cache()
