#!/usr/bin/env python3
"""
Test script para validar la implementación híbrida de Whisper
Prueba tanto Whisper estándar como Faster-Whisper
"""

import os
import sys
import tempfile
import numpy as np
import subprocess
from openai import OpenAI

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.whisper_transcriber import WhisperTranscriber


def create_test_audio():
    """Crear un archivo de audio de prueba simple"""
    try:
        # Crear un archivo de audio de prueba usando ffmpeg
        test_audio_path = os.path.join(tempfile.gettempdir(), 'test_audio.wav')
        
        # Generar 5 segundos de tono de prueba
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=5',
            '-ar', '16000',
            '-ac', '1',
            test_audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Audio de prueba creado: {test_audio_path}")
            return test_audio_path
        else:
            print(f"❌ Error creando audio de prueba: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creando audio de prueba: {e}")
        return None


def test_whisper_implementation(use_faster_whisper: bool):
    """Probar una implementación específica de Whisper"""
    impl_name = "Faster-Whisper" if use_faster_whisper else "Standard Whisper"
    print(f"\n🧪 Probando {impl_name}...")
    
    # Configurar variables de entorno temporalmente
    original_faster = os.environ.get('USE_FASTER_WHISPER')
    original_model = os.environ.get('WHISPER_MODEL')
    
    try:
        # Configurar para la prueba
        os.environ['USE_FASTER_WHISPER'] = 'true' if use_faster_whisper else 'false'
        os.environ['WHISPER_MODEL'] = 'base'  # Usar modelo pequeño para pruebas rápidas
        
        # Crear cliente OpenAI mock (no lo usaremos para esta prueba)
        client = OpenAI(api_key="test-key")  # API key ficticia
        
        # Inicializar transcriptor
        transcriber = WhisperTranscriber(client)
        
        # Verificar configuración
        expected_impl = use_faster_whisper
        actual_impl = transcriber.use_faster_whisper
        
        if actual_impl == expected_impl:
            print(f"✅ {impl_name}: Configuración correcta")
        else:
            print(f"⚠️ {impl_name}: Configuración incorrecta (esperado: {expected_impl}, actual: {actual_impl})")
            return False
        
        # Crear audio de prueba
        test_audio = create_test_audio()
        if not test_audio:
            print(f"❌ {impl_name}: No se pudo crear audio de prueba")
            return False
        
        try:
            # Probar transcripción local
            print(f"🎙️ {impl_name}: Iniciando transcripción de prueba...")
            result = transcriber._transcribe_local(test_audio)
            
            if result and 'text' in result:
                print(f"✅ {impl_name}: Transcripción exitosa")
                print(f"📝 {impl_name}: Texto: '{result['text'][:50]}...'")
                print(f"📊 {impl_name}: Segmentos: {len(result.get('segments', []))}")
                return True
            else:
                print(f"❌ {impl_name}: Resultado de transcripción inválido")
                return False
                
        except Exception as e:
            print(f"❌ {impl_name}: Error durante transcripción: {e}")
            return False
        
        finally:
            # Limpiar
            transcriber.cleanup()
            if test_audio and os.path.exists(test_audio):
                os.remove(test_audio)
        
    finally:
        # Restaurar variables de entorno
        if original_faster is not None:
            os.environ['USE_FASTER_WHISPER'] = original_faster
        elif 'USE_FASTER_WHISPER' in os.environ:
            del os.environ['USE_FASTER_WHISPER']
            
        if original_model is not None:
            os.environ['WHISPER_MODEL'] = original_model
        elif 'WHISPER_MODEL' in os.environ:
            del os.environ['WHISPER_MODEL']


def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas de implementación híbrida de Whisper")
    print("=" * 60)
    
    # Verificar dependencias
    print("🔍 Verificando dependencias...")
    
    try:
        import whisper
        print("✅ Whisper estándar: Disponible")
    except ImportError:
        print("❌ Whisper estándar: No disponible")
        return False
    
    try:
        import faster_whisper
        print("✅ Faster-Whisper: Disponible")
        faster_available = True
    except ImportError:
        print("⚠️ Faster-Whisper: No disponible")
        faster_available = False
    
    try:
        import torch
        print(f"✅ PyTorch: Disponible (versión {torch.__version__})")
    except ImportError:
        print("❌ PyTorch: No disponible")
        return False
    
    # Probar ambas implementaciones
    success_count = 0
    total_tests = 2 if faster_available else 1
    
    # Probar Whisper estándar
    if test_whisper_implementation(use_faster_whisper=False):
        success_count += 1
    
    # Probar Faster-Whisper si está disponible
    if faster_available:
        if test_whisper_implementation(use_faster_whisper=True):
            success_count += 1
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print(f"✅ Pruebas exitosas: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 ¡Todas las pruebas pasaron! La implementación híbrida está funcionando correctamente.")
        print("\n💡 Para usar en producción:")
        print("   USE_FASTER_WHISPER=true   # Usar Faster-Whisper (recomendado)")
        print("   WHISPER_MODEL=large-v3    # Usar modelo large-v3 (mejor calidad)")
        return True
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores anteriores.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
