# 📋 Development Plan - Live Video Editor with Modern UI

## 🎯 Technology Stack
- **Frontend**: CustomTkinter (modern interface with dark theme)
- **Backend**: Python 3.8+
- **Video Processing**: FFmpeg-python
- **LLM Integration**: OpenAI API / Anthropic Claude API
- **File Management**: pathlib, os
- **Video Preview**: opencv-python, PIL

## 🏗️ Project Structure

```
live-video-editor/
├── src/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   ├── video_loader.py
│   │   │   ├── time_input.py
│   │   │   ├── cuts_list.py
│   │   │   ├── video_preview.py
│   │   │   └── progress_dialog.py
│   │   └── styles/
│   │       ├── __init__.py
│   │       └── theme.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── video_processor.py
│   │   ├── time_parser.py
│   │   └── llm_integration.py
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       └── validators.py
├── assets/
│   ├── icons/
│   └── fonts/
├── requirements.txt
├── main.py
└── README.md
```

## 📱 Development Phases

### PHASE 1: Initial Setup and Base UI (Days 1-2)

#### 1.1 Environment Setup
```python
# requirements.txt
customtkinter==5.2.0
ffmpeg-python==0.2.0
opencv-python==4.8.1.78
Pillow==10.0.1
openai==1.3.0
python-dotenv==1.0.0
```

#### 1.2 Base Structure and Theme
- Create modern dark theme system
- Configure main window with fixed size
- Implement navigation between phases

### PHASE 2: UI Without Functionality (Days 3-5)

#### 2.1 Phase 1 - Video Loading
```python
# Main window with:
# - Elegant drag & drop area
# - Large video icon
# - Text "Drag your video here or click to select"
# - Supported format: MP4 only
# - Hover animations
```

#### 2.2 Phase 2.1 - Time Loading
```python
# - Drag & drop area for text files
# - Stylized "Manual" button
# - "Automatic (LLM)" button
# - Visual state indicators
```

#### 2.3 Phase 2.2 - Manual Input
```python
# - Simple TextArea with placeholder showing format example
# - "Process" button with states
# - Basic validation on submit
```

#### 2.4 Phase 3 - Main Editor
```python
# Main layout divided:
# - Left panel: Cuts list (30%)
# - Right panel: Preview and controls (70%)
#   - Interactive timeline
#   - Selected cut information
#   - Export controls
```

#### 2.5 Phase 4 - Progress Window
```python
# - Animated progress bar
# - Current file name
# - Estimated remaining time
# - Cancel option
```

### PHASE 3: Basic Core Functionality (Days 6-8)

#### 3.1 Real Video Loading (Window 1)
- Actual .mp4 file loading functionality
- Video metadata extraction (duration, resolution)
- File validation and error handling
- Store video path for processing

#### 3.2 Real Time File Loading (Window 2)
- Load text files with time formats
- File reading and parsing
- Display loaded content
- Manual input processing

#### 3.3 Time Processing & JSON Conversion
- Parse manual input format: `hh:mm:ss - hh:mm:ss - title - description`
- Convert to internal JSON format
- Basic validation and error reporting
- Generate cuts data structure

#### 3.4 Basic Cuts List (Main Editor)
- Display cuts in simple list format
- Show title, description, start/end times
- No thumbnails or advanced features
- Cut selection functionality

#### 3.5 Basic Video Preview with Cut Playback
##### 3.5.1 Video Player Backend Integration
- Extend VideoPreviewComponent with OpenCV video player
- Implement VideoPlayerManager class for efficient video handling
- Load video file once and reuse for all cuts (memory optimization)
- Frame extraction and display on tkinter Canvas

##### 3.5.2 Playback Controls Implementation
- Add functional Play/Pause/Stop buttons to VideoPreviewComponent
- Implement play state management (playing/paused/stopped)
- Add time display showing current position and cut duration
- Keyboard shortcuts for space bar play/pause
- Real video playback implementation (thread-safe streaming)

##### 3.5.3 Interactive Timeline Enhancement
- Replace static timeline markers with interactive Canvas-based timeline
- Implement draggable start and end markers for cut editing
- Add click-to-seek functionality on timeline
- Real-time progress indicator during playback

