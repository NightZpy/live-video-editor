"""
Prompt Loader for managing and processing prompt templates
"""

import os
import json
from typing import Dict, Any, Optional


class PromptLoader:
    """
    Handles loading and processing prompt templates for the two-phase analysis
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the prompt loader
        
        Args:
            prompts_dir: Directory containing prompt templates (optional)
        """
        if prompts_dir:
            self.prompts_dir = prompts_dir
        else:
            # Default to prompts directory in the same folder as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.prompts_dir = os.path.join(current_dir, "prompts")
        
        print(f"📝 PromptLoader: Using prompts directory: {self.prompts_dir}")
        
        # Create prompts directory if it doesn't exist
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # Load prompt templates
        self._load_templates()
    
    def _load_templates(self):
        """Load prompt templates from files or create defaults"""
        # Topics prompt template
        self.topics_template = self._load_or_create_topics_template()
        
        # Cuts prompt template  
        self.cuts_template = self._load_or_create_cuts_template()
        
        print(f"✅ PromptLoader: Templates loaded successfully")
    
    def _load_or_create_topics_template(self) -> str:
        """Load or create the topics analysis prompt template"""
        template_path = os.path.join(self.prompts_dir, "topics_analysis.txt")
        
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📝 PromptLoader: Loaded topics template from {template_path}")
                return content
            except Exception as e:
                print(f"⚠️ PromptLoader: Failed to load topics template: {e}")
          # Create default template
        default_template = """Eres un analista profesional de contenido de video. Tu tarea es analizar la transcripción de un video e identificar TODOS los temas y temáticas principales discutidos.

🎬 INFORMACIÓN DEL VIDEO:
- Archivo: {filename}
- Duración: {duration}

📝 TRANSCRIPCIÓN (enfócate en el contenido, ignora los timestamps por ahora):
{transcript_text}

🧠 **TAREA DE ANÁLISIS DE CONTENIDO**

**Tu Objetivo**: Identificar CADA tema significativo, temática y punto de discusión en este video.

**Paso 1: Leer y Entender**
- Lee toda la transcripción cuidadosamente
- Comprende el flujo general y la estructura
- Identifica los temas principales y sub-temas

**Paso 2: Identificación de Temas**
Crea una lista comprensiva de TODOS los temas discutidos:

- **TEMAS PRINCIPALES** (temas que abarcan tiempo significativo de discusión)
- **SUB-TEMAS** dentro de cada tema principal
- **CONCEPTOS CLAVE** y principios explicados
- **HISTORIAS/EJEMPLOS** (narrativas completas y anécdotas)
- **INSIGHTS ACCIONABLES** (consejos, recomendaciones)
- **EXPLICACIONES TÉCNICAS** (contenido instructivo, procesos)
- **DISCUSIONES FILOSÓFICAS** (pensamientos profundos, reflexiones)
- **CITAS IMPORTANTES** (declaraciones memorables, insights clave)

**Paso 3: Organización de Temas**
Organiza los temas por:
- **Tipo de Contenido**: Educativo, Entretenimiento, Historia, Insight, etc.
- **Nivel de Importancia**: Crítico, Importante, Interesante, Suplementario
- **Duración Estimada**: Cuánto tiempo de discusión probablemente toma cada tema
- **Relaciones**: Cómo se conectan los temas entre sí

🎯 **FORMATO DE RESPUESTA**:
Devuelve un objeto JSON con esta estructura:

{{
  "topics": [
    {{
      "id": 1,
      "title": "Título claro y descriptivo del tema en español",
      "description": "Descripción detallada en español de lo que cubre este tema",
      "content_type": "major_theme|sub_topic|concept|story|insight|technical|philosophical|quote",
      "importance_level": "critical|important|interesting|supplementary",
      "estimated_duration": "long|medium|short",
      "keywords": ["palabra_clave1", "palabra_clave2", "palabra_clave3"],
      "related_topics": [2, 3]
    }}
  ],
  "summary": {{
    "total_topics": 0,
    "major_themes": 0,
    "key_insights": 0,
    "stories_examples": 0,
    "recommended_focus": "Descripción del contenido más valioso para extraer"
  }}
}}

**REQUISITOS CRÍTICOS**:
- Identifica TODO el contenido sustancial - no pierdas nada importante
- Enfócate en el valor y completitud del contenido
- Organiza por relaciones lógicas
- Proporciona descripciones claras y precisas en español
- Considera diferentes intereses de audiencia (educación, entretenimiento, inspiración)
- TODOS los títulos, descripciones y palabras clave deben estar en español"""

        # Save default template
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(default_template)
            print(f"📝 PromptLoader: Created default topics template at {template_path}")
        except Exception as e:
            print(f"⚠️ PromptLoader: Failed to save topics template: {e}")
        
        return default_template
    
    def _load_or_create_cuts_template(self) -> str:
        """Load or create the cuts generation prompt template"""
        template_path = os.path.join(self.prompts_dir, "cuts_generation.txt")
        
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📝 PromptLoader: Loaded cuts template from {template_path}")
                return content
            except Exception as e:
                print(f"⚠️ PromptLoader: Failed to load cuts template: {e}")
          # Create default template
        default_template = """Eres un editor de video profesional. Tu tarea es crear cortes de video precisos basados en temas identificados y una transcripción con timestamps.

🎬 INFORMACIÓN DEL VIDEO:
- Archivo: {filename}  
- Duración: {duration}

📋 **TEMAS IDENTIFICADOS**:
{topics_json}

📝 **TRANSCRIPCIÓN CON TIMESTAMPS**:
{timestamped_transcript}

🎯 **TAREA DE GENERACIÓN DE CORTES**

**Tu Objetivo**: Crear cortes de video precisos que capturen segmentos de contenido completos y valiosos.

**Paso 1: Mapeo de Temas a Timestamps**
Para cada tema identificado:
- Localiza dónde comienza la discusión del tema en la transcripción
- Encuentra dónde concluye naturalmente la discusión del tema
- Asegúrate de capturar discusiones COMPLETAS de principio a fin
- Busca límites naturales de conversación y transiciones

**Paso 2: Estrategia de Creación de Cortes**
Crea cortes que:
- **CAPTUREN TEMAS COMPLETOS**: Discusiones completas de introducción a conclusión
- **RESPETEN LÍMITES NATURALES**: Inicien y terminen en puntos naturales del habla
- **EVITEN CORTES ABRUPTOS**: Nunca cortes a mitad de oración o explicación
- **INCLUYAN CONTEXTO**: Suficiente contexto para entendimiento independiente
- **OPTIMICEN EL VALOR**: Enfócate en el contenido más valioso y completo

**Paso 3: Tipos de Cortes y Guías de Duración**
- **Discusiones Educativas/Profundas**: 8-45 minutos (la duración natural que requiera el tema)
- **Explicaciones Completas**: 3-15 minutos (explicaciones completas con contexto)
- **Historias/Ejemplos**: 2-8 minutos (narrativas completas)  
- **Insights/Consejos Clave**: 1-4 minutos (pensamientos completos con contexto)
- **Momentos Virales**: 30-90 segundos (highlights impactantes dentro de temas más largos)

**Paso 4: Validación de Calidad**
Para cada corte, verifica:
- ✅ Comienza en un inicio natural (introducción del tema o contexto claro)
- ✅ Termina en una conclusión natural (finalización del tema o transición clara)
- ✅ Contiene valor completo e independiente
- ✅ El título describe exactamente el contenido dentro de esos timestamps exactos
- ✅ La descripción coincide SOLO con lo que pasa en ese rango de tiempo
- ✅ Sin gaps de contenido - cada tema valioso tiene un corte correspondiente

🎯 **FORMATO DE RESPUESTA**:
Devuelve un objeto JSON con esta estructura EXACTA:

{{
  "cuts": [
    {{
      "id": 1,
      "start": "HH:MM:SS",
      "end": "HH:MM:SS",
      "title": "Descripción exacta en español de lo que se discute en este rango de tiempo",
      "description": "Descripción detallada en español de SOLO el contenido dentro de estos timestamps",
      "duration": "HH:MM:SS",
      "content_type": "major_discussion|topic_segment|concept_explanation|key_moment|viral_highlight",
      "source_topic_ids": [1, 2],
      "quality_score": "high|medium|low"
    }}
  ],
  "summary": {{
    "total_cuts": 0,
    "coverage_percentage": 85,
    "avg_cut_duration": "00:05:30",
    "content_distribution": {{
      "major_discussions": 5,
      "topic_segments": 8,
      "concept_explanations": 12,
      "key_moments": 6,
      "viral_highlights": 3
    }}
  }}
}}

🚨 **REQUISITOS ABSOLUTOS**:
- Genera cortes para TODOS los temas valiosos identificados en el análisis de temas
- Prioriza temas COMPLETOS sobre fragmentos parciales
- Crea cortes superpuestos cuando sea beneficioso (educativo + viral del mismo contenido)
- Asegura CERO gaps de contenido - cada tema valioso debe tener un corte
- Mantén perfecta precisión entre timestamps y descripciones
- Para videos largos, espera 15-30+ cortes cubriendo todo el contenido principal
- TODOS los títulos y descripciones deben estar en español

**VALIDACIÓN CRÍTICA**:
- NUNCA crear cortes con tiempos de inicio/fin idénticos (duración cero)
- NUNCA cortar en medio de explicaciones sin contexto apropiado
- NUNCA mezclar información de diferentes segmentos de video en las descripciones
- SIEMPRE verificar que los timestamps coincidan con el contenido actual descrito"""

        # Save default template
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(default_template)
            print(f"📝 PromptLoader: Created default cuts template at {template_path}")
        except Exception as e:
            print(f"⚠️ PromptLoader: Failed to save cuts template: {e}")
        
        return default_template
    
    def build_topics_prompt(self, transcript: Dict, video_info: Dict) -> str:
        """
        Build the topics analysis prompt
        
        Args:
            transcript: Whisper transcription result
            video_info: Video metadata
            
        Returns:
            Complete topics analysis prompt
        """
        # Extract plain text from transcript (without timestamps)
        transcript_text = transcript.get('text', '')
        if not transcript_text and 'segments' in transcript:
            # Build text from segments if main text is not available
            transcript_text = ' '.join([
                segment.get('text', '').strip() 
                for segment in transcript.get('segments', [])
            ])
        
        # Get video info
        filename = os.path.basename(video_info.get('filename', 'video.mp4'))
        duration = video_info.get('duration', 'Unknown')
        
        # Format the prompt
        prompt = self.topics_template.format(
            filename=filename,
            duration=duration,
            transcript_text=transcript_text
        )
        
        print(f"📝 PromptLoader: Built topics prompt, length: {len(prompt)} characters")
        return prompt
    
    def build_cuts_prompt(self, topics_result: Dict, transcript: Dict, video_info: Dict) -> str:
        """
        Build the cuts generation prompt
        
        Args:
            topics_result: Result from topics analysis
            transcript: Whisper transcription result with timestamps
            video_info: Video metadata
            
        Returns:
            Complete cuts generation prompt
        """
        # Build timestamped transcript
        timestamped_transcript = ""
        if 'segments' in transcript:
            for segment in transcript['segments']:
                start_time = self._seconds_to_timestamp(segment.get('start', 0))
                end_time = self._seconds_to_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                timestamped_transcript += f"[{start_time} - {end_time}] {text}\n"
        else:
            # Fallback to full text if segments not available
            timestamped_transcript = transcript.get('text', '')
          # Get video info
        filename = os.path.basename(video_info.get('filename', 'video.mp4'))
        duration = video_info.get('duration', 'Unknown')
        
        # Format topics as clean text instead of verbose JSON
        topics_text = self._format_topics_as_text(topics_result)
        
        # Format the prompt
        prompt = self.cuts_template.format(
            filename=filename,
            duration=duration,
            topics_json=topics_text,
            timestamped_transcript=timestamped_transcript
        )
        
        print(f"📝 PromptLoader: Built cuts prompt, length: {len(prompt)} characters")
        return prompt
    
    def _format_topics_as_text(self, topics_result: Dict) -> str:
        """
        Format topics result as clean, readable text instead of verbose JSON
        
        Args:
            topics_result: Topics analysis result with topics list
            
        Returns:
            Clean formatted text representation of topics
        """
        topics_text = ""
        
        # Extract topics list
        topics_list = topics_result.get('topics', [])
        if not topics_list:
            return "No topics identified."
        
        # Add summary header if available
        summary = topics_result.get('summary', {})
        if summary:
            total_topics = summary.get('total_topics', len(topics_list))
            topics_text += f"TOPICS SUMMARY: {total_topics} topics identified\n\n"
        
        # Format each topic
        for topic in topics_list:
            topic_id = topic.get('id', '?')
            title = topic.get('title', 'Untitled Topic')
            description = topic.get('description', 'No description')
            importance = topic.get('importance_level', 'unknown')
            keywords = topic.get('keywords', [])
            related = topic.get('related_topics', [])
            
            topics_text += f"{topic_id}. {title}\n"
            topics_text += f"   Description: {description}\n"
            topics_text += f"   Importance: {importance}\n"
            
            if keywords:
                keywords_str = ", ".join(keywords)
                topics_text += f"   Keywords: {keywords_str}\n"
            
            if related:
                related_str = ", ".join(map(str, related))
                topics_text += f"   Related: {related_str}\n"
            
            topics_text += "\n"
        
        return topics_text.strip()

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
