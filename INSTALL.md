# Installation Guide - Live Video Editor

This guide helps you install the correct dependencies based on your system and GPU.

## 🚀 Quick Installation

### For Most Users (Windows with NVIDIA GPU or CPU only):
```bash
pip install -r requirements-windows.txt
```

### For macOS/Linux:
```bash
pip install -r requirements-macos.txt
```

### For AMD GPU Users (Windows/Linux):
```bash
pip install -r requirements-amd.txt
```

## 🎯 Detailed GPU Support

### NVIDIA GPU (Recommended) 🚀
- **Compatibility**: GeForce GTX 1060 and newer, RTX series
- **Memory**: Minimum 2GB VRAM recommended
- **Installation**: Use `requirements-windows.txt` or `requirements-macos.txt`
- **Performance**: Fastest transcription with Whisper

### AMD GPU (RX/Vega/NAVI/RDNA) 🔥
- **Compatibility**: RX 5000 series and newer, Vega, NAVI, RDNA
- **Installation**: Use `requirements-amd.txt`
- **Note**: Requires ROCm-compatible PyTorch
- **Performance**: Good transcription speed

### CPU Only 💻
- **Compatibility**: Any modern CPU
- **Installation**: Use `requirements-base.txt`
- **Performance**: Slower but works on all systems

## 🔧 Installation Steps

### 1. Create Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Choose Your Installation

#### Option A: Windows with NVIDIA GPU or CPU
```bash
pip install -r requirements-windows.txt
```

#### Option B: AMD GPU (Windows/Linux)
```bash
# Method 1: Using requirements file (may have version conflicts)
pip uninstall torch torchvision torchaudio -y
pip install -r requirements-amd.txt

# Method 2: Manual installation (recommended for AMD)
# Navigate to project folder
cd d:\Proyectos\live-video-editor

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Remove any existing PyTorch installation
pip uninstall torch torchvision torchaudio -y

# Install AMD GPU support
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/rocm5.6
pip install torchvision==0.16.0 --index-url https://download.pytorch.org/whl/rocm5.6

# Install remaining dependencies
pip install -r requirements-base-no-torch.txt

# Method 3: Alternative ROCm version (if Method 2 fails)
# Navigate to project folder (if not already there)
cd d:\Proyectos\live-video-editor

# Activate virtual environment (if not already activated)
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Remove any existing PyTorch installation
pip uninstall torch torchvision torchaudio -y

# Install older ROCm version
pip install torch==2.0.1 --index-url https://download.pytorch.org/whl/rocm5.4.2
pip install torchvision==0.15.2 --index-url https://download.pytorch.org/whl/rocm5.4.2

# Install remaining dependencies
pip install -r requirements-base-no-torch.txt
```

#### Option C: macOS/Linux
```bash
pip install -r requirements-macos.txt
```

### 3. Run the Application
```bash
python main.py
```

## 🔥 Quick AMD GPU Setup (Windows)

For your specific case with AMD GPU, run these exact commands:

```bash
# 1. Navigate to your project
cd d:\Proyectos\live-video-editor

# 2. Activate the virtual environment
.venv\Scripts\activate

# 3. Clean any existing PyTorch installation
pip uninstall torch torchvision torchaudio -y

# 4. Install PyTorch with ROCm 5.6 (most stable)
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/rocm5.6
pip install torchvision==0.16.0 --index-url https://download.pytorch.org/whl/rocm5.6

# 5. Install remaining dependencies
pip install -r requirements-base-no-torch.txt

# 6. Test the installation
python -c "import torch; print('PyTorch version:', torch.__version__); print('ROCm available:', torch.cuda.is_available())"

# 7. Run the application
python main.py
```

If step 4 fails, try the alternative ROCm 5.4.2 version:
```bash
pip install torch==2.0.1 --index-url https://download.pytorch.org/whl/rocm5.4.2
pip install torchvision==0.15.2 --index-url https://download.pytorch.org/whl/rocm5.4.2
```

## 🧪 GPU Detection