##### 3.5.4 Cut-Specific Playback Logic
- Automatic seek to cut start time when cut is selected
- Playback limited to cut duration (auto-stop at end time)
- Loop playback option within cut boundaries
- Preview frame display when paused

##### 3.5.5 UI Integration and Events
- Connect CutsListComponent selection to video preview
- Update timeline markers when cut selection changes
- Emit events for cut time modifications from timeline
- Synchronize cut data between components

### PHASE 4: Advanced Core Functionality (Days 9-12)

#### 4.1 Video Processing
- FFmpeg integration for cutting
- Metadata extraction enhancement
- Thumbnail generation
- Segment preview improvements

#### 4.2 Enhanced Time Parser
- Advanced format validation
- Multiple format support
- Descriptive error handling
- Import/export functionality

#### 4.3 LLM Integration
- API connection
- Prompt engineering for time extraction
- JSON response processing
- Automatic timestamp detection

### PHASE 5: Advanced Features (Days 13-16)

#### 5.1 Interactive Timeline
- Playback controls
- Visual start/end markers
- Drag to adjust times
- Temporal zoom

#### 5.2 Export System
- Individual export
- Batch export
- Destination folder selector
- Original quality preservation

#### 5.3 State Management
- Automatic project saving
- Session recovery
- Undo/Redo for edits

### PHASE 6: Polish and Optimization (Days 17-18)

#### 6.1 UX Enhancements
- Smooth animations
- Enhanced visual feedback
- Keyboard shortcuts
- Informative tooltips

#### 6.2 Performance
- Asynchronous loading
- Thumbnail caching
- Memory optimization

## 📐 UI Improvement Proposals

### Suggested Improvements:

#### 1. Enhanced Phase 1:
- Add loaded video preview
- Show basic information (duration, resolution, format)
- Replace video option

#### 2. Enhanced Phase 2:
- Tabs for different input methods
- Preview of loaded file content
- Real-time visual validation for manual input

#### 3. Enhanced Phase 3:
- Miniplayer with basic controls
- List vs grid view for cuts
- Editable properties panel
- Tags/categories system

#### 4. Additional Features:
- Predefined cut templates
- Export with different qualities
- Automatic scene analysis
- Cloud storage integration

## 🎨 Design Specifications

### Color Palette
```python
COLORS = {
    "primary": "#1a1a1a",      # Main background
    "secondary": "#2d2d2d",    # Panels
    "accent": "#007acc",       # Main buttons
    "success": "#4caf50",      # Success states
    "warning": "#ff9800",      # Warnings
    "error": "#f44336",        # Errors
    "text": "#ffffff",         # Main text
    "text_secondary": "#b0b0b0" # Secondary text
}
```

### Typography
- **Main**: Segoe UI, sans-serif
- **Monospace**: Consolas, Monaco, monospace
- **Sizes**: 
  - Headers: 18-24px
  - Body: 14-16px
  - Small: 12px

### Spacing
- **Base padding**: 16px
- **Base margin**: 8px
- **Border radius**: 8px
- **Shadows**: 0 2px 8px rgba(0,0,0,0.3)

## 🚀 Data Formats

### Manual Input/File
```
hh:mm:ss - hh:mm:ss - title - description
00:00:30 - 00:02:15 - Introduction - Welcome to the video
00:02:15 - 00:05:30 - Main Topic - Main content development
```

### Processed JSON Format
```json
{
  "cuts": [
    {
      "id": 1,
      "start": "00:00:30",
      "end": "00:02:15",
      "title": "Introduction",
      "description": "Welcome to the video",
      "duration": "00:01:45"
    }
  ],
  "video_info": {
    "filename": "video.mp4",
    "duration": "01:30:00",
    "resolution": "1920x1080",
    "fps": 30
  }
}
```

## 📋 Implementation Checklist

### Phase 1 ✅
- [DONE] Virtual environment setup
- [DONE] Dependencies installation
- [DONE] Folder structure
- [DONE] Base theme configuration

