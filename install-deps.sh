#!/bin/bash
# Installation script for live-video-editor
# Automatically detects platform and installs appropriate dependencies

set -e

echo "🚀 Installing live-video-editor dependencies..."

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS - installing macOS dependencies"
    pip install -r requirements-macos.txt
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OS" == "Windows_NT" ]]; then
    echo "🪟 Detected Windows - installing Windows dependencies"
    pip install -r requirements-windows.txt
else
    echo "🐧 Detected Linux - installing macOS dependencies (should work for Linux too)"
    pip install -r requirements-macos.txt
fi

echo "✅ Dependencies installed successfully!"
echo ""
echo "To run the application:"
echo "python main.py"
