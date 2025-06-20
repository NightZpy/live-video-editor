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
        self.default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
        self.max_completion_tokens = int(os.getenv('MAX_COMPLETION_TOKENS', '8192'))
        
        # Model configuration with fallback strategy
        self.models_to_try = [
            {
                "name": self.default_model, 
                "description": f"{self.default_model} (primary, from config)", 
                "max_completion_tokens": self.max_completion_tokens
            },
            {
                "name": "gpt-4o-mini", 
                "description": "GPT-4o Mini (fallback, faster, cost-effective)", 
                "max_completion_tokens": self.max_completion_tokens
            },
            {
                "name": "gpt-4.1-mini", 
                "description": "GPT-4.1 Mini (fallback, balanced performance)", 
                "max_completion_tokens": self.max_completion_tokens
            },
            {
                "name": "gpt-4.1", 
                "description": "GPT-4.1 (final fallback, most capable)", 
                "max_completion_tokens": self.max_completion_tokens
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
                os.environ['OPENAI_API_KEY'] = api_key
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
            validated_cuts = self._validate_and_adjust_cuts(cuts_array)
            
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
            
            optimized_cuts = self._validate_and_adjust_cuts(cuts_data)
            
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
            validated_cuts = self._validate_and_adjust_cuts(cuts_array)
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
                    
                    # Prepare request parameters using the EXACT format from the working example
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
                        "temperature": 1,
                        "max_completion_tokens": 8192,
                        "top_p": 1,
                        "frequency_penalty": 0,
                        "presence_penalty": 0
                    }
                    
                    # Generate curl command for debugging
                    print(f"🐛 About to generate debug curl for model: {model_name}")
                    self._generate_debug_curl(request_params, model_name)
                    print(f"🐛 Debug curl generation completed for model: {model_name}")
                    
                    response = self.openai_client.chat.completions.create(**request_params)
                    
                    print(f"✅ {model_desc} response received successfully")
                    
                    # Parse the response immediately to check if it's valid
                    response_content = response.choices[0].message.content
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
                    
                    # If we got here, parsing was successful
                    break  # Success, exit the loop
                    
                except json.JSONDecodeError as json_error:
                    print(f"❌ {model_desc} JSON parsing failed: {str(json_error)}")
                    last_error = json_error
                    # Try to fix and parse again for this model before giving up
                    try:
                        fixed_response = self._fix_truncated_json(response_content if 'response_content' in locals() else "")
                        parsed_fixed = json.loads(fixed_response)
                        
                        # Handle both formats
                        if isinstance(parsed_fixed, dict) and "cuts" in parsed_fixed:
                            cuts_data = parsed_fixed["cuts"]
                            print(f"✅ {model_desc} fixed JSON parsing successful (object format), {len(cuts_data)} cuts found")
                            break  # Success after fix
                        elif isinstance(parsed_fixed, list):
                            cuts_data = parsed_fixed
                            print(f"✅ {model_desc} fixed JSON parsing successful (array format), {len(cuts_data)} cuts found")
                            break  # Success after fix
                        else:
                            raise Exception("Invalid JSON structure after fix")
                            
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
                        cuts_data = self._extract_valid_cuts_regex(response_content)
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
                
            # Validate each cut has required fields
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
        """Build the prompt for LLM analysis"""
        
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
        
        # Build the prompt with system instructions included
        prompt = f"""You are a video editing expert. Analyze transcripts and suggest logical cut points for video segments.

Analyze this video transcript and suggest logical cut points to create thematic segments based on natural content flow.

VIDEO INFORMATION:
- File: {filename}
- Duration: {duration}

TRANSCRIPT WITH TIMESTAMPS:
{segments_text}

INSTRUCTIONS:
1. GRANULAR ANALYSIS: Analyze the transcript with maximum granularity to identify ALL possible natural cut points
2. Detect EVERY thematic shift, no matter how small - including:
   - Major topic changes (chapters/sections)
   - Sub-topic transitions within larger themes
   - Individual examples or case studies
   - Specific tips or insights
   - Q&A segments or different speakers
   - Practical demonstrations
   - Conceptual explanations vs. practical applications
   - Introduction/body/conclusion of sub-topics
3. DO NOT group related content into large blocks - identify each distinct concept separately
4. MINIMUM DURATION RULE: Segments should be at least 30 seconds long UNLESS they contain exceptionally complete and highly valuable standalone content
5. Short segments (under 30 seconds) are ONLY allowed when:
   - The content is a complete, self-contained concept or tip
   - The information is particularly valuable or insightful
   - It represents a distinct, finished thought or instruction
   - It would lose meaning if combined with adjacent content
6. PRIORITIZE GRANULARITY: When in doubt between creating one large segment or multiple smaller ones, choose multiple smaller segments if each covers a distinct concept
7. Avoid cutting in the middle of explanations, but DO cut between different explanations, examples, or concepts
8. Look for natural micro-transitions like "Now let's talk about...", "Another example is...", "Here's a key point...", "Moving on to..."
9. Each segment should be immediately useful and consumable as a standalone piece
10. Create descriptive, specific titles that clearly indicate the exact content of each segment

RESPONSE FORMAT - CRITICAL JSON STRUCTURE:
You MUST respond with a JSON object containing a "cuts" array. Follow this EXACT structure:

{{
  "cuts": [
    {{
      "id": 1,
      "start": "00:00:00",
      "end": "00:00:35",
      "title": "Welcome and Introduction",
      "description": "Opening greeting and brief overview of the session",
      "duration": "00:00:35"
    }},
    {{
      "id": 2,
      "start": "00:00:35", 
      "end": "00:01:20",
      "title": "Main Topic Definition",
      "description": "Clear definition and explanation of the primary concept",
      "duration": "00:00:45"
    }},
    {{
      "id": 3,
      "start": "00:01:20",
      "end": "00:02:15", 
      "title": "First Practical Example",
      "description": "Detailed walkthrough of first use case scenario",
      "duration": "00:00:55"
    }}
  ]
}}

IMPORTANT RULES: 
- MAXIMUM GRANULARITY: Create as many meaningful segments as possible - don't group related content unnecessarily
- Think like a viewer who wants to jump to specific concepts, examples, or tips quickly
- Each segment should represent a distinct piece of value that someone might want to reference independently
- CRITICAL: Segments under 30 seconds must contain exceptionally valuable, complete standalone content
- Better to have many precise, focused segments than fewer broad ones
- Respond ONLY with the JSON object containing the "cuts" array
- Ensure timestamps are sequential and don't overlap
- Calculate duration correctly for each segment
- Use HH:MM:SS format for all times
- Aim for comprehensive coverage - every distinct concept should have its own segment"""
        
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
    
    def _validate_and_adjust_cuts(self, cuts_array: List[Dict]) -> List[Dict]:
        """
        Validate cuts and adjust short segments that don't meet quality criteria
        Also validates timing and fixes overlaps/gaps
        
        Args:
            cuts_array: Array of cuts from LLM
            
        Returns:
            Validated and potentially adjusted cuts array
        """
        print(f"🔍 Validating cuts for minimum duration and timing requirements...")
        
        if not cuts_array:
            print(f"⚠️ No cuts to validate, returning empty list")
            return []
        
        # Get video duration for timing validation
        video_duration = getattr(self, '_current_video_duration', '01:00:00')  # Default fallback
        
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
                print(f"⚠️ Error validating cut timing: {str(e)}")
                # Create a safe default cut
                validated_cut = {
                    "id": current_cut.get("id", i + 1),
                    "start": previous_end,
                    "end": self._seconds_to_timestamp(
                        min(self._timestamp_to_seconds(previous_end) + 30, 
                            self._timestamp_to_seconds(video_duration))
                    ),
                    "title": current_cut.get("title", f"Segment {i + 1}"),
                    "description": current_cut.get("description", f"Video segment {i + 1}"),
                    "duration": "00:00:30"
                }
            
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
                        next_validated = self._validate_cut_timing(next_cut, video_duration, validated_cut["end"])
                        merged_cut = self._merge_cuts(validated_cut, next_validated)
                        print(f"🔗 Merged with next segment: '{merged_cut['title']}'")
                        validated_cuts.append(merged_cut)
                        previous_end = merged_cut["end"]
                        i += 2  # Skip next cut as it's been merged
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
        # Calculate new duration
        start_seconds = self._timestamp_to_seconds(cut1["start"])
        end_seconds = self._timestamp_to_seconds(cut2["end"])
        duration_seconds = end_seconds - start_seconds
        
        merged_cut = {
            "id": cut1["id"],
            "start": cut1["start"],
            "end": cut2["end"],
            "title": f"{cut1['title']} + {cut2['title']}",
            "description": f"{cut1['description']} Combined with: {cut2['description']}",
            "duration": self._seconds_to_timestamp(duration_seconds)
        }
        
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
                    duration = match.group(6) if match.group(6) else None;
                    
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
            
            # 2. Ensure end is after start
            if end_seconds <= start_seconds:
                print(f"⚠️ Cut end is not after start, adjusting...")
                # Give it at least 30 seconds or until video end
                end_seconds = min(start_seconds + 30, video_duration_seconds)
                end_time = self._seconds_to_timestamp(end_seconds)
            
            # 3. Ensure cut doesn't exceed video duration
            if end_seconds > video_duration_seconds:
                print(f"⚠️ Cut extends beyond video duration, truncating...")
                end_seconds = video_duration_seconds
                end_time = self._seconds_to_timestamp(end_seconds)
            
            # 4. Recalculate duration
            duration_seconds = end_seconds - start_seconds
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
            safe_curl_command = curl_command.replace(self.api_key, "YOUR_API_KEY_HERE")
            
            with open(safe_curl_file, 'w', encoding='utf-8') as f:
                f.write(safe_curl_command)
            
            print(f"🐛 Safe curl command (without API key) saved to: {safe_curl_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to generate debug curl: {str(e)}")
            print(f"⚠️ Exception type: {type(e).__name__}")
            print(f"⚠️ Full traceback: {traceback.format_exc()}")
            # Don't fail the main process if curl generation fails

    # End of class
