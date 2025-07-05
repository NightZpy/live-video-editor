#!/usr/bin/env python3
"""
Test script for Faster-Whisper progress tracking
Tests the new real-time progress reporting functionality
"""

import os
import sys
import time
from typing import Dict, Any

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.whisper_transcriber import WhisperTranscriber

class MockOpenAIClient:
    """Mock OpenAI client for testing"""
    pass

def test_progress_callback(stage: str, progress: float, message: str):
    """
    Test progress callback to monitor Faster-Whisper progress
    
    Args:
        stage: Current processing stage
        progress: Progress percentage (0-100)
        message: Progress message
    """
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {stage}: {progress:.1f}% - {message}")

def main():
    """Test Faster-Whisper progress tracking"""
    print("🧪 Testing Faster-Whisper Progress Tracking")
    print("=" * 50)
    
    # Set environment variables to use Faster-Whisper
    os.environ['USE_FASTER_WHISPER'] = 'true'
    os.environ['WHISPER_MODEL'] = 'small'  # Use small model for faster testing
    
    # Initialize transcriber
    mock_client = MockOpenAIClient()
    transcriber = WhisperTranscriber(mock_client)
    
    print(f"\n🔧 Configuration:")
    print(f"   - Using Faster-Whisper: {transcriber.use_faster_whisper}")
    print(f"   - Preferred model: {transcriber.preferred_model}")
    print(f"   - Device: {transcriber.device}")
    
    # Check if we have any test audio files
    test_audio_paths = [
        "test_audio.wav",
        "test_audio.mp3",
        "sample_audio.wav",
        "sample_audio.mp3"
    ]
    
    audio_path = None
    for path in test_audio_paths:
        if os.path.exists(path):
            audio_path = path
            break
    
    if not audio_path:
        print(f"\n⚠️ No test audio file found. Tested paths:")
        for path in test_audio_paths:
            print(f"   - {path}")
        print(f"\n💡 To test properly, place a test audio file in the project root")
        print(f"💡 You can use any .wav or .mp3 file for testing")
        return
    
    print(f"\n🎙️ Found test audio: {audio_path}")
    
    try:
        # Test transcription with progress tracking
        print(f"\n🚀 Starting transcription with progress tracking...")
        print(f"🔍 Watch for real-time progress updates below:")
        print(f"-" * 30)
        
        result = transcriber.transcribe(audio_path, progress_callback=test_progress_callback)
        
        print(f"-" * 30)
        print(f"✅ Transcription completed successfully!")
        
        # Display results summary
        text = result.get('text', '')
        segments = result.get('segments', [])
        
        print(f"\n📊 Results Summary:")
        print(f"   - Text length: {len(text)} characters")
        print(f"   - Number of segments: {len(segments)}")
        print(f"   - Language: {result.get('language', 'unknown')}")
        
        if segments:
            total_duration = segments[-1].get('end', 0) if segments else 0
            print(f"   - Total duration: {total_duration:.1f} seconds")
            
            print(f"\n📝 First few segments:")
            for i, segment in enumerate(segments[:3]):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                print(f"   [{start:.1f}s-{end:.1f}s]: {text}")
        
        if text:
            print(f"\n📝 Full transcription (first 200 chars):")
            print(f"   {text[:200]}{'...' if len(text) > 200 else ''}")
    
    except Exception as e:
        print(f"\n❌ Transcription failed: {str(e)}")
        print(f"💡 This might be expected if Faster-Whisper is not installed")
        print(f"💡 Install with: pip install faster-whisper")
    
    finally:
        # Cleanup
        try:
            transcriber.cleanup()
            print(f"\n🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {str(e)}")

if __name__ == "__main__":
    main()
