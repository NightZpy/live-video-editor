# Python Project General Coding Rules

This document contains general-purpose coding standards and best practices for Python projects. These rules are applicable to any Python codebase, regardless of domain or framework.

- **Language**: All code comments and documentation (including docstrings) must be written in English. Do not use Spanish or any other language for code documentation.
- **File Handling**: Prefer `pathlib.Path` over `os.path` for file management.
- **Data Structures**: Use list/dict comprehensions for concise, readable code.
- **Data Containers**: Use `dataclasses` to reduce boilerplate for structured data.
- **Composition Over Inheritance**: Prefer composition over inheritance. Avoid deep or complex inheritance hierarchies.
- **Duck Typing & Interfaces**: Prefer duck typing and simple interface-based design (as in Go) over abstract base classes and inheritance. Minimize unnecessary abstraction and boilerplate.
- **Function Arguments**: Avoid mutable default arguments.
- **File Length**: Code files should not exceed 500 lines where possible. Split large files into smaller, focused modules.
- **Function Length**: Keep functions short (< 50 lines) and focused on local behavior.
- **Naming**: Use `snake_case` for variables/functions, `PascalCase` for classes, and `snake_case` for files/folders.
- **Imports**: Sort imports with ruff (stdlib, third-party, local).
- **Formatting**: Use Black-compatible formatting via `ruff format`.
- **Linting**: Use `ruff` for style and error checking (enforces PEP 8).
- **Type Checking**: Use VS Code with Pylance for static type checking.
- **Documentation**: Use Google-style docstrings for all modules, classes, and functions.
- **Project Layout**: Organize all source code inside a `src/` folder at the workspace root. This includes the main entry point script (e.g., `main.py` or `app.py`). Do not place source files or the main script at the workspace root.

  Non-code folders such as `resources/`, `assets/`, `data/`, `docs/`, and `tests/`, as well as configuration files (e.g., `.env`, `.env.example`, `requirements.txt`, `pyproject.toml`), must be placed at the workspace root, not inside `src/`.

## Error Handling & Debugging
- **Error Handling**: Use specific exceptions with context messages and proper logging.
- **Debugging**: Use the `logging` module for observability (prefer JSON-structured logs for production). Use `print` only for short, temporary debug output or quick tests.

## Configuration & Security
- **Configuration**: Use environment variables (via `python-dotenv`) for all configuration.
- **Security**: Never store or log AWS credentials or API keys. Set command timeouts where applicable. Add sensitive data folders/files (e.g., token/api key files) to `.gitignore`.


## Environment & Dependency Management
- **Virtual Environment Location**: The virtual environment must be located at `.venv/` in the workspace root (e.g., `workspace_root/.venv`). Do not place it inside `src/` or any subfolder.
- **Creating the Virtual Environment**: If `.venv/` does not exist, create it from the workspace root with:
  - `python -m venv .venv`
- **Activating the Virtual Environment**: Always activate the virtual environment before installing packages or running scripts. On macOS/Linux:
  - `source .venv/bin/activate`
  On Windows:
  - `.venv\Scripts\activate`
- **Installing Packages**: With the virtual environment activated, install packages using `pip install package_name`, then update the appropriate requirements file.
- **Running Scripts**: Always run scripts from the workspace root, even though the entry point script (e.g., `main.py` or `app.py`) is located inside the `src/` folder. Use a single command to activate the virtual environment and execute the script. For example (macOS/Linux):
  - `source .venv/bin/activate && python src/main.py`
  On Windows:
  - `.venv\Scripts\activate && python src/main.py`
  This ensures scripts never fail due to the wrong environment or import issues.


## Testing
- Avoid creating loose or ad-hoc test scripts just to try out features. If you must create a temporary test script, delete it after use.
- Prioritize organized tests following the testing pyramid: first unit tests, then integration, and finally end-to-end tests.
- Use pytest as the main testing framework.
- Organize tests in a `tests/` folder at the project root, with subfolders for each feature or module (`tests/feature_x/`, etc.).
- Within each subfolder, separate tests by type: unit, integration, component, use cases, etc.
- Prefer adding new tests to the existing structure rather than creating standalone scripts.
- Temporary test files must be deleted after use.


