# General Python rules for projects are in `.github/RULES.md`. This file contains only project-specific conventions and integration points.
# Copilot Instructions for Live Video Editor

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
- **AI Analysis**: Triggered from UI (`CutTimesInputComponent`), handled by `LLMCutsProcessor`, results passed back to UI via callback.
- **Progress**: All long-running tasks use progress callbacks to update the UI (see `llm_progress_dialog.py`).
- **Cache**: Transcriptions and cuts are cached for fast reloads and recovery.


## Coding Standards & Conventions

General-purpose Python coding rules have been moved to `.github/RULES.md`.

This file now contains only project-specific conventions and integration points. For any unclear or missing conventions, review `plan.md`, the `docs/` folder, or `.github/RULES.md` for up-to-date project decisions.
