"""
Main Window
Live Video Editor - Main Application Window
"""

import customtkinter as ctk
from .styles.theme import apply_theme, COLORS, FONTS, SPACING, get_frame_style, get_text_style

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Apply theme
        apply_theme()
        
        # Configure window
        self.title("Live Video Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Set window background
        self.configure(fg_color=COLORS["primary"])
        
        # Initialize UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main UI structure"""
        # Main container frame
        main_frame_style = get_frame_style("primary")
        self.main_frame = ctk.CTkFrame(
            self,
            **main_frame_style
        )
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header
        self.create_header()
        
        # Content area (will be used for different phases)
        self.create_content_area()
    
    def create_header(self):
        """Create the application header"""
        header_style = get_frame_style("card")
        header_frame = ctk.CTkFrame(
            self.main_frame,
            height=80,
            **header_style
        )
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=(SPACING["md"], SPACING["sm"]))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)
        
        # Title
        title_style = get_text_style("large_header")
        title_label = ctk.CTkLabel(
            header_frame,
            text="Live Video Editor",
            **title_style
        )
        title_label.grid(row=0, column=0, pady=SPACING["md"])
    
    def create_content_area(self):
        """Create the main content area"""
        content_style = get_frame_style("default")
        self.content_frame = ctk.CTkFrame(
            self.main_frame,
            **content_style
        )
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Placeholder content
        placeholder_style = get_text_style("secondary")
        placeholder_label = ctk.CTkLabel(
            self.content_frame,
            text="UI Base Structure Ready\nPhase 1.2 Complete ✓",
            **placeholder_style
        )
        placeholder_label.grid(row=0, column=0, pady=SPACING["xl"])

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