The application will automatically detect your GPU and show:
- ✅ **NVIDIA GPU**: "🚀 NVIDIA GPU detected: [GPU Name]"
- ✅ **AMD GPU**: "🔥 AMD GPU with ROCm detected"
- ✅ **AMD without ROCm**: "🔍 AMD GPU detected but ROCm not available" + installation instructions
- ✅ **CPU**: "💻 No compatible GPU found, using CPU for processing"

## 🆘 Troubleshooting

### AMD GPU Not Detected
If you have an AMD GPU but the app uses CPU:

1. **Verify ROCm installation:**
   ```bash
   python -c "import torch; print('PyTorch version:', torch.__version__)"
   python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
   ```
   - Should show version with `+rocm` (e.g., `2.1.0+rocm5.6`)
   - CUDA available should be `True` (ROCm uses CUDA API)

2. **If installation failed, try manual installation:**
   ```bash
   # Remove existing installations
   pip uninstall torch torchvision torchaudio -y
   
   # Try different ROCm versions
   # ROCm 5.6 (newer):
   pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/rocm5.6
   
   # OR ROCm 5.4.2 (more stable):
   pip install torch==2.0.1 --index-url https://download.pytorch.org/whl/rocm5.4.2
   
   # Then install other dependencies
   pip install -r requirements-base-no-torch.txt
   ```

3. **Check compatible GPUs:**
   - ✅ RX 6000 series (RDNA2): RX 6700 XT, 6800, 6900 XT
   - ✅ RX 5000 series (RDNA): RX 5700, 5700 XT
   - ✅ Vega series: Vega 56, 64, VII
   - ❌ RX 500 series and older are not officially supported

4. **If still not working, use CPU mode:**
   ```bash
   pip install torch>=2.1.0  # Regular CPU version
   ```

### NVIDIA GPU Not Detected
1. Verify CUDA installation: `python -c "import torch; print(torch.cuda.is_available())"`
2. Should return `True`
3. Check GPU memory: App requires minimum 2GB VRAM

### Memory Issues
- **GPU Out of Memory**: App will automatically fallback to CPU
- **Large Videos**: Use smaller Whisper models automatically selected
- **CPU Slow**: Consider upgrading to supported GPU

## 📋 File Overview

- `requirements.txt` - Main file with installation options
- `requirements-base.txt` - Core dependencies (NVIDIA/CPU)
- `requirements-windows.txt` - Windows-specific (NVIDIA/CPU)
- `requirements-macos.txt` - macOS/Linux-specific
- `requirements-amd.txt` - AMD GPU support
- `requirements-base-no-torch.txt` - Dependencies without PyTorch (used by AMD)

## 🐧 WSL2 Option for AMD GPU (Recommended for Windows)

Since ROCm pip packages for Windows are not yet available, WSL2 provides the best AMD GPU support:

### Automatic Setup (Recommended)

#### 1. Run PowerShell Setup (as Administrator)
```powershell
# In PowerShell as Administrator
cd d:\Proyectos\live-video-editor
.\setup-wsl2.ps1
```

#### 2. Run Ubuntu Setup
```bash
# In Ubuntu 22.04 (from Start Menu)
chmod +x ~/setup-wsl2.sh
~/setup-wsl2.sh
```

#### 3. Start the Application
```bash
# In Ubuntu WSL2
cd ~/live-video-editor
./start_app.sh
```

### Manual WSL2 Setup

If you prefer manual setup, follow the detailed guide in `WSL2-SETUP.md`.

### GUI Support Options

- **Windows 11 22H2+**: GUI works automatically (WSLg)
- **Windows 10/11**: Install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) or [X410](https://x410.dev/)
- **Alternative**: Modify app to run as web interface

### WSL2 Benefits for AMD GPU

✅ **Native Linux ROCm support**  
✅ **Better PyTorch compatibility**  
✅ **Near-native GPU performance**  
✅ **Access to Windows files via `/mnt/d/`**  
✅ **Easier dependency management**
