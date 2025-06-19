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
from .whisper_transcriber import WhisperTranscriber
from ..utils.data_cache import DataCacheManager

# Print version info for debugging
print(f"🔍 OpenAI library version: {openai.__version__}")


class LLMCutsProcessor:
    """
    Processes video files to automatically generate cuts using AI transcription and LLM analysis
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the LLM processor
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        
        # Initia ize OpenAI client with error handling
        try:
            print(f"🔑 Initializing OpenAI client...")
            self.openai_client = openai.OpenAI(api_key=api_key)
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
                import os
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
        print(f"🤖 Starting LLM analysis with GPT-4o")
        
        # Build the prompt
        prompt = self._build_analysis_prompt(transcript, video_info)
        print(f"🤖 Prompt built, length: {len(prompt)} characters")
        print(f"🤖 Prompt content:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        try:
            print(f"🤖 Sending request to GPT-4o...")
            # Call GPT-4o (latest and most capable model)
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a video editing expert. Analyze transcripts and suggest logical cut points for video segments. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=2000
            )
            
            print(f"✅ GPT-4o response received")
            
            # Parse the response
            response_content = response.choices[0].message.content
            print(f"🤖 Raw LLM response:\n{'-'*50}\n{response_content}\n{'-'*50}")
            
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
            
            print(f"🤖 Cleaned response:\n{'-'*50}\n{response_text}\n{'-'*50}")
            
            # Parse JSON
            cuts_data = json.loads(response_text)
            print(f"✅ JSON parsing successful, {len(cuts_data)} cuts found")
            
            # Validate the format
            if not isinstance(cuts_data, list):
                raise Exception("LLM response is not a list of cuts")
                
            # Validate each cut has required fields
            for i, cut in enumerate(cuts_data):
                required_fields = ["start", "end", "title", "description"]
                for field in required_fields:
                    if field not in cut:
                        raise Exception(f"Cut {i+1} missing required field: {field}")
                print(f"✅ Cut {i+1} validation passed: {cut.get('title', 'No title')}")
            
            print(f"✅ All cuts validated successfully")
            return cuts_data
            
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
        
        # Build the prompt without f-string to avoid JSON bracket conflicts
        prompt = f"""
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

RESPONSE FORMAT (JSON Array only):
[
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
  }},
  {{
    "id": 4,
    "start": "00:02:15",
    "end": "00:02:45", 
    "title": "Critical Warning",
    "description": "Important cautionary advice to avoid common mistakes (SHORT SEGMENT JUSTIFIED)",
    "duration": "00:00:30"
  }},
  {{
    "id": 5,
    "start": "00:02:45",
    "end": "00:04:10", 
    "title": "Second Practical Example",
    "description": "Different scenario demonstrating alternative approach",
    "duration": "00:01:25"
  }},
  {{
    "id": 6,
    "start": "00:04:10",
    "end": "00:04:55", 
    "title": "Pro Tip for Advanced Users",
    "description": "Advanced technique for experienced practitioners",
    "duration": "00:00:45"
  }},
  {{
    "id": 7,
    "start": "00:04:55",
    "end": "00:05:30", 
    "title": "Summary and Next Steps",
    "description": "Recap of key points and actionable next steps",
    "duration": "00:00:35"
  }}
]

IMPORTANT: 
- MAXIMUM GRANULARITY: Create as many meaningful segments as possible - don't group related content unnecessarily
- Think like a viewer who wants to jump to specific concepts, examples, or tips quickly
- Each segment should represent a distinct piece of value that someone might want to reference independently
- CRITICAL: Segments under 30 seconds must contain exceptionally valuable, complete standalone content
- Better to have many precise, focused segments than fewer broad ones
- Respond ONLY with the JSON array, no additional text
- Ensure timestamps are sequential and don't overlap
- Calculate duration correctly for each segment
- Use HH:MM:SS format for all times
- Aim for comprehensive coverage - every distinct concept should have its own segment
"""
        
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
        
        Args:
            cuts_array: Array of cuts from LLM
            
        Returns:
            Validated and potentially adjusted cuts array
        """
        print(f"🔍 Validating cuts for minimum duration requirements...")
        
        validated_cuts = []
        short_segments_keywords = [
            'tip', 'insight', 'key', 'important', 'critical', 'essential', 
            'pro tip', 'quick tip', 'takeaway', 'lesson', 'principle',
            'rule', 'secret', 'hack', 'trick', 'warning', 'note'
        ]
        
        i = 0
        while i < len(cuts_array):
            current_cut = cuts_array[i]
            
            # Calculate duration in seconds
            start_seconds = self._timestamp_to_seconds(current_cut["start"])
            end_seconds = self._timestamp_to_seconds(current_cut["end"])
            duration_seconds = end_seconds - start_seconds
            
            print(f"🔍 Validating cut {i+1}: '{current_cut['title']}' - {duration_seconds:.1f} seconds")
            
            # Check if it's a short segment (< 30 seconds)
            if duration_seconds < 30:
                title_lower = current_cut.get("title", "").lower()
                description_lower = current_cut.get("description", "").lower()
                
                # Check if it contains quality indicators
                has_quality_indicators = any(
                    keyword in title_lower or keyword in description_lower 
                    for keyword in short_segments_keywords
                )
                
                if has_quality_indicators:
                    print(f"✅ Short segment approved: Contains quality indicators")
                    validated_cuts.append(current_cut)
                    i += 1
                else:
                    print(f"⚠️ Short segment needs merging: No quality indicators found")
                    # Try to merge with next segment if possible
                    if i + 1 < len(cuts_array):
                        next_cut = cuts_array[i + 1]
                        merged_cut = self._merge_cuts(current_cut, next_cut)
                        print(f"🔗 Merged with next segment: '{merged_cut['title']}'")
                        validated_cuts.append(merged_cut)
                        i += 2  # Skip next cut as it's been merged
                    else:
                        # Last segment, keep it even if short
                        print(f"📝 Keeping last segment even if short")
                        validated_cuts.append(current_cut)
                        i += 1
            else:
                # Segment is long enough, keep it
                validated_cuts.append(current_cut)
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


# Progress phases for UI
PROGRESS_PHASES = {
    "extracting_audio": "Extracting Audio...",
    "generating_transcription": "Generating Transcription...", 
    "analyzing_with_ai": "Analyzing with AI...",
    "finalizing": "Finalizing Results...",
    "complete": "Complete!"
}
