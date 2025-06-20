"""
LLM Cuts Processor
Handles automatic video analysis using AI transcription and LLM processing
"""

import os
import json
import tempfile
import threading
from typing import Dict, List, Optional, Callable
import ffmpeg
import openai
from datetime import timedelta
from dotenv import load_dotenv
from .whisper_transcriber import WhisperTranscriber
from ..utils.data_cache import DataCacheManager

# Load environment variables from .env file
load_dotenv()

# Print version info for debugging
print(f"🔍 OpenAI library version: {openai.__version__}")


class LLMCutsProcessor:
    """
    Processes video files to automatically generate cuts using AI transcription and LLM analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM processor
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
        """
        # Use provided API key or fallback to environment variable
        if api_key:
            self.api_key = api_key
            print(f"🔑 Using provided API key")
        else:
            self.api_key = os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError(
                    "No OpenAI API key provided. Either:\n"
                    "1. Pass api_key parameter when creating LLMCutsProcessor\n"
                    "2. Set OPENAI_API_KEY environment variable\n"
                    "3. Create a .env file with OPENAI_API_KEY=your_key_here"
                )
            print(f"🔑 Using API key from environment variable")
        
        # Load model configuration from environment variables with defaults
        self.default_model = os.getenv('DEFAULT_MODEL', 'o4-mini')
        self.max_completion_tokens = int(os.getenv('MAX_COMPLETION_TOKENS', '8192'))
        self.reasoning_effort = os.getenv('REASONING_EFFORT', 'high')  # low, medium, high - using high for better precision
        
        # Model configuration with fallback strategy - optimized for precise cut analysis
        self.models_to_try = [
            {
                "name": "o4-mini", 
                "description": "o4-mini (best reasoning model for precise cuts)", 
                "reasoning_model": True,
                "effort": self.reasoning_effort
            },
            {
                "name": self.default_model if self.default_model != "o4-mini" else "gpt-4o", 
                "description": f"{self.default_model if self.default_model != 'o4-mini' else 'gpt-4o'} (fallback from config)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            },
            {
                "name": "gpt-4o", 
                "description": "GPT-4o (high quality, good context understanding)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            },
            {
                "name": "gpt-4o-mini", 
                "description": "GPT-4o Mini (fallback, faster, cost-effective)", 
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning_model": False
            }
        ]
        
        # Remove duplicates while preserving order
        seen_models = set()
        unique_models = []
        for model in self.models_to_try:
            if model["name"] not in seen_models:
                seen_models.add(model["name"])
                unique_models.append(model)
        self.models_to_try = unique_models
        
        print(f"🤖 Configured {len(self.models_to_try)} LLM models:")
        for i, model in enumerate(self.models_to_try):
            if model.get("reasoning_model", False):
                print(f"  {i+1}. {model['description']} (reasoning model)")
            else:
                print(f"  {i+1}. {model['description']} ({model['max_completion_tokens']} tokens)")
        
        # Initialize OpenAI client with error handling
        try:
            print(f"🔑 Initializing OpenAI client...")
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            print(f"✅ OpenAI client initialized successfully")
            
            # Test API key validity with a simple request
            try:
                print(f"🔑 Testing API key validity...")
                # Make a minimal test request to validate the API key
                models = self.openai_client.models.list()
                print(f"✅ API key is valid - found {len(models.data)} models")
            except Exception as test_e:
                print(f"⚠️ API key test failed: {str(test_e)}")
                # Don't fail initialization, just warn
                
        except Exception as e:
            print(f"❌ Error initializing OpenAI client: {str(e)}")
            print(f"❌ OpenAI version: {openai.__version__}")
            # Try alternative initialization without any optional parameters
            try:
                if api_key:
                    os.environ['OPENAI_API_KEY'] = str(api_key)
                self.openai_client = openai.OpenAI()
                print(f"✅ OpenAI client initialized with environment variable")
            except Exception as e2:
                print(f"❌ Alternative initialization also failed: {str(e2)}")
                raise Exception(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        self.is_cancelled = False
        
        # Processing state
        self.current_phase = ""
        self.current_progress = 0.0
        
        # Initialize Whisper transcriber
        self.transcriber = WhisperTranscriber(self.openai_client)
        print(f"🎙️ Whisper transcriber initialized")
        
        # Initialize data cache manager
        self.cache_manager = DataCacheManager()
        print(f"💾 Data cache manager initialized")
        
        # Quality and precision settings
        self.prefer_reasoning_models = os.getenv('PREFER_REASONING_MODELS', 'true').lower() == 'true'
        self.enable_advanced_boundary_detection = os.getenv('ENABLE_ADVANCED_BOUNDARY_DETECTION', 'true').lower() == 'true'
        
        print(f"⚙️ Quality settings:")
        print(f"   - Prefer reasoning models: {self.prefer_reasoning_models}")
        print(f"   - Advanced boundary detection: {self.enable_advanced_boundary_detection}")
        print(f"   - Reasoning effort: {self.reasoning_effort}")
        
        # Sort models to prioritize reasoning models if enabled
        if self.prefer_reasoning_models:
            self.models_to_try.sort(key=lambda x: (not x.get("reasoning_model", False), x["name"]))
            print(f"🧠 Prioritizing reasoning models for better cut precision")
        
    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates"""
        print(f"📞 LLM processor setting progress callback: {callback}")
        self.progress_callback = callback
        
    def cancel_processing(self):
        """Cancel the current processing operation"""
        print(f"⚠️ LLM processor cancelled")
        self.is_cancelled = True
        
        # Also cleanup transcriber resources
        if hasattr(self, 'transcriber'):
            self.transcriber.cleanup()
        
    def _update_progress(self, phase: str, progress: float, message: str = ""):
        """Update progress and call callback if set"""
        print(f"📈 LLM processor updating progress: phase={phase}, progress={progress:.1f}%, message='{message}', callback_set={self.progress_callback is not None}")
        
        if self.is_cancelled:
            print(f"⚠️ LLM processor ignoring progress update - cancelled")
            return
            
        self.current_phase = phase
        self.current_progress = progress
        
        if self.progress_callback:
            print(f"📞 LLM processor calling progress callback...")
            try:
                self.progress_callback(phase, progress, message)
                print(f"✅ LLM processor progress callback completed")
            except Exception as e:
                print(f"❌ LLM processor progress callback error: {str(e)}")
        else:
            print(f"⚠️ LLM processor no progress callback set")
    
    def process_video_async(self, video_path: str, video_info: Dict, completion_callback: Callable):
        """
        Process video asynchronously to generate cuts
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata 
            completion_callback: Function to call when processing is complete
        """
        print(f"🔄 Starting async video processing...")
        
        def worker():
            try:
                print(f"🔄 Worker thread started")
                result = self.process_video_sync_with_cache_check(video_path, video_info)
                if not self.is_cancelled:
                    print(f"✅ Processing successful, calling completion callback")
                    completion_callback(True, result, None)
                else:
                    print(f"⚠️ Processing was cancelled")
            except Exception as e:
                print(f"❌ Error in worker thread: {str(e)}")
                import traceback
                print(f"❌ Worker thread traceback: {traceback.format_exc()}")
                if not self.is_cancelled:
                    completion_callback(False, None, str(e))
        
        # Start processing in background thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        print(f"🔄 Background thread started")
        
    def process_video_with_cache_check(self, video_path: str, video_info: Dict, completion_callback: Callable):
        """
        Process video with intelligent cache checking
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata
            completion_callback: Function to call when processing is complete
        """
        print(f"🔄 Starting video processing with cache checking...")
        
        def worker():
            try:
                # Verificar si hay cuts completos en caché
                if self.cache_manager.has_cuts_cache(video_path):
                    print("🎯 Complete cuts cache found! Loading immediately...")
                    try:
                        cached_cuts = self.cache_manager.load_cuts(video_path)
                        if not self.is_cancelled:
                            completion_callback(True, cached_cuts, "Cuts loaded from cache")
                            return
                    except Exception as e:
                        print(f"⚠️ Failed to load cuts cache: {e}")
                        # Continuar con procesamiento normal
                
                # Verificar si hay transcripción en caché
                if self.cache_manager.has_transcription_cache(video_path):
                    print("📝 Transcription cache found! Skipping transcription...")
                    self._process_with_cached_transcription(video_path, video_info, completion_callback)
                    return
                else:
                    print("🔄 No cache found, processing from scratch...")
                    result = self.process_video(video_path, video_info)
                    if not self.is_cancelled:
                        completion_callback(True, result, "Processing completed successfully")
                        
            except Exception as e:
                print(f"❌ Error in cache-aware worker thread: {str(e)}")
                import traceback
                print(f"❌ Cache-aware worker thread traceback: {traceback.format_exc()}")
                if not self.is_cancelled:
                    completion_callback(False, None, str(e))
        
        # Start processing in background thread
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
    def _process_with_cached_transcription(self, video_path: str, video_info: Dict, completion_callback: Callable):
        """Process video using cached transcription"""
        try:
            self._update_progress("loading_cache", 10.0, "Cargando transcripción desde caché...")
            
            # Cargar transcripción desde caché
            transcription_result = self.cache_manager.load_transcription(video_path)
            if not transcription_result:
                raise Exception("Failed to load transcription from cache")
            
            cached_transcription, cached_video_info = transcription_result
            
            if self.is_cancelled:
                raise Exception("Processing cancelled")
            
            self._update_progress("analyzing_with_ai", 30.0, "Analizando contenido con GPT-4...")
            
            # Saltar directamente al análisis LLM
            cuts_array = self._analyze_with_llm(cached_transcription, cached_video_info)
            
            if self.is_cancelled:
                raise Exception("Processing cancelled")
            
            self._update_progress("analyzing_with_ai", 80.0, "Validando y optimizando cortes...")
            validated_cuts = self._validate_and_adjust_cuts(cuts_array, cached_video_info)
            
            self._update_progress("finalizing", 90.0, "Construyendo resultado final...")
            
            # Asegurar que video_path esté en cached_video_info
            cached_video_info_with_path = cached_video_info.copy()
            cached_video_info_with_path['video_path'] = video_path
            
            final_result = self._build_final_json(validated_cuts, cached_video_info_with_path, video_path)
            
            self._update_progress("complete", 100.0, "¡Procesamiento completado!")
            
            if not self.is_cancelled:
                completion_callback(True, final_result, "Processing completed successfully with cached transcription")
            
        except Exception as e:
            print(f"❌ Error in cached processing: {str(e)}")
            if not self.is_cancelled:
                completion_callback(False, None, f"Error: {str(e)}")
        
    def process_video_sync_with_cache_check(self, video_path: str, video_info: Dict) -> Dict:
        """
        Synchronous video processing with intelligent cache checking
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata
            
        Returns:
            Complete cuts data in the expected format
        """
        print(f"🚀 Starting cache-aware LLM video processing...")
        print(f"📁 Video path: {video_path}")
        
        # Verificar si hay cuts completos en caché
        if self.cache_manager.has_cuts_cache(video_path):
            print("🎯 Cuts cache found! Loading directly...")
            try:
                cached_cuts = self.cache_manager.load_cuts(video_path)
                if cached_cuts and 'cuts' in cached_cuts:
                    print(f"✅ Loaded {len(cached_cuts['cuts'])} cuts from cache")
                    return cached_cuts
            except Exception as e:
                print(f"⚠️ Failed to load cuts cache: {e}")
                # Continuar con procesamiento normal
        
        # Verificar si hay transcripción en caché
        if self.cache_manager.has_transcription_cache(video_path):
            print("📝 Transcription cache found! Skipping transcription...")
            return self._process_with_cached_transcription_sync(video_path, video_info)
        
        # No cache found, proceso normal
        print("🔄 No cache found, processing from scratch...")
        return self.process_video(video_path, video_info)

    def _process_with_cached_transcription_sync(self, video_path: str, video_info: Dict) -> Dict:
        """
        Synchronous processing using cached transcription
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata
            
        Returns:
            Complete cuts data
        """
        try:
            # Cargar transcripción del caché
            transcription_result = self.cache_manager.load_transcription(video_path)
            if not transcription_result:
                raise Exception("Failed to load cached transcription")
            
            cached_transcription, cached_video_info = transcription_result
            
            print(f"📂 Loaded cached transcription from cache")
            print(f"📝 Cached text length: {len(cached_transcription.get('text', ''))}")
            
            # Update progress 
            if self.progress_callback:
                self.progress_callback("analyzing_with_ai", 70.0, "Analyzing content with GPT-4...")
            
            # Analizar con LLM usando transcripción cacheada
            cuts_data = self._analyze_with_llm(cached_transcription, video_info)
            
            # Validar y optimizar
            if self.progress_callback:
                self.progress_callback("analyzing_with_ai", 90.0, "Validating and optimizing cuts...")
            
            optimized_cuts = self._validate_and_adjust_cuts(cuts_data, video_info)
            
            # Progress update
            if self.progress_callback:
                self.progress_callback("analyzing_with_ai", 95.0, "AI analysis complete")
            
            # Preparar resultado final
            if self.progress_callback:
                self.progress_callback("finalizing", 95.0, "Building final cuts data...")
            
            result = self._build_final_json(optimized_cuts, video_info, video_path)
            
            if self.progress_callback:
                self.progress_callback("complete", 100.0, "Processing complete!")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in cached transcription processing: {e}")
            # Fallback to normal processing
            return self.process_video(video_path, video_info)
        
    def process_video(self, video_path: str, video_info: Dict) -> Dict:
        """
        Main processing function - extracts audio, transcribes, and analyzes with LLM
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata (duration, filename, etc.)
            
        Returns:
            Complete cuts data in the expected format
        """
        print(f"🚀 Starting LLM video processing...")
        print(f"📁 Video path: {video_path}")
        print(f"📊 Video info: {video_info}")
        
        # Ensure video_path is in video_info for caching
        video_info_with_path = video_info.copy()
        video_info_with_path['video_path'] = video_path
        
        if self.is_cancelled:
            raise Exception("Processing cancelled")
            
        try:
            # Phase 1: Extract audio (0-30%)
            self._update_progress("extracting_audio", 0.0, "Extracting audio from video...")
            audio_path = self._extract_audio(video_path)
            print(f"🎵 Audio extracted to: {audio_path}")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            self._update_progress("extracting_audio", 30.0, "Audio extraction complete")
            
            # Phase 2: Generate transcription (30-70%)
            self._update_progress("generating_transcription", 30.0, "Generating transcription with Whisper...")
            transcript = self._transcribe_audio(audio_path, video_info_with_path)
            print(f"📝 Transcription completed. Text length: {len(transcript.get('text', ''))}")
            print(f"📝 Full transcript: {transcript}")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            self._update_progress("generating_transcription", 70.0, "Transcription complete")
            
            # Phase 3: LLM Analysis (70-95%)
            self._update_progress("analyzing_with_ai", 70.0, "Analyzing content with GPT-4...")
            cuts_array = self._analyze_with_llm(transcript, video_info_with_path)
            print(f"🤖 LLM analysis completed. Generated {len(cuts_array)} cuts")
            print(f"🤖 Generated cuts: {cuts_array}")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            # Validate and adjust cuts for quality
            self._update_progress("analyzing_with_ai", 90.0, "Validating and optimizing cuts...")
            validated_cuts = self._validate_and_adjust_cuts(cuts_array, video_info_with_path)
            print(f"🔍 Validation completed. Final cuts: {len(validated_cuts)} segments")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            self._update_progress("analyzing_with_ai", 95.0, "AI analysis complete")
            
            # Phase 4: Build final JSON (95-100%)
            self._update_progress("finalizing", 95.0, "Building final cuts data...")
            final_result = self._build_final_json(validated_cuts, video_info_with_path, video_path)
            print(f"✅ Final result built: {final_result}")
            
            # Cleanup
            self._cleanup_temp_file(audio_path)
            
            # Cleanup transcriber resources
            self.transcriber.cleanup()
            
            self._update_progress("complete", 100.0, "Processing complete!")
            print(f"🎉 LLM processing completed successfully!")
            
            return final_result
            
        except Exception as e:
            print(f"❌ Error in LLM processing: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video using FFmpeg
        
        Args:
            video_path: Path to input video
            
        Returns:
            Path to extracted audio file
        """
        print(f"🎵 Starting audio extraction from: {video_path}")
        
        # Create temporary file for audio
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_path = temp_audio.name
        temp_audio.close()
        
        print(f"🎵 Temporary audio file: {audio_path}")
        
        try:
            # Extract audio using ffmpeg-python
            (
                ffmpeg
                .input(video_path)
                .output(
                    audio_path,
                    acodec='pcm_s16le',  # 16-bit PCM for Whisper compatibility
                    ac=1,  # Mono audio
                    ar='16000'  # 16kHz sample rate (optimal for Whisper)
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            
            print(f"✅ Audio extraction successful")
            return audio_path
            
        except ffmpeg.Error as e:
            self._cleanup_temp_file(audio_path)
            error_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            print(f"❌ FFmpeg error: {error_msg}")
            raise Exception(f"Failed to extract audio: {error_msg}")
        except Exception as e:
            self._cleanup_temp_file(audio_path)
            print(f"❌ Unexpected error in audio extraction: {str(e)}")
            raise
    
    def _transcribe_audio(self, audio_path: str, video_info: Dict) -> Dict:
        """
        Transcribe audio using the smart Whisper transcriber with video metadata
        Automatically chooses between API and local based on file size and optimizes model selection
        
        Args:
            audio_path: Path to audio file
            video_info: Video metadata containing duration information
            
        Returns:
            Transcription with timestamps
        """
        print(f"🎙️ Starting intelligent transcription with adaptive model selection...")
        print(f"🎙️ Audio file: {audio_path}")
        
        try:
            # Use the smart transcriber with video info for optimal model selection
            transcript = self.transcriber.transcribe_with_video_info(
                audio_path, 
                video_info,
                progress_callback=self._update_progress
            )
            
            print(f"✅ Transcription successful")
            print(f"📝 Text preview: {transcript.get('text', '')[:200]}...")
            print(f"📝 Segments: {len(transcript.get('segments', []))}")
            
            # Save transcription to cache for recovery
            try:
                video_path = video_info.get('video_path', video_info.get('filename', 'unknown'))
                self.cache_manager.save_transcription(video_path, transcript, video_info)
            except Exception as cache_e:
                print(f"⚠️ Failed to save transcription cache: {cache_e}")
                # Don't fail the whole process if cache fails
            
            return transcript
            
        except Exception as e:
            print(f"❌ Error in transcription: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def _analyze_with_llm(self, transcript: Dict, video_info: Dict) -> List[Dict]:
        """
        Analyze transcript with GPT-4 to generate cuts
        
        Args:
            transcript: Whisper transcription result
            video_info: Video metadata
            
        Returns:
            Array of cuts as returned by LLM
        """
        print(f"🤖 Starting LLM analysis with multi-model fallback strategy")
        
        # Build the prompt
        prompt = self._build_analysis_prompt(transcript, video_info)
        print(f"🤖 Prompt built, length: {len(prompt)} characters")
        print(f"🤖 Prompt content:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            # Use model configuration from constructor (with environment variables)
            models_to_try = self.models_to_try
            
            response = None
            last_error = None
            cuts_data = None
            
            for model_info in models_to_try:
                model_name = model_info["name"]
                model_desc = model_info["description"]
                
                try:
                    print(f"🤖 Trying {model_desc}...")
                    
                    # Adjust parameters based on model type
                    is_reasoning_model = model_info.get("reasoning_model", False)
                    model_effort = model_info.get("effort", "medium")
                    
                    if model_name == "o4-mini":
                        # For o4-mini, use responses.create with specific format (no max_completion_tokens)
                        print(f"🧠 Using o4-mini with effort: {model_effort}")
                        
                        # Use the EXACT format from the example - reasoning models don't use completion tokens
                        response = self.openai_client.responses.create(
                            model="o4-mini",
                            input=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": prompt
                                        }
                                    ]
                                }
                            ],
                            text={
                                "format": {
                                    "type": "json_object"
                                }
                            },
                            reasoning={
                                "effort": model_effort,
                                "summary": None 
                            },
                            store=False
                        )
                        
                        # Extract response content from o4-mini format
                        try:
                            # For o4-mini responses, convert to string and parse later
                            response_content = str(response)
                            print(f"✅ Extracted o4-mini response as string")
                            
                            # Try to extract JSON from the string response
                            import re
                            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                            if json_match:
                                response_content = json_match.group(0)
                                print(f"✅ Extracted JSON from o4-mini response")
                                
                        except Exception as extract_error:
                            print(f"⚠️ Error extracting o4-mini response: {extract_error}")
                            response_content = str(response)
                        
                    elif is_reasoning_model:
                        # For other reasoning models (o1-preview, o1-mini), use simpler parameters
                        request_params = {
                            "model": model_name,
                            "messages": [
                                {
                                    "role": "user", 
                                    "content": prompt
                                }
                            ]
                        }
                        print(f"🧠 Using reasoning model parameters for {model_name}")
                        response = self.openai_client.chat.completions.create(**request_params)
                        response_content = response.choices[0].message.content
                        
                    else:
                        # For standard models, use full parameter set
                        request_params = {
                            "model": model_name,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": prompt
                                        }
                                    ]
                                }
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.3,  # Lower temperature for more consistent cuts
                            "max_completion_tokens": 8192,
                            "top_p": 1,
                            "frequency_penalty": 0,
                            "presence_penalty": 0
                        }
                        print(f"🎛️ Using standard model parameters for {model_name}")
                        response = self.openai_client.chat.completions.create(**request_params)
                        response_content = response.choices[0].message.content
                    
                    # Skip debug curl for o4-mini since it uses different API
                    if model_name != "o4-mini":
                        # Generate curl command for debugging
                        print(f"🐛 About to generate debug curl for model: {model_name}")
                        self._generate_debug_curl(request_params, model_name)
                        print(f"🐛 Debug curl generation completed for model: {model_name}")
                    
                    print(f"✅ {model_desc} response received successfully")
                    print(f"🤖 Raw LLM response from {model_name}:\n{'-'*50}\n{response_content[:500]}{'...' if len(response_content) > 500 else ''}\n{'-'*50}")
                    
                    if not response_content:
                        raise Exception("Empty response from LLM")
                        
                    response_text = response_content.strip()
                    
                    # Clean up the response (remove markdown code blocks if present)
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]  # Remove ```json
                        print(f"🤖 Removed ```json prefix")
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]  # Remove ```
                        print(f"🤖 Removed ``` suffix")
                    
                    # Check if response might be truncated
                    if not (response_text.strip().endswith(']') or response_text.strip().endswith('}')):
                        print(f"⚠️ Response appears to be truncated (doesn't end with ']' or '}}'), trying to fix...")
                        response_text = self._fix_truncated_json(response_text)
                    
                    # Try to parse JSON
                    parsed_response = json.loads(response_text)
                    
                    # Handle new format with "cuts" object or legacy array format
                    if isinstance(parsed_response, dict) and "cuts" in parsed_response:
                        cuts_data = parsed_response["cuts"]
                        print(f"✅ {model_desc} JSON parsing successful (object format), {len(cuts_data)} cuts found")
                    elif isinstance(parsed_response, list):
                        cuts_data = parsed_response
                        print(f"✅ {model_desc} JSON parsing successful (array format), {len(cuts_data)} cuts found")
                    else:
                        raise Exception("Invalid JSON structure: expected object with 'cuts' array or direct array")
                    
                    # IMMEDIATE VALIDATION: Check for invalid timestamps
                    print(f"🔍 Initial validation: checking for invalid timestamps...")
                    valid_cuts = []
                    for i, cut in enumerate(cuts_data):
                        start_time = cut.get("start", "00:00:00")
                        end_time = cut.get("end", "00:00:00")
                        
                        # Check for identical start/end times (0 duration)
                        if start_time == end_time:
                            print(f"❌ INVALID CUT DETECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has identical start/end times: {start_time}")
                            continue  # Skip this invalid cut
                        
                        # Check for valid timestamp format
                        try:
                            start_seconds = self._timestamp_to_seconds(start_time)
                            end_seconds = self._timestamp_to_seconds(end_time)
                            duration = end_seconds - start_seconds
                            
                            if duration <= 0:
                                print(f"❌ INVALID CUT DETECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has negative/zero duration: {duration}s")
                                continue  # Skip this invalid cut
                            
                            if duration < 30:
                                print(f"⚠️ SHORT CUT WARNING: Cut {i+1} '{cut.get('title', 'Unknown')}' has duration {duration}s (will be extended later)")
                            
                            valid_cuts.append(cut)
                            print(f"✅ Cut {i+1} passed initial validation: {duration}s duration")
                            
                        except Exception as ts_error:
                            print(f"❌ INVALID TIMESTAMPS: Cut {i+1} '{cut.get('title', 'Unknown')}' has malformed timestamps: {ts_error}")
                            continue  # Skip this invalid cut
                    
                    cuts_data = valid_cuts
                    print(f"🔍 Initial validation complete: {len(cuts_data)} valid cuts remaining")
                    
                    if not cuts_data:
                        raise Exception("All cuts had invalid timestamps after initial validation")
                    
                    # If we got here, parsing was successful
                    break  # Success, exit the loop
                    
                except json.JSONDecodeError as json_error:
                    print(f"❌ {model_desc} JSON parsing failed: {str(json_error)}")
                    last_error = json_error
                    # Try to fix and parse again for this model before giving up
                    try:
                        fixed_response = self._fix_truncated_json(str(response_content) if response_content else "")
                        parsed_fixed = json.loads(fixed_response)
                        
                        # Handle both formats
                        if isinstance(parsed_fixed, dict) and "cuts" in parsed_fixed:
                            cuts_data = parsed_fixed["cuts"]
                            print(f"✅ {model_desc} fixed JSON parsing successful (object format), {len(cuts_data)} cuts found")
                        elif isinstance(parsed_fixed, list):
                            cuts_data = parsed_fixed
                            print(f"✅ {model_desc} fixed JSON parsing successful (array format), {len(cuts_data)} cuts found")
                        else:
                            raise Exception("Invalid JSON structure after fix")
                        
                        # IMMEDIATE VALIDATION FOR FIXED JSON: Check for invalid timestamps
                        print(f"🔍 Initial validation (fixed JSON): checking for invalid timestamps...")
                        valid_cuts = []
                        for i, cut in enumerate(cuts_data):
                            start_time = cut.get("start", "00:00:00")
                            end_time = cut.get("end", "00:00:00")
                            
                            # Check for identical start/end times (0 duration)
                            if start_time == end_time:
                                print(f"❌ INVALID CUT DETECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has identical start/end times: {start_time}")
                                continue  # Skip this invalid cut
                            
                            # Check for valid timestamp format
                            try:
                                start_seconds = self._timestamp_to_seconds(start_time)
                                end_seconds = self._timestamp_to_seconds(end_time)
                                duration = end_seconds - start_seconds
                                
                                if duration <= 0:
                                    print(f"❌ INVALID CUT DETECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has negative/zero duration: {duration}s")
                                    continue  # Skip this invalid cut
                                
                                valid_cuts.append(cut)
                                print(f"✅ Cut {i+1} passed initial validation: {duration}s duration")
                                
                            except Exception as ts_error:
                                print(f"❌ INVALID TIMESTAMPS: Cut {i+1} '{cut.get('title', 'Unknown')}' has malformed timestamps: {ts_error}")
                                continue  # Skip this invalid cut
                        
                        cuts_data = valid_cuts
                        print(f"🔍 Initial validation (fixed JSON) complete: {len(cuts_data)} valid cuts remaining")
                        
                        if not cuts_data:
                            raise Exception("All cuts had invalid timestamps after initial validation (fixed JSON)")
                            
                        break  # Success after fix
                            
                    except Exception as fix_error:
                        print(f"❌ {model_desc} JSON fix also failed: {str(fix_error)}")
                        last_error = fix_error
                        continue  # Try next model
                    
                except Exception as model_error:
                    print(f"❌ {model_desc} failed: {str(model_error)}")
                    last_error = model_error
                    continue  # Try next model
            
            # If all models failed, try one final fallback strategy
            if cuts_data is None:
                print(f"⚠️ All models failed, attempting final fallback strategies...")
                
                # Try regex extraction as last resort if we have any response
                if 'response_content' in locals() and response_content:
                    try:
                        cuts_data = self._extract_valid_cuts_regex(str(response_content))
                        if cuts_data:
                            print(f"✅ Regex extraction successful, {len(cuts_data)} cuts found")
                        else:
                            raise Exception("No cuts found via regex")
                    except Exception as regex_error:
                        print(f"❌ Regex extraction failed: {str(regex_error)}")
                        last_error = regex_error
                
                # Final fallback: Create a single segment for the entire video
                if cuts_data is None:
                    duration = video_info.get('duration', '00:05:00')
                    cuts_data = [
                        {
                            "id": 1,
                            "start": "00:00:00",
                            "end": duration,
                            "title": "Complete Video",
                            "description": "Full video content (AI analysis failed to generate specific cuts)",
                            "duration": duration
                        }
                    ]
                    print(f"⚠️ Using final fallback: single segment for entire video")
            
            if not cuts_data:
                raise Exception(f"All models and fallback strategies failed. Last error: {str(last_error)}")
            
            print(f"✅ LLM analysis completed successfully")
            
            # Validate the format
            if not isinstance(cuts_data, list):
                print(f"⚠️ LLM response is not a list, attempting to wrap...")
                if isinstance(cuts_data, dict):
                    cuts_data = [cuts_data]
                else:
                    raise Exception("LLM response is not a valid cuts array")
                
            # Advanced validation with transcript segments for better boundaries
            transcript_segments = transcript.get('segments', [])
            
            # Validate each cut has required fields and apply quality validation
            validated_cuts = []
            for i, cut in enumerate(cuts_data):
                required_fields = ["start", "end", "title", "description"]
                
                # Check and fix missing fields
                if not all(field in cut for field in required_fields):
                    print(f"⚠️ Cut {i+1} missing fields, attempting to fix...")
                    
                    # Add missing fields with defaults
                    if "start" not in cut:
                        cut["start"] = "00:00:00" if i == 0 else validated_cuts[-1]["end"]
                    if "end" not in cut:
                        cut["end"] = video_info.get('duration', '00:05:00')
                    if "title" not in cut:
                        cut["title"] = f"Segment {i+1}"
                    if "description" not in cut:
                        cut["description"] = f"Video segment {i+1}"
                    if "id" not in cut:
                        cut["id"] = i + 1
                
                # Ensure duration is calculated
                if "duration" not in cut or not cut["duration"]:
                    start_seconds = self._timestamp_to_seconds(cut["start"])
                    end_seconds = self._timestamp_to_seconds(cut["end"])
                    duration_seconds = max(0, end_seconds - start_seconds)
                    cut["duration"] = self._seconds_to_timestamp(duration_seconds)
                
                # Apply advanced quality validation for natural boundaries
                if transcript_segments and self.enable_advanced_boundary_detection:
                    quality_validated_cut = self._validate_cut_quality(cut, transcript_segments)
                    validated_cuts.append(quality_validated_cut)
                else:
                    validated_cuts.append(cut)
                
                print(f"✅ Cut {i+1} validation passed: {cut.get('title', 'No title')}")
            
            print(f"✅ All cuts validated successfully: {len(validated_cuts)} segments")
            return validated_cuts
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"❌ Failed to parse response as JSON")
            raise Exception(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            print(f"❌ Error in LLM analysis: {str(e)}")
            print(f"❌ Exception type: {type(e).__name__}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise Exception(f"LLM analysis failed: {str(e)}")
    
    def _build_analysis_prompt(self, transcript: Dict, video_info: Dict) -> str:
        """Build the enhanced prompt for precise cut analysis that prevents abrupt cuts"""
        
        # Extract segments with timestamps
        segments_text = ""
        if 'segments' in transcript:
            for segment in transcript['segments']:
                start_time = self._seconds_to_timestamp(segment.get('start', 0))
                end_time = self._seconds_to_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                segments_text += f"[{start_time} - {end_time}] {text}\n"
        else:
            # Fallback to full text if segments not available
            segments_text = transcript.get('text', '')
        
        # Build video duration info
        duration = video_info.get('duration', 'Unknown')
        filename = os.path.basename(video_info.get('filename', 'video.mp4'))
        
        # TWO-PHASE SEPARATE ANALYSIS: Content first, then timestamps
        prompt = f"""You are a professional video content analyst and editor. Your task is to perform a STRICT two-phase analysis where you completely separate content analysis from timestamp analysis.

🎬 VIDEO INFORMATION:
- File: {filename}
- Duration: {duration}

📝 TRANSCRIPT (timestamps will be used LATER):
{segments_text}

🧠 **PHASE 1: PURE CONTENT ANALYSIS (IGNORE TIMESTAMPS)**

**Step 1.1: Read the Full Text**
- Read ONLY the spoken words/content, completely ignoring all timestamps
- Treat this as if you're reading a book or article transcript
- Focus solely on ideas, topics, themes, and concepts discussed

**Step 1.2: Identify All Major Topics**
Map out EVERY major topic discussed in the video:
- **Main themes** (topics that span several minutes of discussion)
- **Sub-topics** within each main theme  
- **Key stories, examples, anecdotes** (complete narratives)
- **Standalone insights** (important quotes, tips, principles)
- **Technical explanations** (step-by-step processes)
- **Philosophical discussions** (deeper thoughts, reflections)

**Step 1.3: Content Hierarchy Creation**
Organize the content into:
- **MAJOR DISCUSSIONS** (15+ minutes of related content)
- **TOPIC SEGMENTS** (5-15 minutes of focused discussion)  
- **CONCEPT EXPLANATIONS** (2-8 minutes of specific explanations)
- **KEY MOMENTS** (30 seconds - 3 minutes of high-value content)

**CRITICAL**: Do this analysis without looking at any timestamps. Focus only on what is actually discussed.

🎯 **PHASE 2: TIMESTAMP MAPPING (AFTER CONTENT ANALYSIS)**

**Step 2.1: Map Topics to Timestamps**
NOW, and only now, use the timestamps to find where each identified topic occurs:
- Locate the START of each major topic/discussion
- Find the natural END of each topic/discussion  
- Ensure you capture COMPLETE ideas from beginning to end
- Look for natural conversation boundaries

**Step 2.2: Create Comprehensive Cuts**
For each topic identified in Phase 1, create cuts that capture:
- **COMPLETE TOPICS**: Full discussions from introduction to conclusion
- **COMPLETE EXPLANATIONS**: Entire explanations including setup, examples, and conclusions
- **COMPLETE STORIES**: Full anecdotes from beginning to end
- **OVERLAPPING EXTRACTS**: Shorter cuts that highlight key moments within longer topics

**Step 2.3: Duration Guidelines by Content Type**
- **Educational/Deep Discussions**: 8-45 minutes (whatever the natural topic length requires)
- **Complete Explanations**: 3-15 minutes (full explanations with context)
- **Stories/Examples**: 2-8 minutes (complete narratives)
- **Key Insights/Tips**: 1-4 minutes (complete thoughts with context)
- **Viral Moments**: 30-90 seconds (punchy highlights from within longer topics)

🚨 **CRITICAL VALIDATION RULES**:

**Content Completeness**:
- NEVER cut in the middle of an explanation
- NEVER start a cut mid-topic without proper introduction
- NEVER end a cut before the speaker concludes their point
- ALWAYS include enough context for standalone understanding

**Title/Description Accuracy**:
- Titles must describe EXACTLY what happens in those specific timestamps
- Descriptions must match ONLY the content within that time range
- NO mixing information from different parts of the video
- Verify accuracy by re-reading the transcript segment

**Natural Boundaries**:
- Start cuts at topic introductions or natural conversation starts
- End cuts at topic conclusions or natural transition points
- Respect speech patterns and breathing points
- Ensure smooth entry and exit points

🎯 **RESPONSE FORMAT**:
Return a JSON object with this EXACT structure:

{{
  "cuts": [
    {{
      "id": 1,
      "start": "HH:MM:SS",
      "end": "HH:MM:SS", 
      "title": "Exact description of what is discussed in this time range",
      "description": "Detailed description of ONLY the content within these timestamps",
      "duration": "HH:MM:SS",
      "content_type": "major_discussion|topic_segment|concept_explanation|key_moment|viral_highlight"
    }}
  ]
}}

🚨 **ABSOLUTE REQUIREMENTS**:
- Generate cuts for ALL substantial content identified in Phase 1
- Prioritize COMPLETE topics over partial fragments  
- Create overlapping cuts when beneficial (long educational + short viral from same content)
- Ensure ZERO content gaps - every valuable topic should have a corresponding cut
- For a 2+ hour video, expect 15-30+ cuts covering all major content
- Focus on content completeness over artificial duration limits

Remember: Your goal is to extract EVERY valuable piece of content, ensuring nothing important is missed while maintaining complete accuracy between timestamps and descriptions."""        
        return prompt   

    def _build_final_json(self, cuts_array: List[Dict], video_info: Dict, video_path: str) -> Dict:
        """
        Build the final JSON object that matches the expected format
        
        Args:
            cuts_array: Array of cuts from LLM
            video_info: Video metadata
            video_path: Path to the original video file
            
        Returns:
            Complete cuts data object
        """
        # Calculate duration for each cut if not provided
        processed_cuts = []
        for cut in cuts_array:
            processed_cut = cut.copy()
            
            # Ensure duration is calculated if not provided
            if "duration" not in processed_cut or not processed_cut["duration"]:
                start_seconds = self._timestamp_to_seconds(cut["start"])
                end_seconds = self._timestamp_to_seconds(cut["end"])
                duration_seconds = end_seconds - start_seconds
                processed_cut["duration"] = self._seconds_to_timestamp(duration_seconds)
            
            processed_cuts.append(processed_cut)
        
        # Build the complete object matching the expected format
        final_data = {
            "cuts": processed_cuts,
            "video_info": {
                "filename": os.path.basename(video_info.get("filename", "video.mp4")),
                "duration": video_info.get("duration", "00:00:00"),
                "resolution": video_info.get("resolution", "Unknown"),
                "fps": video_info.get("fps", 30),
                "total_cuts": len(processed_cuts)
            }
        }
        
        # Save cuts data to cache for recovery
        try:
            processing_info = {
                "total_segments": len(cuts_array),
                "processed_cuts": len(processed_cuts),
                "processing_method": "llm_analysis"
            }
            self.cache_manager.save_cuts(video_path, final_data, processing_info)
        except Exception as cache_e:
            print(f"⚠️ Failed to save cuts cache: {cache_e}")
            # Don't fail the whole process if cache fails
        
        return final_data
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert HH:MM:SS format to seconds"""
        try:
            parts = timestamp.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:
                return float(parts[0])
        except (ValueError, IndexError):
            return 0.0
    
    def _cleanup_temp_file(self, file_path: str):
        """Clean up temporary files"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    def _validate_and_adjust_cuts(self, cuts_array: List[Dict], video_info: Optional[Dict] = None) -> List[Dict]:
        """
        Validate cuts and adjust short segments that don't meet quality criteria
        Also validates timing and fixes overlaps/gaps
        
        Args:
            cuts_array: Array of cuts from LLM
            video_info: Video metadata (optional, for getting duration)
            
        Returns:
            Validated and potentially adjusted cuts array
        """
        print(f"🔍 Validating cuts for minimum duration and timing requirements...")
        
        if not cuts_array:
            print(f"⚠️ No cuts to validate, returning empty list")
            return []
        
        # Get video duration for timing validation - try multiple sources
        video_duration = '01:00:00'  # Default fallback
        if video_info and 'duration' in video_info:
            video_duration = video_info['duration']
            print(f"📊 Using video duration from video_info: {video_duration}")
        else:
            print(f"⚠️ No video duration available, using fallback: {video_duration}")
        
        # IMMEDIATE PRE-VALIDATION: Remove any cuts with identical start/end
        print(f"🔍 PRE-VALIDATION: Checking for invalid cuts...")
        pre_validated_cuts = []
        for i, cut in enumerate(cuts_array):
            start_time = cut.get("start", "00:00:00")
            end_time = cut.get("end", "00:00:00")
            
            # Check for identical start/end times
            if start_time == end_time:
                print(f"❌ PRE-VALIDATION REJECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has identical start/end: {start_time}")
                continue
            
            # Check for valid duration calculation
            try:
                start_seconds = self._timestamp_to_seconds(start_time)
                end_seconds = self._timestamp_to_seconds(end_time)
                duration = end_seconds - start_seconds
                
                if duration <= 0:
                    print(f"❌ PRE-VALIDATION REJECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has zero/negative duration: {duration}s")
                    continue
                
                pre_validated_cuts.append(cut)
                print(f"✅ PRE-VALIDATION PASSED: Cut {i+1} has {duration}s duration")
                
            except Exception as e:
                print(f"❌ PRE-VALIDATION REJECTED: Cut {i+1} '{cut.get('title', 'Unknown')}' has invalid timestamps: {e}")
                continue
        
        if not pre_validated_cuts:
            print(f"❌ All cuts failed pre-validation!")
            return []
        
        print(f"🔍 PRE-VALIDATION complete: {len(cuts_array)} -> {len(pre_validated_cuts)} cuts passed")
        cuts_array = pre_validated_cuts
        
        validated_cuts = []
        short_segments_keywords = [
            'tip', 'insight', 'key', 'important', 'critical', 'essential', 
            'pro tip', 'quick tip', 'takeaway', 'lesson', 'principle',
            'rule', 'secret', 'hack', 'trick', 'warning', 'note'
        ]
        
        i = 0
        previous_end = "00:00:00"
        
        while i < len(cuts_array):
            current_cut = cuts_array[i]
            
            # First, validate and fix timing issues
            try:
                validated_cut = self._validate_cut_timing(current_cut, video_duration, previous_end)
            except Exception as e:
                print(f"⚠️ Cut {i+1} has critical timing issues, skipping: {str(e)}")
                # Skip this cut entirely - don't try to fix critically broken cuts
                i += 1
                continue
            
            # Calculate duration in seconds for quality check
            start_seconds = self._timestamp_to_seconds(validated_cut["start"])
            end_seconds = self._timestamp_to_seconds(validated_cut["end"])
            duration_seconds = end_seconds - start_seconds
            
            print(f"🔍 Validating cut {i+1}: '{validated_cut['title']}' - {duration_seconds:.1f} seconds")
            
            # Check if it's a short segment (< 30 seconds)
            if duration_seconds < 30:
                title_lower = validated_cut.get("title", "").lower()
                description_lower = validated_cut.get("description", "").lower()
                
                # Check if it contains quality indicators
                has_quality_indicators = any(
                    keyword in title_lower or keyword in description_lower 
                    for keyword in short_segments_keywords
                )
                
                if has_quality_indicators:
                    print(f"✅ Short segment approved: Contains quality indicators")
                    validated_cuts.append(validated_cut)
                    previous_end = validated_cut["end"]
                    i += 1
                else:
                    print(f"⚠️ Short segment needs merging: No quality indicators found")
                    # Try to merge with next segment if possible
                    if i + 1 < len(cuts_array):
                        next_cut = cuts_array[i + 1]
                        # Validate next cut timing first
                        try:
                            next_validated = self._validate_cut_timing(next_cut, video_duration, validated_cut["end"])
                            merged_cut = self._merge_cuts(validated_cut, next_validated)
                            print(f"🔗 Merged with next segment: '{merged_cut['title']}'")
                            validated_cuts.append(merged_cut)
                            previous_end = merged_cut["end"]
                            i += 2  # Skip next cut as it's been merged
                        except Exception as merge_e:
                            print(f"⚠️ Failed to merge cuts: {str(merge_e)}")
                            # Just keep the current cut without merging
                            validated_cuts.append(validated_cut)
                            previous_end = validated_cut["end"]
                            i += 1
                    else:
                        # Last segment, keep it even if short
                        print(f"📝 Keeping last segment even if short")
                        validated_cuts.append(validated_cut)
                        previous_end = validated_cut["end"]
                        i += 1
            else:
                # Segment is long enough, keep it
                validated_cuts.append(validated_cut)
                previous_end = validated_cut["end"]
                i += 1
        
        print(f"✅ Validation complete: {len(cuts_array)} -> {len(validated_cuts)} segments")
        return validated_cuts
    
    def _merge_cuts(self, cut1: Dict, cut2: Dict) -> Dict:
        """
        Merge two adjacent cuts into one
        
        Args:
            cut1: First cut
            cut2: Second cut
            
        Returns:
            Merged cut
        """
        # Calculate new duration with validation
        start_seconds = self._timestamp_to_seconds(cut1["start"])
        end_seconds = self._timestamp_to_seconds(cut2["end"])
        duration_seconds = end_seconds - start_seconds
        
        # Validate the merge will create a valid cut
        if duration_seconds <= 0:
            print(f"⚠️ MERGE ERROR: Would create invalid cut with duration {duration_seconds}s")
            # Return the longer of the two cuts instead of merging
            cut1_duration = self._timestamp_to_seconds(cut1.get("end", "00:00:00")) - self._timestamp_to_seconds(cut1.get("start", "00:00:00"))
            cut2_duration = self._timestamp_to_seconds(cut2.get("end", "00:00:00")) - self._timestamp_to_seconds(cut2.get("start", "00:00:00"))
            
            if cut1_duration >= cut2_duration:
                print(f"🔄 Returning cut1 instead of invalid merge")
                return cut1
            else:
                print(f"🔄 Returning cut2 instead of invalid merge")
                return cut2
        
        # Validate timestamps are reasonable
        if cut1["start"] == cut1["end"] or cut2["start"] == cut2["end"]:
            print(f"⚠️ MERGE ERROR: One of the cuts has identical start/end times")
            # Return the valid cut if one exists
            if cut1["start"] != cut1["end"]:
                return cut1
            elif cut2["start"] != cut2["end"]:
                return cut2
            else:
                # Both are invalid, create a safe default
                return {
                    "id": cut1["id"],
                    "start": "00:00:00",
                    "end": "00:00:30",
                    "title": f"Safe Merge: {cut1.get('title', 'Cut')}",
                    "description": f"Safe merge due to invalid timestamps: {cut1.get('description', '')}",
                    "duration": "00:00:30"
                }
        
        merged_cut = {
            "id": cut1["id"],
            "start": cut1["start"],
            "end": cut2["end"],
            "title": f"{cut1['title']} + {cut2['title']}",
            "description": f"{cut1['description']} Combined with: {cut2['description']}",
            "duration": self._seconds_to_timestamp(duration_seconds)
        }
        
        print(f"✅ Successfully merged cuts: {duration_seconds}s duration")
        return merged_cut
    
    def _fix_truncated_json(self, response_text: str) -> str:
        """
        Try to fix truncated JSON response from LLM with multiple recovery strategies
        
        Args:
            response_text: The potentially truncated JSON response
            
        Returns:
            Fixed JSON string or original if no fix possible
        """
        try:
            print(f"🔧 Attempting to fix truncated JSON...")
            original_text = response_text.strip()
            
            # Strategy 1: Try to find and complete the last valid JSON object
            last_complete_brace = original_text.rfind('}')
            if last_complete_brace != -1:
                # Keep everything up to the last complete object
                truncated_at_object = original_text[:last_complete_brace + 1]
                
                # Count brackets to see if we need to close the array
                open_brackets = truncated_at_object.count('[')
                close_brackets = truncated_at_object.count(']')
                
                # Add missing closing brackets
                missing_brackets = open_brackets - close_brackets
                if missing_brackets > 0:
                    fixed_text = truncated_at_object + ']' * missing_brackets
                    print(f"🔧 Strategy 1: Added {missing_brackets} missing closing bracket(s)")
                    
                    # Test if this creates valid JSON
                    try:
                        json.loads(fixed_text)
                        print(f"✅ Strategy 1 successful - valid JSON created")
                        return fixed_text
                    except json.JSONDecodeError:
                        print(f"⚠️ Strategy 1 failed - still invalid JSON")
            
            # Strategy 2: Try to extract valid cuts using regex as fallback
            print(f"🔧 Strategy 2: Attempting regex extraction...")
            extracted_cuts = self._extract_valid_cuts_regex(original_text)
            if extracted_cuts:
                fixed_json = json.dumps(extracted_cuts)
                print(f"✅ Strategy 2 successful - extracted {len(extracted_cuts)} cuts via regex")
                return fixed_json
            
            # Strategy 3: Create minimal valid response if all else fails
            print(f"🔧 Strategy 3: Creating minimal fallback response...")
            fallback_response = [
                {
                    "id": 1,
                    "start": "00:00:00",
                    "end": "00:05:00", 
                    "title": "Full Video Segment",
                    "description": "Complete video content (LLM analysis was incomplete)",
                    "duration": "00:05:00"
                }
            ]
            print(f"✅ Strategy 3: Created fallback response with 1 segment")
            return json.dumps(fallback_response)
            
        except Exception as e:
            print(f"❌ All JSON repair strategies failed: {str(e)}")
            # Return a minimal valid JSON as last resort
            return '[{"id": 1, "start": "00:00:00", "end": "00:05:00", "title": "Video Content", "description": "Content analysis failed", "duration": "00:05:00"}]'
    
    def _extract_valid_cuts_regex(self, text: str) -> List[Dict]:
        """
        Extract valid cut objects from malformed JSON using regex patterns
        
        Args:
            text: The malformed JSON text
            
        Returns:
            List of valid cut dictionaries
        """
        import re
        
        try:
            print(f"🔍 Extracting cuts using regex patterns...")
            cuts = []
            
            # Pattern to match JSON objects in the text
            # Looks for objects with id, start, end, title, description, duration
            object_pattern = r'\{[^{}]*"id"\s*:\s*(\d+)[^{}]*"start"\s*:\s*"([^"]+)"[^{}]*"end"\s*:\s*"([^"]+)"[^{}]*"title"\s*:\s*"([^"]+)"[^{}]*"description"\s*:\s*"([^"]+)"[^{}]*(?:"duration"\s*:\s*"([^"]+)")?[^{}]*\}'
            
            matches = re.finditer(object_pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    cut_id = int(match.group(1))
                    start_time = match.group(2)
                    end_time = match.group(3) 
                    title = match.group(4)
                    description = match.group(5)
                    duration = match.group(6) if match.group(6) else None
                    
                    # Calculate duration if not provided
                    if not duration:
                        start_seconds = self._timestamp_to_seconds(start_time)
                        end_seconds = self._timestamp_to_seconds(end_time)
                        duration_seconds = end_seconds - start_seconds
                        duration = self._seconds_to_timestamp(duration_seconds)
                    
                    cut = {
                        "id": cut_id,
                        "start": start_time,
                        "end": end_time,
                        "title": title,
                        "description": description,
                        "duration": duration
                    }
                    
                    cuts.append(cut)
                    print(f"✅ Extracted cut {cut_id}: {title}")
                    
                except Exception as e:
                    print(f"⚠️ Failed to parse regex match: {str(e)}")
                    continue
            
            print(f"🔍 Regex extraction found {len(cuts)} valid cuts")
            return cuts
            
        except Exception as e:
            print(f"❌ Regex extraction failed: {str(e)}")
            return []
    
    def _normalize_timestamp(self, timestamp: str, video_duration_str: Optional[str] = None) -> str:
        """
        Normalize and validate timestamp format
        
        Args:
            timestamp: Timestamp string in various formats
            video_duration_str: Total video duration for bounds checking
            
        Returns:
            Normalized timestamp in HH:MM:SS format
        """
        try:
            # Clean the timestamp
            timestamp = str(timestamp).strip()
            
            # Handle common malformed formats
            if '.' in timestamp:
                # Remove milliseconds if present (e.g., "00:01:30.5" -> "00:01:30")
                timestamp = timestamp.split('.')[0]
            
            # Ensure proper format
            parts = timestamp.split(':')
            
            if len(parts) == 1:
                # Assume seconds only
                seconds = float(parts[0])
                return self._seconds_to_timestamp(seconds)
            elif len(parts) == 2:
                # MM:SS format, add hours
                minutes, seconds = parts
                total_seconds = float(minutes) * 60 + float(seconds)
                return self._seconds_to_timestamp(total_seconds)
            elif len(parts) == 3:
                # HH:MM:SS format, validate each part
                hours, minutes, seconds = parts
                total_seconds = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                
                # Validate bounds
                if video_duration_str:
                    max_seconds = self._timestamp_to_seconds(video_duration_str)
                    total_seconds = min(total_seconds, max_seconds)
                
                return self._seconds_to_timestamp(total_seconds)
            else:
                # Invalid format, return default
                print(f"⚠️ Invalid timestamp format: {timestamp}, using 00:00:00")
                return "00:00:00"
                
        except (ValueError, TypeError) as e:
            print(f"⚠️ Timestamp normalization error for '{timestamp}': {str(e)}")
            return "00:00:00"
    
    def _validate_cut_timing(self, cut: Dict, video_duration_str: str, previous_end: str = "00:00:00") -> Dict:
        """
        Validate and fix cut timing issues
        
        Args:
            cut: Cut dictionary with start/end times
            video_duration_str: Total video duration 
            previous_end: End time of previous cut for gap detection
            
        Returns:
            Validated and corrected cut
        """
        try:
            # Normalize timestamps
            start_time = self._normalize_timestamp(cut.get("start", "00:00:00"), video_duration_str)
            end_time = self._normalize_timestamp(cut.get("end", video_duration_str), video_duration_str)
            
            # Convert to seconds for validation
            start_seconds = self._timestamp_to_seconds(start_time)
            end_seconds = self._timestamp_to_seconds(end_time)
            previous_end_seconds = self._timestamp_to_seconds(previous_end)
            video_duration_seconds = self._timestamp_to_seconds(video_duration_str)
            
            # Fix timing issues
            
            # 1. Ensure start is not before previous cut ended
            if start_seconds < previous_end_seconds:
                print(f"⚠️ Cut starts before previous cut ended, adjusting...")
                start_seconds = previous_end_seconds
                start_time = self._seconds_to_timestamp(start_seconds)
            
            # 2. Ensure end is after start with minimum 30 seconds
            if end_seconds <= start_seconds:
                print(f"⚠️ INVALID CUT DETECTED: Cut '{cut.get('title', 'Unknown')}' has start={start_time}, end={end_time}")
                print(f"⚠️ Start seconds: {start_seconds}, End seconds: {end_seconds}")
                print(f"⚠️ CRITICAL: This cut would have {end_seconds - start_seconds} seconds duration!")
                
                # This is a critical error - we cannot fix a cut where end <= start reliably
                # Instead of trying to force a fix, we should reject this cut entirely
                raise Exception(f"Critical timestamp error: Cut has end time ({end_time}) <= start time ({start_time}). This cut should be rejected.")
            
            # 3. Ensure minimum duration of 30 seconds
            duration_seconds = end_seconds - start_seconds
            if duration_seconds < 30:
                print(f"⚠️ DURATION TOO SHORT: Cut '{cut.get('title', 'Unknown')}' has duration {duration_seconds}s")
                print(f"⚠️ Extending to minimum 30 seconds...")
                # Give it at least 30 seconds or until video end
                end_seconds = min(start_seconds + 30, video_duration_seconds)
                end_time = self._seconds_to_timestamp(end_seconds)
                duration_seconds = end_seconds - start_seconds
                print(f"✅ Extended duration to: {duration_seconds}s")
            
            # 4. Ensure cut doesn't exceed video duration
            if end_seconds > video_duration_seconds:
                print(f"⚠️ Cut extends beyond video duration, truncating...")
                end_seconds = video_duration_seconds
                end_time = self._seconds_to_timestamp(end_seconds)
            
            # 4. Final validation check
            duration_seconds = end_seconds - start_seconds
            
            if duration_seconds < 30:
                print(f"⚠️ DURATION TOO SHORT: Cut '{cut.get('title', 'Unknown')}' has duration {duration_seconds}s")
                print(f"⚠️ Extending to minimum 30 seconds...")
                end_seconds = min(start_seconds + 30, video_duration_seconds)
                end_time = self._seconds_to_timestamp(end_seconds)
                duration_seconds = end_seconds - start_seconds
                print(f"✅ Final duration: {duration_seconds}s")
            
            if duration_seconds == 0:
                print(f"❌ CRITICAL ERROR: Cut still has 0 duration after validation!")
                print(f"❌ Cut details: start={start_time}, end={end_time}")
                # Force a valid cut
                end_seconds = min(start_seconds + 30, video_duration_seconds)
                end_time = self._seconds_to_timestamp(end_seconds)
                duration_seconds = end_seconds - start_seconds
                print(f"✅ FORCE-FIXED: duration now {duration_seconds}s")
            
            duration_time = self._seconds_to_timestamp(duration_seconds)
            
            # Update cut with validated times
            validated_cut = cut.copy()
            validated_cut.update({
                "start": start_time,
                "end": end_time,
                "duration": duration_time
            })
            
            return validated_cut
            
        except Exception as e:
            print(f"❌ Cut timing validation error: {str(e)}")
            # Return a safe default cut
            return {
                **cut,
                "start": previous_end,
                "end": self._seconds_to_timestamp(
                    min(self._timestamp_to_seconds(previous_end) + 30, 
                        self._timestamp_to_seconds(video_duration_str))
                ),
                "duration": "00:00:30"
            }

    def _validate_cut_quality(self, cut: Dict, transcript_segments: List[Dict]) -> Dict:
        """
        Advanced validation to ensure cuts respect natural speech boundaries
        
        Args:
            cut: Cut dictionary to validate
            transcript_segments: List of transcript segments with timestamps
            
        Returns:
            Validated and potentially adjusted cut
        """
        print(f"🔍 Advanced quality validation for: '{cut.get('title', 'Unknown')}'")
        
        start_seconds = self._timestamp_to_seconds(cut["start"])
        end_seconds = self._timestamp_to_seconds(cut["end"])
        
        # Find segments that overlap with this cut
        relevant_segments = []
        for segment in transcript_segments:
            seg_start = segment.get('start', 0)
            seg_end = segment.get('end', 0)
            
            # Check if segment overlaps with cut timeframe
            if not (seg_end < start_seconds or seg_start > end_seconds):
                relevant_segments.append(segment)
        
        if not relevant_segments:
            print(f"⚠️ No transcript segments found for cut timeframe")
            return cut
        
        # Analyze first and last segments for natural boundaries
        first_segment = relevant_segments[0]
        last_segment = relevant_segments[-1]
        
        # Check start boundary
        adjusted_cut = cut.copy()
        start_text = first_segment.get('text', '').strip()
        
        # Look for natural start indicators
        natural_starts = [
            'so ', 'now ', 'alright ', 'okay ', 'well ', 'and ', 'but ',
            'the thing is', 'what i want to', 'let me', 'i think', 'you know'
        ]
        
        if start_text.lower().startswith(tuple(natural_starts)):
            print(f"✅ Natural start boundary detected: '{start_text[:30]}...'")
        else:
            # Try to find a better start point within 10 seconds
            better_start = self._find_better_start_boundary(start_seconds, relevant_segments)
            if better_start != start_seconds:
                adjusted_cut["start"] = self._seconds_to_timestamp(better_start)
                print(f"🔧 Adjusted start time for better boundary: {adjusted_cut['start']}")
        
        # Check end boundary
        end_text = last_segment.get('text', '').strip()
        
        # Look for natural end indicators
        natural_ends = [
            '.', '?', '!', 'right?', 'okay?', 'you know?', 'exactly', 'perfect',
            'that\'s it', 'got it', 'makes sense', 'absolutely', 'definitely'
        ]
        
        has_natural_end = any(end_text.lower().endswith(ending) for ending in natural_ends)
        
        if has_natural_end:
            print(f"✅ Natural end boundary detected: '...{end_text[-30:]}'")
        else:
            # Try to find a better end point within 10 seconds
            better_end = self._find_better_end_boundary(end_seconds, relevant_segments)
            if better_end != end_seconds:
                adjusted_cut["end"] = self._seconds_to_timestamp(better_end)
                print(f"🔧 Adjusted end time for better boundary: {adjusted_cut['end']}")
        
        # Recalculate duration
        new_start = self._timestamp_to_seconds(adjusted_cut["start"])
        new_end = self._timestamp_to_seconds(adjusted_cut["end"])
        new_duration = new_end - new_start
        adjusted_cut["duration"] = self._seconds_to_timestamp(new_duration)
        
        print(f"✅ Quality validation complete: {new_duration:.1f}s duration")
        return adjusted_cut
    
    def _find_better_start_boundary(self, current_start: float, segments: List[Dict]) -> float:
        """Find a better start boundary within nearby segments"""
        search_window = 10  # seconds
        
        for segment in segments:
            seg_start = segment.get('start', 0)
            if abs(seg_start - current_start) <= search_window:
                text = segment.get('text', '').strip().lower()
                # Look for sentence beginnings or natural speech starts
                if (text.startswith(('so ', 'now ', 'alright ', 'okay ', 'well ')) or
                    text.startswith(('the ', 'i ', 'you ', 'we ', 'that ')) or
                    text.startswith('and ') and len(text) > 10):
                    return seg_start
        
        return current_start
    
    def _find_better_end_boundary(self, current_end: float, segments: List[Dict]) -> float:
        """Find a better end boundary within nearby segments"""
        search_window = 10  # seconds
        
        for segment in reversed(segments):
            seg_end = segment.get('end', 0)
            if abs(seg_end - current_end) <= search_window:
                text = segment.get('text', '').strip()
                # Look for sentence endings or natural speech conclusions
                if (text.endswith(('.', '?', '!', 'right?', 'okay?')) or
                    text.lower().endswith(('you know', 'exactly', 'perfect', 'got it'))):
                    return seg_end
        
        return current_end
    
    def _generate_debug_curl(self, request_params: Dict, model_name: str):
        """
        Generate a curl command equivalent to the OpenAI API request for debugging
        
        Args:
            request_params: The request parameters being sent to OpenAI
            model_name: The model being used
        """
        try:
            import json
            import traceback
            from datetime import datetime
            
            print(f"🐛 Starting debug curl generation for {model_name}")
            
            # Create debug directory if it doesn't exist
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "debug")
            print(f"🐛 Debug directory path: {debug_dir}")
            os.makedirs(debug_dir, exist_ok=True)
            print(f"🐛 Debug directory created/verified")
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            curl_file = os.path.join(debug_dir, f"debug_curl_{model_name}_{timestamp}.txt")
            print(f"🐛 Curl file path: {curl_file}")
            
            # Prepare the curl command
            curl_command = f"""#!/bin/bash
# Debug curl command for OpenAI API request
# Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Model: {model_name}
# Request parameters: {json.dumps(request_params, indent=2)}

curl -X POST "https://api.openai.com/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {self.api_key}" \\
  -d '{json.dumps(request_params, indent=2)}'

# To test this curl command:
# 1. Save this file as debug_curl.sh
# 2. Make it executable: chmod +x debug_curl.sh
# 3. Run it: ./debug_curl.sh
# 4. Or copy the curl command and run it directly in terminal

# Alternative one-liner (escape quotes as needed):
# curl -X POST "https://api.openai.com/v1/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer {self.api_key}" -d '{json.dumps(request_params).replace('"', '\\"')}'
"""
            
            print(f"🐛 Curl command prepared, writing to file...")
            
            # Write to file
            with open(curl_file, 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            print(f"🐛 Debug curl command saved to: {curl_file}")
            print(f"🐛 You can test the API request directly using this curl command")
            
            # Also create a simplified version without the API key for sharing
            safe_curl_file = os.path.join(debug_dir, f"debug_curl_safe_{model_name}_{timestamp}.txt")
            safe_curl_command = curl_command.replace(self.api_key or "API_KEY", "YOUR_API_KEY_HERE")
            
            with open(safe_curl_file, 'w', encoding='utf-8') as f:
                f.write(safe_curl_command)
            
            print(f"🐛 Safe curl command (without API key) saved to: {safe_curl_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to generate debug curl: {str(e)}")
            print(f"⚠️ Exception type: {type(e).__name__}")
            print(f"⚠️ Full traceback: {traceback.format_exc()}")
            # Don't fail the main process if curl generation fails

    # End of class
