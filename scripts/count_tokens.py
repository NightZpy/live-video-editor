
"""
count_tokens.py

Counts the number of tokens in a transcription JSON file using OpenAI's tiktoken library.

Purpose:
    - Accurately estimate the number of tokens that would be processed by an LLM (e.g., GPT, Claude, LeMUR) for cost calculation or quota management.
    - This is more precise than counting words or characters, as LLMs bill by tokens.

Usage:
    python scripts/count_tokens.py <file.json>

    - <file.json> must be a JSON file with the structure:
        {
            "transcription": {
                "text": "...your transcript here..."
            }
        }
    - The script prints the number of tokens in the 'transcription.text' field.
    - Requires tiktoken to be installed globally or in your virtual environment.

Example:
    python scripts/count_tokens.py data/transcriptions/2025-03-26-113723474.json
"""
import sys
import json
import tiktoken
from pathlib import Path

def count_tokens(text, model_name="gpt-3.5-turbo"):
    enc = tiktoken.encoding_for_model(model_name)
    return len(enc.encode(text))

def main():
    if len(sys.argv) < 2:
        print("Usage: python count_tokens.py <file.json>")
        sys.exit(1)
    file_path = sys.argv[1]
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    text = data.get('transcription', {}).get('text', '')
    if not text:
        print("No transcription text found.")
        sys.exit(1)
    tokens = count_tokens(text)
    print(f"{file_path}: {tokens} tokens (input only)")

if __name__ == "__main__":
    main()
