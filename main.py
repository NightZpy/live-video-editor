#!/usr/bin/env python3
"""
Live Video Editor
Entry point for the application
"""

import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path for runtime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import using absolute path (Pylance will understand this)
try:
    from ui.main_window import MainWindow
except ImportError:
    # Fallback for different environments
    from src.ui.main_window import MainWindow

def main():
    """Main application entry point"""
    # Create the main application window normally
    # Drag and drop will be handled at component level
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
