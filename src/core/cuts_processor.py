"""
Cuts Processor for orchestrating the two-phase video analysis and cuts generation
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Callable
from .llm_processor import LLMProcessor
from .prompt_loader import PromptLoader
from ..utils.data_cache import DataCacheManager


class CutsProcessor:
    """
    Main orchestrator for the two-phase video analysis:
    1. Thematic analysis without timestamps
    2. Mapping themes to timestamps for precise cuts
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 prompts_dir: Optional[str] = None,
                 cache_manager: Optional[DataCacheManager] = None):
        """
        Initialize the cuts processor
        
        Args:
            api_key: OpenAI API key (optional)
            prompts_dir: Directory containing prompt templates (optional) 
            cache_manager: Cache manager instance (optional)
        """
        print(f"🎬 CutsProcessor: Initializing...")
        
        # Initialize components
        self.llm_processor = LLMProcessor(api_key=api_key)
        self.prompt_loader = PromptLoader(prompts_dir=prompts_dir)
        
        # Cache manager (create if not provided)
        if cache_manager:
            self.cache_manager = cache_manager
        else:
            self.cache_manager = DataCacheManager()
        
        # Quality settings
        self.min_cut_duration = float(os.getenv('MIN_CUT_DURATION', '30.0'))  # 30 seconds
        self.max_cuts = int(os.getenv('MAX_CUTS', '50'))
        self.prefer_longer_cuts = os.getenv('PREFER_LONGER_CUTS', 'true').lower() == 'true'
        
        print(f"🎬 CutsProcessor: Initialized with settings:")
        print(f"  - Min cut duration: {self.min_cut_duration}s")
        print(f"  - Max cuts: {self.max_cuts}")
        print(f"  - Prefer longer cuts: {self.prefer_longer_cuts}")

    def process(self, 
                video_path: str, 
                video_info: Dict,
                progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Main processing method - orchestrates the two-phase analysis with intelligent caching
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of cuts with titles, descriptions and timestamps
        """
        try:
            print(f"🎬 CutsProcessor: Starting intelligent processing for {video_path}")
            
            # 1. Verificar cuts completos (ya existe) - máxima prioridad
            if self.cache_manager.has_cuts_cache(video_path):
                print(f"✅ CutsProcessor: Found complete cuts cache, loading immediately...")
                cached_cuts = self.cache_manager.load_cuts(video_path)
                if cached_cuts and 'cuts' in cached_cuts:
                    if progress_callback:
                        progress_callback("Cargando cortes desde cache...", 100)
                    cuts = cached_cuts['cuts']
                    print(f"✅ CutsProcessor: Loaded {len(cuts)} cuts from cache")
                    return cuts
            
            if progress_callback:
                progress_callback("Verificando transcripción...", 10)
            
            # 2. Obtener transcripción (verificar cache primero)
            transcription_data = self._get_or_create_transcription(video_path, video_info, progress_callback)
            
            if progress_callback:
                progress_callback("Verificando análisis de temas...", 30)
            
            # 3. Obtener análisis de temas (verificar cache primero) - NUEVO
            topics_result = self._get_or_create_topics(video_path, transcription_data, video_info, progress_callback)
            
            if progress_callback:
                progress_callback("Generando cortes precisos...", 60)
            
            # 4. Generar cortes basados en temas - NUEVO con temas
            cuts_result = self._get_or_create_cuts(video_path, topics_result, transcription_data, video_info, progress_callback)
            
            if progress_callback:
                progress_callback("Procesamiento completado", 100)
            
            # Extract cuts list from result
            cuts = cuts_result.get('cuts', [])
            
            # Cache the final result for future use
            self.cache_manager.save_cuts(video_path, cuts_result)
            
            print(f"✅ CutsProcessor: Generated {len(cuts)} cuts successfully")
            return cuts
            
        except Exception as e:
            error_msg = f"Error in CutsProcessor: {str(e)}"
            print(f"❌ CutsProcessor: {error_msg}")
            if progress_callback:
                progress_callback(f"Error: {error_msg}", -1)
            raise
    
    def _get_or_create_transcription(self, 
                                   video_path: str, 
                                   video_info: Dict,
                                   progress_callback: Optional[Callable] = None) -> Dict:
        """
        Get transcription from cache or create new one
        
        Args:
            video_path: Path to the video file
            video_info: Video metadata
            progress_callback: Optional progress callback
            
        Returns:
            Transcription data
        """
        print(f"🎙️ CutsProcessor: Getting transcription...")
        
        # Check cache first
        if self.cache_manager.has_transcription_cache(video_path):
            cached_data = self.cache_manager.load_transcription(video_path)
            if cached_data:
                transcription_data, cached_video_info = cached_data
                print(f"📂 CutsProcessor: Using cached transcription")
                return transcription_data
        
        # If no cache, we need to generate transcription
        # For now, this would require integration with whisper transcriber
        # This is where we would call the transcription logic
        print(f"⚠️ CutsProcessor: No transcription cache found - would need to generate")
        raise Exception("Transcription generation not yet implemented in CutsProcessor. Use LLMCutsProcessor for full pipeline.")
    
    def _get_or_create_topics(self, 
                             video_path: str,
                             transcription_data: Dict, 
                             video_info: Dict,
                             progress_callback: Optional[Callable] = None) -> Dict:
        """
        Get topics from cache or generate new ones
        
        Args:
            video_path: Path to the video file
            transcription_data: Full transcription with timestamps
            video_info: Video metadata
            progress_callback: Optional progress callback
            
        Returns:
            Topics analysis result
        """
        print(f"🎯 CutsProcessor: Phase 1 - Topics Analysis...")
        
        # Check cache first
        if self.cache_manager.has_topics_cache(video_path):
            cached_topics = self.cache_manager.load_topics(video_path)
            if cached_topics:
                print(f"🎯 CutsProcessor: Using cached topics analysis")
                return cached_topics
        
        # Generate new topics analysis
        print(f"🎯 CutsProcessor: Generating new topics analysis...")
        
        if progress_callback:
            progress_callback("Analizando contenido temático...", 10)
        
        # Build topics prompt
        topics_prompt = self.prompt_loader.build_topics_prompt(transcription_data, video_info)
        
        if progress_callback:
            progress_callback("Enviando transcripción para análisis temático...", 20)
        
        # Call LLM for topics analysis
        topics_response = self.llm_processor.process(topics_prompt, response_type="json")
        
        # Parse topics response
        topics_result = self._parse_json_response(topics_response, "topics")
        
        # Cache the result
        processing_info = {
            "phase": "topics_analysis",
            "timestamp": time.time(),
            "model_used": "unknown"  # Could be enhanced to track which model was used
        }
        self.cache_manager.save_topics(video_path, topics_result, processing_info)
        
        total_topics = topics_result.get('summary', {}).get('total_topics', 0)
        print(f"✅ CutsProcessor: Generated {total_topics} topics")
        return topics_result
    
    def _get_or_create_cuts(self, 
                           video_path: str,
                           topics_result: Dict,
                           transcription_data: Dict, 
                           video_info: Dict,
                           progress_callback: Optional[Callable] = None) -> Dict:
        """
        Get cuts from cache or generate new ones based on topics
        
        Args:
            video_path: Path to the video file
            topics_result: Topics analysis result
            transcription_data: Full transcription with timestamps
            video_info: Video metadata
            progress_callback: Optional progress callback
            
        Returns:
            Cuts analysis result
        """
        print(f"✂️ CutsProcessor: Phase 2 - Cuts Generation...")
        
        # Note: For cuts, we could use cache but since it depends on both topics and transcription,
        # we might want to regenerate it each time or use a more complex cache key.
        # For now, let's generate fresh cuts each time to ensure consistency with topics.
        
        if progress_callback:
            progress_callback("Generando cortes precisos...", 60)
        
        # Build cuts prompt
        cuts_prompt = self.prompt_loader.build_cuts_prompt(topics_result, transcription_data, video_info)
        
        if progress_callback:
            progress_callback("Enviando datos para generar cortes...", 70)
        
        # Call LLM for cuts generation
        cuts_response = self.llm_processor.process(cuts_prompt, response_type="json")
        
        # Parse cuts response
        cuts_result = self._parse_json_response(cuts_response, "cuts")
        
        # Validate and filter cuts
        validated_cuts = self._validate_and_filter_cuts(cuts_result.get('cuts', []))
        cuts_result['cuts'] = validated_cuts
        
        # Update summary
        if 'summary' in cuts_result:
            cuts_result['summary']['total_cuts'] = len(validated_cuts)
        
        total_cuts = len(validated_cuts)
        print(f"✅ CutsProcessor: Generated {total_cuts} validated cuts")
        return cuts_result
    
    def _parse_json_response(self, response: str, expected_type: str) -> Dict:
        """
        Parse JSON response from LLM
        
        Args:
            response: Raw response from LLM
            expected_type: Expected type for validation ("topics" or "cuts")
            
        Returns:
            Parsed JSON data
        """
        try:
            # Clean up response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            
            # Basic validation
            if expected_type == "topics":
                if 'topics' not in data:
                    raise ValueError("Response missing 'topics' field")
            elif expected_type == "cuts":
                if 'cuts' not in data:
                    raise ValueError("Response missing 'cuts' field")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"❌ Response content: {response[:500]}...")
            raise Exception(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            raise
    
    def _validate_and_filter_cuts(self, cuts: List[Dict]) -> List[Dict]:
        """
        Validate and filter cuts based on quality criteria
        
        Args:
            cuts: List of cuts from LLM
            
        Returns:
            Filtered and validated cuts
        """
        valid_cuts = []
        
        for i, cut in enumerate(cuts):
            try:
                # Basic validation
                if not all(key in cut for key in ['start', 'end', 'title']):
                    print(f"⚠️ Cut {i+1} missing required fields, skipping")
                    continue
                
                # Parse timestamps
                start_seconds = self._parse_timestamp(cut['start'])
                end_seconds = self._parse_timestamp(cut['end'])
                
                # Validate duration
                duration = end_seconds - start_seconds
                if duration < self.min_cut_duration:
                    print(f"⚠️ Cut {i+1} too short ({duration:.1f}s), skipping")
                    continue
                
                if start_seconds >= end_seconds:
                    print(f"⚠️ Cut {i+1} has invalid time range, skipping")
                    continue
                
                # Add calculated duration
                cut['duration_seconds'] = duration
                
                valid_cuts.append(cut)
                
            except Exception as e:
                print(f"⚠️ Error validating cut {i+1}: {e}, skipping")
                continue
        
        # Sort by start time
        valid_cuts.sort(key=lambda x: self._parse_timestamp(x['start']))
        
        # Limit number of cuts if configured
        if len(valid_cuts) > self.max_cuts:
            print(f"⚠️ Too many cuts ({len(valid_cuts)}), limiting to {self.max_cuts}")
            valid_cuts = valid_cuts[:self.max_cuts]
        
        return valid_cuts
    
    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Parse timestamp string to seconds
        
        Args:
            timestamp: Timestamp string (HH:MM:SS or MM:SS)
            
        Returns:
            Timestamp in seconds
        """
        try:
            parts = timestamp.split(':')
            if len(parts) == 3:
                # HH:MM:SS
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
            else:
                raise ValueError(f"Invalid timestamp format: {timestamp}")
        except Exception as e:
            raise ValueError(f"Cannot parse timestamp '{timestamp}': {e}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to HH:MM:SS timestamp
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
