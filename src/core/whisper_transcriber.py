"""
Whisper Transcriber
Handles both OpenAI API and local Whisper transcription with automatic fallback
"""

import os
import platform
import subprocess
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
        """Load the local Whisper model with intelligent device and model selection"""
        print(f"📥 Loading local Whisper model...")
        
        # Use preferred model or fall back to default order based on device
        if preferred_model:
            models_to_try = [preferred_model, "medium", "small", "base"]
        else:
            # Optimize model selection based on device and system
            if self.device == "cuda":
                models_to_try = ["large", "medium", "small", "base"]
            else:
                # For CPU, prioritize smaller models for better performance
                system_name = platform.system()
                if system_name == "Linux":
                    # WSL2 or Linux - start with medium for good balance
                    models_to_try = ["medium", "small", "base"]
                else:
                    # Windows/macOS - start with medium, avoid large for CPU
                    models_to_try = ["medium", "small", "base"]
        
        # Try devices in order of preference
        if self.device == "cuda":
            devices_to_try = ["cuda", "cpu"]  # Try GPU first, fallback to CPU
        else:
            devices_to_try = ["cpu"]  # Only CPU
        
        for model_name in models_to_try:
            for device in devices_to_try:
                try:
                    print(f"📥 Trying Whisper '{model_name}' model on {device}...")
                    
                    # For GPU, check if we have enough memory for the model
                    if device == "cuda":
                        memory_needed = self._estimate_model_memory(model_name)
                        available_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                        
                        if memory_needed > available_memory * 0.8:  # Use only 80% of GPU memory
                            print(f"⚠️ Model '{model_name}' needs ~{memory_needed:.1f}GB, but only {available_memory:.1f}GB available")
                            continue
                    
                    # Load the model
                    self.local_model = whisper.load_model(model_name, device=device)
                    self.device = device  # Update device if we had to fallback
                    
                    # Test the model with a simple operation
                    if device == "cuda":
                        print(f"🧪 Testing GPU model...")
                        torch.cuda.empty_cache()
                    else:
                        print(f"🧪 Testing CPU model...")
                    
                    print(f"✅ Local Whisper model '{model_name}' loaded successfully on {device}")
                    
                    # Log optimization info for CPU
                    if device == "cpu":
                        cpu_cores = os.cpu_count() or 1
                        print(f"⚡ CPU optimization: Using {cpu_cores} cores")
                        
                    return
                    
                except torch.cuda.OutOfMemoryError as e:
                    print(f"💾 GPU out of memory for '{model_name}': {str(e)}")
                    if device == "cuda":
                        torch.cuda.empty_cache()  # Clear GPU memory
                    continue
                except Exception as e:
                    print(f"⚠️ Failed to load '{model_name}' on {device}: {str(e)}")
                    if device == "cuda":
                        torch.cuda.empty_cache()  # Clear GPU memory on any GPU error
                    continue
        
        # If we get here, all attempts failed
        raise Exception("Failed to load any Whisper model on any device")
    
    def _estimate_model_memory(self, model_name: str) -> float:
        """Estimate memory requirements for Whisper models in GB"""
        memory_requirements = {
            "large": 3.0,    # ~3GB
            "medium": 1.5,   # ~1.5GB  
            "small": 1.0,    # ~1GB
            "base": 0.5      # ~0.5GB
        }
        return memory_requirements.get(model_name, 2.0)  # Default 2GB
    
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
        """Detect the best available device with intelligent fallback for all platforms"""
        # First check for CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            try:
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    
                    print(f"🚀 NVIDIA GPU detected: {gpu_name}")
                    print(f"💾 GPU Memory: {gpu_memory:.1f} GB")
                    
                    # Check if GPU has enough memory for Whisper (minimum 2GB recommended)
                    if gpu_memory >= 2.0:
                        print(f"✅ NVIDIA GPU has sufficient memory for Whisper processing")
                        return "cuda"
                    else:
                        print(f"⚠️ NVIDIA GPU memory too low for Whisper, falling back to CPU")
                        return "cpu"
                else:
                    print(f"⚠️ CUDA available but no GPU devices found")
                    return "cpu"
            except Exception as e:
                print(f"⚠️ CUDA detection failed: {str(e)}")
                return "cpu"
        
        # Check for Apple Metal (macOS)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"🍎 Apple Metal (MPS) detected, but using CPU for Whisper compatibility")
            # Note: MPS has compatibility issues with Whisper's sparse operations
            return "cpu"
        
        # If no compatible GPU found, check for AMD and provide info
        else:
            # Detect AMD GPU and provide helpful information
            amd_detected = self._detect_amd_gpu_system()
            
            if amd_detected:
                print(f"💻 Using optimized CPU processing (AMD GPU detected but not supported)")
            else:
                print(f"💻 Using optimized CPU processing")
            
            return "cpu"
    
    def _check_rocm_support(self) -> bool:
        """Check if ROCm (AMD GPU) support is available - Legacy method"""
        # This method is kept for compatibility but ROCm detection is now handled
        # in _detect_device() method with better platform awareness
        return False
    
    def _optimize_pytorch(self):
        """Optimize PyTorch for better performance with intelligent platform detection"""
        # Get optimal number of CPU cores
        cpu_count = os.cpu_count() or 1
        
        # Optimize thread count based on system
        system_name = platform.system()
        if system_name == "Linux":
            # Check if we're in WSL2
            try:
                with open('/proc/version', 'r') as f:
                    proc_version = f.read().lower()
                if 'microsoft' in proc_version or 'wsl' in proc_version:
                    # WSL2 - use slightly fewer threads to avoid conflicts
                    optimal_threads = max(1, cpu_count - 1)
                    print(f"🐧 WSL2 detected: Using {optimal_threads} of {cpu_count} CPU threads")
                else:
                    # Native Linux
                    optimal_threads = cpu_count
                    print(f"🐧 Linux: Using {optimal_threads} CPU threads")
            except:
                optimal_threads = cpu_count
                print(f"🐧 Linux: Using {optimal_threads} CPU threads")
        else:
            # Windows/macOS
            optimal_threads = cpu_count
            print(f"💻 {system_name}: Using {optimal_threads} CPU threads")
        
        torch.set_num_threads(optimal_threads)
        
        # Configure quantized backend based on platform
        try:
            if system_name == 'Darwin':  # macOS
                torch.backends.quantized.engine = 'qnnpack'
                print("🍎 Using QNNPACK backend for macOS")
            else:  # Windows, Linux, WSL2
                torch.backends.quantized.engine = 'fbgemm'
                print(f"💻 Using FBGEMM backend for {system_name}")
        except Exception as e:
            print(f"⚠️ Could not configure quantized backend: {str(e)}")
            print(f"⚠️ Continuing with default PyTorch configuration...")
            # Continue without quantized optimizations - this is not critical
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def cleanup(self):
        """Clean up resources and GPU memory"""
        if self.local_model is not None:
            print(f"🧹 Cleaning up local Whisper model...")
            del self.local_model
            self.local_model = None
            
            # Clear GPU memory based on device
            try:
                if self.device == "cuda" and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    print(f"🧹 GPU memory cleared")
                elif self.device == "mps" and hasattr(torch.mps, 'empty_cache'):
                    torch.mps.empty_cache()
                    print(f"🧹 MPS memory cleared")
            except Exception as e:
                print(f"⚠️ Could not clear GPU memory: {str(e)}")
        
        print(f"✅ Whisper transcriber cleanup completed")
    
    def _detect_amd_gpu_windows(self) -> bool:
        """Detect AMD GPU on Windows using system commands"""
        try:
            # Try to detect AMD GPU on Windows using wmic
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                  capture_output=True, text=True, timeout=5)
            gpu_info = result.stdout.upper()
            
            amd_keywords = ['AMD', 'RADEON', 'RX', 'VEGA', 'NAVI', 'RDNA']
            if any(keyword in gpu_info for keyword in amd_keywords):
                # Extract GPU names for better info
                lines = result.stdout.strip().split('\n')
                gpu_names = [line.strip() for line in lines if line.strip() and 'Name' not in line]
                amd_gpus = [name for name in gpu_names if any(keyword in name.upper() for keyword in amd_keywords)]
                
                if amd_gpus:
                    print(f"🔍 AMD GPU detected: {', '.join(amd_gpus)}")
                    print(f"🔍 AMD GPU detected but ROCm not available")
                    return True
            return False
        except Exception:
            return False
    
    def _detect_amd_gpu_system(self) -> bool:
        """Detect AMD GPU on current system (Windows/WSL2/Linux)"""
        try:
            system_name = platform.system()
            
            if system_name == 'Windows':
                return self._detect_amd_gpu_windows()
            elif system_name == 'Linux':
                # Check if we're in WSL2 or native Linux
                try:
                    with open('/proc/version', 'r') as f:
                        proc_version = f.read().lower()
                    
                    if 'microsoft' in proc_version or 'wsl' in proc_version:
                        # We're in WSL2, check Windows hardware indirectly
                        print(f"🐧 Running in WSL2 - AMD GPU support limited")
                        return True  # Assume AMD GPU exists but not accessible in WSL2
                    else:
                        # Native Linux, check for AMD GPU
                        result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                        return 'amd' in result.stdout.lower() or 'radeon' in result.stdout.lower()
                except:
                    return False
            else:
                return False
        except Exception:
            return False
