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
- **AI Analysis**: Triggered from UI (`CutTimesInputComponent`), handled by `LLMCutsProcessor`, results passed back to UI via callback.
- **Progress**: All long-running tasks use progress callbacks to update the UI (see `llm_progress_dialog.py`).
- **Cache**: Transcriptions and cuts are cached for fast reloads and recovery.


## Coding Standards & Conventions

General-purpose Python coding rules have been moved to `.github/RULES.md`.

This file now contains only project-specific conventions and integration points. For any unclear or missing conventions, review `plan.md`, the `docs/` folder, or `.github/RULES.md` for up-to-date project decisions.
