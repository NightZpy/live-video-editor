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

For project-specific conventions, see the main Copilot instructions or project documentation.