## Version Control & Commits
- After adding any new feature, fix, or minimal implementation, you must create a commit to checkpoint your work. This helps prevent breaking the application with uncommitted changes.
- Commit messages must be clear, concise, and written in English, describing what was added or fixed.
- Always use a single command to stage and commit: `git add . && git commit -m "your message"` (never split into multiple agent calls).

## Extensibility
New features or modules should be added as new files/components, not by modifying core logic directly.

---

# Copilot Instructions for Live Video Editor (CURRENT PROJECT)

## Project Overview
- **Live Video Editor** is a Python desktop app for segmenting and editing videos using AI (OpenAI/Whisper/LLM) and a modern UI (CustomTkinter).
- The architecture is modular: `src/core` (processing, AI, audio/video), `src/ui` (Tkinter UI, components), `src/utils` (helpers, cache, video/audio utils).
- Data flows: User loads video → audio is extracted (FFmpeg) → transcribed (Whisper/Faster-Whisper) → transcript analyzed by LLM (OpenAI GPT-4, etc.) → JSON cuts generated → UI updates.

## Key Components
- `src/core/llm_cuts_processor.py`: Orchestrates the full pipeline (audio extraction, transcription, LLM analysis, validation, JSON output).
- `src/core/whisper_transcriber.py`: Handles both Whisper and Faster-Whisper, with auto-fallback and progress callbacks.
- `src/core/cuts_processor.py`: Newer two-phase cut analysis logic.
- `src/ui/components/`: UI widgets (video loader, cuts list, timeline, progress dialogs, etc.).
- `src/utils/`: Caching, file, and video/audio utilities.

## Developer Workflows
- **Install**: Use the right requirements file for your OS/GPU (see `INSTALL.md`). For AMD GPUs, follow the special ROCm/PyTorch steps.
- **Run**: `python main.py` (after activating your virtualenv and setting up `.env`).
- **Test**: `python test_faster_whisper_progress.py` and `python test_whisper_integration.py` for audio/AI pipeline validation.
- **Environment**: Configure `.env` (see `ENV_SETUP.md`). `OPENAI_API_KEY` is required. Optional: `DEFAULT_MODEL`, `MAX_COMPLETION_TOKENS`, `USE_FASTER_WHISPER`, `WHISPER_MODEL`.
- **Debugging**: Progress and errors are printed to console. Progress callbacks update the UI in real time.

## Project-Specific Patterns
- **AI/LLM Fallback**: If the preferred model fails, the system auto-tries fallback models (see `llm_cuts_processor.py`).
- **Transcription**: Both Whisper and Faster-Whisper are supported. Use `USE_FASTER_WHISPER` in `.env` to switch. Progress is real-time and based on audio duration.
- **Manual & AI Cuts**: Both manual and AI-generated cuts use the same JSON format. The UI and export logic are agnostic to the source.
- **UI/Backend Sync**: All cut edits (manual or AI) are reflected in the UI and persisted to cache.
- **Component Communication**: UI components communicate via callbacks and shared state (see `main_window.py`, `components/`).

## Integration Points

## Transcription

### AssemblyAI Transcription Service

AssemblyAI provides a robust API and Python SDK for audio transcription, supporting both batch (pre-recorded files) and real-time streaming. Below are essential usage patterns and code examples for integration:

#### Installation

```bash
pip install assemblyai
```

#### Basic Batch Transcription (Pre-recorded Audio)

```python
import assemblyai as aai

aai.settings.api_key = "<YOUR_API_KEY>"
transcriber = aai.Transcriber()

# Local file or public URL
audio_file = "./example.mp3"  # or a URL

# Optional: configure model/granularity
config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.slam_1)
transcript = transcriber.transcribe(audio_file, config=config)

if transcript.status == aai.TranscriptStatus.error:
    print(f"Transcription failed: {transcript.error}")
    exit(1)

print(transcript.text)  # Full transcript
```

