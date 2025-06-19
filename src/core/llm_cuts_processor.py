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
        
        # Initialize OpenAI client with error handling
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
        
    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates"""
        self.progress_callback = callback
        
    def cancel_processing(self):
        """Cancel the current processing operation"""
        self.is_cancelled = True
        
    def _update_progress(self, phase: str, progress: float, message: str = ""):
        """Update progress and call callback if set"""
        if self.is_cancelled:
            return
            
        self.current_phase = phase
        self.current_progress = progress
        
        if self.progress_callback:
            self.progress_callback(phase, progress, message)
    
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
                result = self.process_video(video_path, video_info)
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
            transcript = self._transcribe_audio(audio_path)
            print(f"📝 Transcription completed. Text length: {len(transcript.get('text', ''))}")
            print(f"📝 Full transcript: {transcript}")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            self._update_progress("generating_transcription", 70.0, "Transcription complete")
            
            # Phase 3: LLM Analysis (70-95%)
            self._update_progress("analyzing_with_ai", 70.0, "Analyzing content with GPT-4...")
            cuts_array = self._analyze_with_llm(transcript, video_info)
            print(f"🤖 LLM analysis completed. Generated {len(cuts_array)} cuts")
            print(f"🤖 Generated cuts: {cuts_array}")
            
            if self.is_cancelled:
                self._cleanup_temp_file(audio_path)
                raise Exception("Processing cancelled")
                
            self._update_progress("analyzing_with_ai", 95.0, "AI analysis complete")
            
            # Phase 4: Build final JSON (95-100%)
            self._update_progress("finalizing", 95.0, "Building final cuts data...")
            final_result = self._build_final_json(cuts_array, video_info)
            print(f"✅ Final result built: {final_result}")
            
            # Cleanup
            self._cleanup_temp_file(audio_path)
            
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
    
    def _transcribe_audio(self, audio_path: str) -> Dict:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcription with timestamps
        """
        print(f"🎙️ Starting transcription with Whisper API")
        print(f"🎙️ Audio file: {audio_path}")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                print(f"🎙️ Sending audio to Whisper API...")
                # Use Whisper API with timestamp information
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"  # Get detailed response with timestamps
                )
                
            result = transcript.model_dump()
            print(f"✅ Whisper transcription successful")
            print(f"📝 Transcript text preview: {result.get('text', '')[:200]}...")
            print(f"📝 Number of segments: {len(result.get('segments', []))}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in Whisper transcription: {str(e)}")
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
1. Identify complete thematic segments that make sense as standalone pieces
2. Each segment should cover a complete topic or idea, regardless of duration
3. Segments can be short (even 20-30 seconds) if the topic is brief and complete
4. Segments can be long (several minutes) if the topic requires extended explanation
5. Avoid cutting in the middle of explanations or important content
6. Look for natural topic transitions, introductions, conclusions, or subject changes
7. Create descriptive titles that clearly indicate what each segment covers
8. Ensure each segment tells a complete story or covers a complete concept

RESPONSE FORMAT (JSON Array only):
[
  {{
    "id": 1,
    "start": "00:00:05",
    "end": "00:00:25",
    "title": "Quick Introduction",
    "description": "Brief welcome and overview of what will be covered",
    "duration": "00:00:20"
  }},
  {{
    "id": 2,
    "start": "00:00:25", 
    "end": "00:03:45",
    "title": "Main Concept Explanation",
    "description": "Detailed explanation of the core concept with examples",
    "duration": "00:03:20"
  }},
  {{
    "id": 3,
    "start": "00:03:45",
    "end": "00:04:15", 
    "title": "Quick Tip",
    "description": "Short practical tip related to the main concept",
    "duration": "00:00:30"
  }}
]

IMPORTANT: 
- Focus on thematic completeness rather than duration constraints
- Let content determine segment boundaries naturally
- Respond ONLY with the JSON array, no additional text
- Ensure timestamps are sequential and don't overlap
- Calculate duration correctly for each segment
- Use HH:MM:SS format for all times
- Generate as many or as few segments as the content naturally suggests
"""
        
        return prompt
    
    def _build_final_json(self, cuts_array: List[Dict], video_info: Dict) -> Dict:
        """
        Build the final JSON object that matches the expected format
        
        Args:
            cuts_array: Array of cuts from LLM
            video_info: Video metadata
            
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


# Progress phases for UI
PROGRESS_PHASES = {
    "extracting_audio": "Extracting Audio...",
    "generating_transcription": "Generating Transcription...", 
    "analyzing_with_ai": "Analyzing with AI...",
    "finalizing": "Finalizing Results...",
    "complete": "Complete!"
}