### Phase 2 ✅
- [DONE] Video loading component (UI)
- [DONE] Time loading interface (UI)
- [DONE] Simple manual time input (placeholder only)
- [DONE] Main editor layout (UI)
- [DONE] Progress window (UI)

### Phase 3 (Basic Core Functionality) 🔄
- [DONE] Real video loading (.mp4 files)
- [DONE] Real time file loading and parsing
- [DONE] Time processing and JSON conversion
- [DONE] Basic cuts list display
- [ ] Basic video preview with cut playback
  - [DONE] 3.5.1 Video Player Backend Integration
  - [PARTIAL] 3.5.2 Playback Controls Implementation
    - [DONE] UI Controls (Play/Pause/Stop buttons)
    - [DONE] Play state management
    - [DONE] Time display
    - [DONE] Keyboard shortcuts
    - [ ] Real video playback implementation (thread-safe streaming)
  - [ ] 3.5.3 Interactive Timeline Enhancement
  - [ ] 3.5.4 Cut-Specific Playback Logic
  - [ ] 3.5.5 UI Integration and Events

### Phase 4 ✅
- [ ] Advanced FFmpeg integration
- [ ] Enhanced time parser
- [ ] LLM connection
- [ ] Advanced validations

### Phase 5 ✅
- [ ] Interactive timeline
- [ ] Export system
- [ ] State management
- [ ] Advanced video preview

### Phase 6 ✅
- [ ] Animations
- [ ] Optimizations
- [ ] Testing
- [ ] Documentation

### Final Phase (Must-Have Enhancements) 🔄
- [ ] Syntax highlighting for manual input
- [ ] Real-time validation
- [ ] Valid lines counter
- [ ] Auto-completion suggestions
- [ ] Line numbers display

## 🔧 Technical Decisions & Library Usage

### **FFmpeg-python vs Direct FFmpeg Console**

#### **Why ffmpeg-python?**

1. **Type Safety and Validation**:
   - Parameter validation at development time
   - IDE autocomplete support
   - Fewer syntax errors

2. **Robust Error Handling**:
   ```python
   # With ffmpeg-python
   try:
       ffmpeg.input('video.mp4').output('cut.mp4', ss=30, t=60).run()
   except ffmpeg.Error as e:
       print(f"Error: {e.stderr}")
   
   # vs direct call (more error-prone)
   os.system('ffmpeg -i video.mp4 -ss 30 -t 60 cut.mp4')
   ```

3. **Dynamic Command Construction**:
   ```python
   # Easy programmatic construction
   stream = ffmpeg.input(video_path)
   if add_filters:
       stream = stream.filter('scale', 1920, 1080)
   stream.output(output_path).run()
   ```

4. **Python Integration**:
   - Better path and encoding handling
   - Natural integration with Python variables
   - Automatic special character escaping

#### **When to use direct FFmpeg:**
- For very complex commands that ffmpeg-python doesn't support well
- For maximum performance in specific cases

### **OpenCV-python Usage**

1. **Thumbnail/Frame Extraction**:
   ```python
   import cv2
   
   # Extract specific frame for preview
   cap = cv2.VideoCapture('video.mp4')
   cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
   ret, frame = cap.read()
   ```

2. **Video Information**:
   ```python
   # Get video metadata
   cap = cv2.VideoCapture('video.mp4')
   fps = cap.get(cv2.CAP_PROP_FPS)
   width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
   height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
   total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
   ```

3. **Interactive Timeline**:
   - Show specific frames on timeline
   - Real-time preview while user drags markers
   - Generate thumbnails for timeline

4. **Automatic Scene Analysis** (optional):
   ```python
   # Automatically detect scene changes
   def detect_scene_changes(video_path):
       cap = cv2.VideoCapture(video_path)
       # Scene change detection algorithm
   ```

### **Pillow (PIL) Usage**

1. **Thumbnail Processing**:
   ```python
   from PIL import Image
   
   # Resize thumbnails for UI
   img = Image.open('thumbnail.jpg')
   img.thumbnail((200, 150))  # For cuts list
   ```