#### Streaming Transcription (Real-Time)

```python
import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient, StreamingClientOptions, StreamingEvents, StreamingParameters
)

api_key = "<YOUR_API_KEY>"

def on_begin(self, event):
    print(f"Session started: {event.id}")

def on_turn(self, event):
    print(f"{event.transcript} ({event.end_of_turn})")

def on_terminated(self, event):
    print(f"Session terminated: {event.audio_duration_seconds} seconds of audio processed")

def on_error(self, error):
    print(f"Error occurred: {error}")

client = StreamingClient(
    StreamingClientOptions(api_key=api_key, api_host="streaming.assemblyai.com")
)
client.on(StreamingEvents.Begin, on_begin)
client.on(StreamingEvents.Turn, on_turn)
client.on(StreamingEvents.Termination, on_terminated)
client.on(StreamingEvents.Error, on_error)

client.connect(StreamingParameters(sample_rate=16000, format_turns=True))
try:
    client.stream(aai.extras.MicrophoneStream(sample_rate=16000))
finally:
    client.disconnect(terminate=True)
```

#### Granularity Options

You can control the output granularity for both batch and streaming transcriptions:

**Batch (pre-recorded files):**
- By default, the transcript object includes:
  - `transcript.text`: Full transcript as plain text.
  - `transcript.words`: List of words with timestamps.
  - `transcript.utterances`: List of utterances (speaker turns) with text and timestamps.

Example: Accessing words and utterances in batch mode
```python
# Access word-level details
for word in transcript.words:
    print(word.text, word.start, word.end)

# Access utterance-level details
for utt in transcript.utterances:
    print(utt.speaker, utt.text, utt.start, utt.end)
```

**Streaming:**
- Use `format_turns=True` in `StreamingParameters` to receive formatted output by turns.
```python
client.connect(StreamingParameters(sample_rate=16000, format_turns=True))
```
In the `on_turn` event, you receive each turn's transcript, which can be accumulated or processed in real time.

**Advanced:**
- You can further customize output using `TranscriptionConfig` (for batch) and `StreamingSessionParameters` (for streaming) to control language, formatting, and more. See the SDK documentation for all options.

#### Saving and Analyzing Transcriptions

- The `transcript.text` property contains the full transcript (batch mode).
- For streaming, accumulate `event.transcript` outputs.
- Save to file:
  ```python
  with open("output.txt", "w") as f:
      f.write(transcript.text)
  ```

#### Batch Transcription of Multiple Files

