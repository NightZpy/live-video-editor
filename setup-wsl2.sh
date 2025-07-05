#!/bin/bash
# WSL2 AMD GPU Setup Script for Live Video Editor
# Run this script inside WSL2 Ubuntu

set -e  # Exit on any error

echo "🐧 Starting WSL2 AMD GPU setup for Live Video Editor..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in WSL2
if [[ ! -f /proc/version ]] || ! grep -q Microsoft /proc/version; then
    print_error "This script must be run inside WSL2"
    exit 1
fi

print_status "Running in WSL2"

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
print_status "Installing Python and build dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    git curl wget build-essential \
    libnuma-dev libffi-dev libssl-dev \
    pkg-config

# Check if ROCm is already installed
if ! command -v rocm-smi &> /dev/null; then
    print_status "Installing ROCm for AMD GPU support..."
    
    # Add ROCm repository
    wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
    echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/5.7 ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list
    
    # Install ROCm
    sudo apt update
    sudo apt install -y rocm-dev rocm-libs rocm-utils rocm-smi
    
    # Add user to groups
    sudo usermod -a -G render $USER
    sudo usermod -a -G video $USER
    
    print_warning "ROCm installed. You may need to restart WSL2 for GPU access:"
    print_warning "In Windows: wsl --shutdown && wsl"
else
    print_status "ROCm already installed"
fi

# Create project directory
PROJECT_DIR="$HOME/live-video-editor"
print_status "Setting up project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
if [[ ! -d "venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with ROCm
print_status "Installing PyTorch with ROCm support..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# Install other dependencies
print_status "Installing project dependencies..."
pip install customtkinter>=5.2.2
pip install ffmpeg-python==0.2.0
pip install opencv-python>=4.9.0
pip install Pillow>=10.0.1
pip install openai>=1.35.0
pip install python-dotenv==1.0.0

# Install Whisper
print_status "Installing OpenAI Whisper..."
pip install git+https://github.com/openai/whisper.git

# Copy project files if they exist in Windows
WINDOWS_PROJECT="/mnt/d/Proyectos/live-video-editor"
if [[ -d "$WINDOWS_PROJECT" ]]; then
    print_status "Copying project files from Windows..."
    
    # Copy source files
    if [[ -d "$WINDOWS_PROJECT/src" ]]; then
        cp -r "$WINDOWS_PROJECT/src" .
    fi
    
    # Copy main files
    for file in main.py plan.md pyrightconfig.json; do
        if [[ -f "$WINDOWS_PROJECT/$file" ]]; then
            cp "$WINDOWS_PROJECT/$file" .
        fi
    done
    
    # Copy data directory if it exists
    if [[ -d "$WINDOWS_PROJECT/data" ]]; then
        cp -r "$WINDOWS_PROJECT/data" .
    fi
else
    print_warning "Windows project directory not found at $WINDOWS_PROJECT"
    print_warning "You'll need to copy your project files manually"
fi

# Test GPU detection
print_status "Testing GPU detection..."
python3 -c "
import torch
print('🐍 Python version:', torch.__version__)
print('🔥 PyTorch version:', torch.__version__)
print('🚀 ROCm available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('📊 GPU devices:', torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f'  Device {i}: {torch.cuda.get_device_name(i)}')
else:
    print('💻 Using CPU mode')
"

# Create startup script
print_status "Creating startup script..."
cat > start_app.sh << 'EOF'
#!/bin/bash
cd ~/live-video-editor
source venv/bin/activate

# Set display for GUI (if using X11)
export DISPLAY=:0

echo "🚀 Starting Live Video Editor..."
echo "📁 Project directory: $(pwd)"
echo "🐍 Python: $(which python)"

# Test GPU
python -c "import torch; print('🔥 GPU available:', torch.cuda.is_available())"

# Run the application
python main.py
EOF

chmod +x start_app.sh

print_status "Setup completed successfully!"
echo
echo "🎉 Next steps:"
echo "1. If this is your first ROCm installation, restart WSL2:"
echo "   - In Windows: wsl --shutdown"
echo "   - Then: wsl"
echo
echo "2. To run the application:"
echo "   cd ~/live-video-editor"
echo "   ./start_app.sh"
echo
echo "3. For GUI support on Windows 10, install VcXsrv or X410"
echo "   Windows 11 22H2+ has built-in GUI support (WSLg)"
echo
print_status "Project location: $PROJECT_DIR"
