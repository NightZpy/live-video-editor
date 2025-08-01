# Live Video Editor

## 1. Overview

Live Video Editor is a powerful, AI-driven desktop application designed to streamline the process of editing long videos into shorter, shareable clips. By leveraging advanced AI for transcription and content analysis, this tool automates the tedious task of finding key moments, allowing content creators to focus on storytelling and producing high-quality content efficiently.

The application is built with Python and uses a combination of local and cloud-based AI models to provide a seamless editing experience.

## 2. Features

- **AI-Powered Cut Detection:** Automatically analyzes video transcripts to identify and suggest meaningful cuts based on topics, stories, and key moments.
- **Manual and Automatic Editing:** Provides a user-friendly interface to review, modify, and create cuts manually or use the AI-generated suggestions.
- **Flexible Transcription:** Utilizes OpenAI's Whisper model, with the option to use the faster, locally-run `faster-whisper` implementation or the `whisper-1` API for smaller files.
- **Intelligent Caching:** Caches transcriptions, cuts, and topic analyses to avoid re-processing videos, saving time and resources.
- **Multiple Export Options:** Export individual clips or batch-export all selected cuts with various quality settings.
- **Cross-Platform Support:** Runs on Windows, macOS, and Linux, with GPU acceleration available for NVIDIA users.

## 3. How it Works

The application follows a straightforward workflow:

1.  **Load Video:** Start by loading a video file from your local machine.
2.  **Transcription:** The audio is automatically transcribed using either the OpenAI API (`whisper-1`) for smaller files or a local Whisper/Faster-Whisper model for larger files.
3.  **AI Analysis:** The generated transcript is then analyzed by an OpenAI LLM (`gpt-4o`, `gpt-4o-mini`, or `o4-mini`) to identify and suggest potential cuts.
4.  **Review and Edit:** The suggested cuts are displayed in the main editor, where you can preview, edit, or create new cuts manually.
5.  **Export:** Once you are satisfied with the cuts, you can export them as individual video clips.

## 4. Installation

### Prerequisites

- **Python:** Version 3.8 or higher.
- **ffmpeg:** You must have `ffmpeg` installed and accessible from your system's PATH. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).

### Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/NightZpy/live-video-editor.git
    cd live-video-editor
    ```

2.  **Install dependencies based on your system and hardware:**

    - **For NVIDIA GPU (Windows/Linux):**
        - Ensure you have the [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) installed.
        - For Windows, run:
          ```bash
          pip install -r requirements-windows.txt
          ```
        - For Linux, it's recommended to install the base requirements and then the correct PyTorch version for your CUDA setup:
          ```bash
          pip install -r requirements-base.txt
          pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
          ```
          *(Replace `cu118` with your CUDA version if different.)*

    - **For CPU-only (Windows/macOS/Linux):**
        ```bash
        pip install -r requirements-base.txt
        ```

    - **For macOS:**
        ```bash
        pip install -r requirements-macos.txt
        ```

    - **Note on AMD GPUs:**
        The application currently does **not** support AMD GPUs for processing, even though a `requirements-amd.txt` file exists. The system will default to CPU processing if an AMD GPU is detected.

3.  **Set up environment variables:**
    - Create a `.env` file by copying the example file:
      ```bash
      cp .env.example .env
      ```
    - Open the `.env` file and add your OpenAI API key:
      ```
      OPENAI_API_KEY="your_openai_api_key_here"
      ```
    - You can also configure other optional variables, such as `WHISPER_MODEL` (e.g., `large-v3`, `medium`) and `USE_FASTER_WHISPER` (`true` or `false`).

## 5. Usage

To run the application, execute the following command from the root of the project:

```bash
python main.py
```

The main window will open, and you can start by loading a video. The application will guide you through the process of transcription, analysis, and editing.

## 6. Caching

The application uses a caching system to improve performance. Transcriptions, cuts, and topic analyses are stored in the `data/` directory. This means that if you load the same video again, the application will use the cached data instead of re-processing it from scratch.

To clear the cache for a specific video or for the entire application, you can delete the corresponding files or directories within the `data/` folder.

## 7. Project Structure

-   `src/`: Contains the main source code for the application.
    -   `core/`: Backend logic for video processing, transcription, and AI analysis.
    -   `ui/`: Frontend components and the main application window.
    -   `utils/`: Utility functions for caching, video processing, etc.
-   `data/`: Stores cached data, such as transcriptions and cuts.
-   `scripts/`: Includes additional scripts for various tasks.
-   `debug/`: Stores debug information, such as curl commands for API requests.

## 8. Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

## 9. Roadmap

For a list of planned features and improvements, see the [Project Roadmap](docs/ROADMAP.md).

## 10. License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