- See [Batch Transcription Guide](https://www.assemblyai.com/docs/guides/batch_transcription) for processing multiple files in parallel.

#### LLM Analysis (LeMUR)

You can apply LLMs to transcripts for summarization, Q&A, and more. LeMUR supports several Anthropic Claude models via the `final_model` parameter in `aai.LemurModel`:

- `aai.LemurModel.claude_sonnet_4_20250514` (Claude 4 Sonnet)
- `aai.LemurModel.claude_opus_4_20250514` (Claude 4 Opus)
- `aai.LemurModel.claude3_7_sonnet_20250219` (Claude 3.7 Sonnet)
- `aai.LemurModel.claude3_5_sonnet` (Claude 3.5 Sonnet)
- `aai.LemurModel.claude3_5_haiku_20241022` (Claude 3.5 Haiku)
- `aai.LemurModel.claude3_opus` (Claude 3.0 Opus, legacy)
- `aai.LemurModel.claude3_haiku` (Claude 3.0 Haiku, legacy)
- `aai.LemurModel.claude3_sonnet` (Claude 3.0 Sonnet, legacy)

Example with custom parameters:
```python
result = transcript.lemur.task(
    prompt,
    final_model=aai.LemurModel.claude_sonnet_4_20250514,  # Select model
    max_output_size=1000,  # Optional: max tokens
    temperature=0.7        # Optional: creativity
)
print(result.response)
```
See the documentation for model details and regional availability.

#### Example: Segmenting by Paragraphs (Chapter Summaries)

```python
import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"
transcriber = aai.Transcriber()

# Transcribe audio (local file or URL)
transcript = transcriber.transcribe(
    "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
)

# Get paragraphs and group them
paragraphs = transcript.get_paragraphs()
combined_paragraphs = []
step = 2  # Adjust group size as needed
for i in range(0, len(paragraphs), step):
    paragraph_group = paragraphs[i : i + step]
    start = paragraph_group[0].start
    end = paragraph_group[-1].end
    text = " ".join([p.text for p in paragraph_group])
    combined_paragraphs.append(f"Paragraph: {text} Start: {start} End: {end}")

# Summarize each group with LeMUR
results = []
for paragraph in combined_paragraphs:
    result = aai.Lemur().task(
        prompt="Summarize this text as a whole and provide start and end timestamps.",
        input_text=paragraph,
        final_model=aai.LemurModel.claude3_5_sonnet,
    )
    results.append(result.response)

for result in results:
    print(result)
```

#### Example: Segmenting by Topics (Thematic Segmentation)

```python
import assemblyai as aai

aai.settings.api_key = "YOUR_API_KEY"
transcriber = aai.Transcriber()
transcript = transcriber.transcribe("./example.mp3")

prompt = (
    "Segment this transcript into topics. For each topic, provide: "
    "a title, a brief description, and the start and end timestamps. "
    "Return the result as a JSON list."
)

result = transcript.lemur.task(
    prompt,
    final_model=aai.LemurModel.claude3_7_sonnet_20250219
)
print(result.response)
```

// The output will be a list of topics with their titles, descriptions, and timestamps, suitable for cuts or chapters in your app.

#### References

- [AssemblyAI Python SDK Docs](https://www.assemblyai.com/docs/getting-started/transcribe-an-audio-file)
- [Streaming Transcription](https://www.assemblyai.com/docs/getting-started/transcribe-streaming-audio)
- [Batch Transcription](https://www.assemblyai.com/docs/guides/batch_transcription)
- [LeMUR LLM Analysis](https://www.assemblyai.com/docs/lemur/apply-llms-to-audio-files)
- [Cookbooks & Guides](https://www.assemblyai.com/docs/guides)


### Pricing (2025)

AssemblyAI pricing is usage-based and split between transcription and LLM analysis (LeMUR). Each is billed separately.

#### Transcription (Speech-to-Text)

- **Pre-recorded audio (Universal/Slam-1):**
  - $0.27 per hour of audio (lower rates for volume)
- **Streaming audio (Universal-Streaming):**
  - $0.15 per hour of audio (lower rates for volume)

**Example:**
Transcribing a 30-minute audio file with Universal model:
  - 0.5 hours × $0.27 = **$0.135**

#### LLM Analysis (LeMUR)

LLM analysis is billed by tokens processed (input and output) and depends on the Claude model used:

| Model                | Input (per 1k tokens) | Output (per 1k tokens) |
|----------------------|----------------------|------------------------|
| Claude 4 Sonnet      | $0.003               | $0.015                 |
| Claude 4 Opus        | $0.015               | $0.075                 |
| Claude 3.7 Sonnet    | $0.003               | $0.015                 |
| Claude 3.5 Sonnet    | $0.003               | $0.015                 |
| Claude 3.5 Haiku     | $0.0008              | $0.004                 |
| Claude 3 Opus        | $0.015               | $0.075                 |
| Claude 3 Haiku       | $0.00025             | $0.00125               |
| Claude 3 Sonnet      | $0.003               | $0.015                 |

**Example:**
If your transcript and prompt total 2,000 input tokens and the LLM generates 1,000 output tokens using Claude 3.5 Haiku:
  - Input: 2 × $0.0008 = **$0.0016**
  - Output: 1 × $0.004 = **$0.004**
  - **Total LLM cost:** $0.0056

**Note:** 1,000 tokens ≈ 750 words. Both transcription and LLM analysis are charged separately and summed for the total cost.

For up-to-date pricing and volume discounts, see: https://www.assemblyai.com/pricing