2. **Format Conversion**:
   ```python
   # Convert OpenCV frames to Tkinter-compatible format
   cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
   pil_image = Image.fromarray(cv_image)
   tk_image = ImageTk.PhotoImage(pil_image)
   ```

3. **Image Optimization**:
   ```python
   # Compress thumbnails for better performance
   img.save('thumbnail.jpg', 'JPEG', quality=85, optimize=True)
   ```

4. **UI Visual Effects**:
   ```python
   # Add borders, shadows to thumbnails
   from PIL import ImageFilter
   img_with_shadow = img.filter(ImageFilter.GaussianBlur(2))
   ```

### **Complete Workflow Pipeline**

```python
# 1. OpenCV extracts frame
cap = cv2.VideoCapture('video.mp4')
cap.set(cv2.CAP_PROP_POS_MSEC, cut_start_ms)
ret, frame = cap.read()

# 2. Pillow processes the image
cv_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
pil_img = Image.fromarray(cv_rgb)
pil_img.thumbnail((300, 200))

# 3. Display in CustomTkinter
tk_image = ImageTk.PhotoImage(pil_img)
preview_label.configure(image=tk_image)

# 4. FFmpeg-python performs actual cut
ffmpeg.input('video.mp4').output(
    'cut.mp4', 
    ss=start_time, 
    t=duration
).run()
```

### **Library Responsibilities Summary**

| Library | Responsibility | Use Case |
|---------|----------------|----------|
| **CustomTkinter** | Modern UI framework | All interface components |
| **FFmpeg-python** | Video cutting/processing | Export final cuts |
| **OpenCV** | Frame extraction & analysis | Timeline previews, metadata |
| **Pillow** | Image processing | Thumbnail generation, UI images |
| **OpenAI/Anthropic** | AI processing | Automatic timestamp extraction |

## 🎯 Must-Have Features (Future Enhancements)

### **Enhanced Manual Input System**
- **Syntax Highlighting**: Color-coded format validation
  ```python
  # Green: Valid timestamp format
  # Red: Invalid format
  # Blue: Title and description sections
  ```
- **Real-time Validation**: Live feedback as user types
- **Valid Lines Counter**: Shows "X of Y lines valid"
- **Auto-completion**: Suggest common timestamp patterns
- **Line Numbers**: For easy error identification

### **Advanced Timeline Features**
- **Waveform Visualization**: Audio waveform overlay on timeline
- **Keyboard Shortcuts**: 
  - Space: Play/Pause
  - Left/Right arrows: Frame by frame
  - Shift + Left/Right: 10 second jumps
- **Snap to Beat**: Automatic alignment to audio beats
- **Multiple Selection**: Select and edit multiple cuts at once

### **Export Enhancements**
- **Quality Presets**: 4K, 1080p, 720p, 480p options
- **Format Selection**: MP4, AVI, MOV, WebM export options
- **Compression Settings**: Customizable bitrate and quality
- **Batch Processing**: Queue multiple export jobs
- **Progress Notifications**: System notifications when exports complete

### **LLM Integration Improvements**
- **Multiple LLM Providers**: OpenAI, Anthropic, Local models
- **Custom Prompts**: User-defined extraction prompts
- **Confidence Scoring**: Show AI confidence for each detected segment
- **Manual Review**: Review and edit AI-generated timestamps before processing

### **Video Format Support**
- **Multiple Format Support**: AVI, MOV, MKV, WebM, FLV
  ```python
  # Extended format validation
  # Format-specific metadata extraction
  # Automatic format detection
  ```
- **Format Conversion**: Convert between formats during export
- **Codec Support**: Different video/audio codec handling
- **Quality Profiles**: Different compression settings per format

### **Enhanced UI System**
- **Responsive Layout**: Auto-resize based on screen size and content
  ```python
  # Dynamic window sizing
  # Grid weight management for different screen sizes
  # Adaptive component scaling
  ```
- **Multi-monitor Support**: Proper handling of different screen resolutions
- **Zoom Controls**: UI scaling for accessibility
- **Window State Management**: Remember size and position between sessions
