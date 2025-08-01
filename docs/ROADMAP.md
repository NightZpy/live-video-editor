# Project Roadmap

This document outlines the planned features and improvements for the Live Video Editor, based on the project's development plan and architectural diagrams.

## High-Priority Features

### 1. AssemblyAI Integration
- **Goal:** Integrate AssemblyAI as an alternative transcription and processing service.
- **Implementation:**
    - Create a `UniversalTranscriber` to manage different transcription services.
    - Implement an `AssemblyAITranscriber` to handle API requests.
    - Allow users to switch between Whisper and AssemblyAI via environment variables.
- **Benefit:** Faster processing for large files and potentially more accurate results.
- **Technical Details:** For more information on the proposed architecture, see the [AssemblyAI Integration Diagram](CLASS_DIAGRAM.md).

### 2. Interactive Timeline Enhancements
- **Goal:** Make the video timeline fully interactive for precise editing.
- **Features:**
    - Draggable start and end markers to visually adjust cut times.
    - Click-to-seek functionality.
    - Waveform visualization overlay.
    - Temporal zoom (zoom in/out).

### 3. State Management
- **Goal:** Allow users to save their work and resume later.
- **Features:**
    - **Project Saving/Loading:** Save the entire session (video path, cuts, edits) to a project file.
    - **Session Recovery:** Automatically save the state to recover from unexpected closures.
    - **Undo/Redo:** Implement undo/redo functionality for all editing actions.

## Core Functionality Improvements

### 1. Enhanced Manual Input
- **Goal:** Improve the manual input experience for power users.
- **Features:**
    - Syntax highlighting for the `hh:mm:ss - hh:mm:ss - title - description` format.
    - Real-time validation with clear error messages.
    - A counter for valid/invalid lines.

### 2. Advanced Export Options
- **Goal:** Provide more flexibility when exporting clips.
- **Features:**
    - Quality presets (e.g., 4K, 1080p, 720p).
    - Export format selection (e.g., MP4, MOV, WebM).
    - Customizable compression settings.

### 3. Expanded Video Format Support
- **Goal:** Allow users to import a wider range of video formats.
- **Formats:** AVI, MOV, MKV, WebM, FLV.

## User Experience (UX) and Polish

### 1. UI Enhancements
- **Responsive Layout:** Ensure the UI adapts gracefully to different window sizes.
- **UI Animations:** Add smooth transitions and animations for a more modern feel.
- **Keyboard Shortcuts:** Implement a comprehensive set of keyboard shortcuts for all major actions.

### 2. Performance Optimization
- **Asynchronous Loading:** Ensure all file I/O and processing tasks are non-blocking.
- **Memory Management:** Optimize memory usage, especially for long videos and large numbers of cuts.

## Long-Term Vision

- **Multi-LLM Support:** Allow users to choose between different LLM providers (e.g., OpenAI, Anthropic, local models).
- **Cloud Integration:** Save/load projects directly from cloud storage services like Google Drive or Dropbox.
- **Real-time Collaboration:** Enable multiple users to work on the same project simultaneously.
