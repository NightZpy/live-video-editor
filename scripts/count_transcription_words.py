import sys
import json
from pathlib import Path

def count_words_and_chars(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Try to find the main text field
    text = None
    if 'transcription' in data and 'text' in data['transcription']:
        text = data['transcription']['text']
    elif 'text' in data:
        text = data['text']
    else:
        print(f"No text found in {file_path}")
        return
    words = text.split()
    print(f"{file_path}: {len(words)} words, {len(text)} characters")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_transcription_words.py <file1.json> [file2.json ...]")
        sys.exit(1)
    for file in sys.argv[1:]:
        count_words_and_chars(file)
