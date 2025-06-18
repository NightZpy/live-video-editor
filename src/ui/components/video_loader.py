"""
Video Loader Component
Drag & Drop interface for video file loading with real functionality
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.utils.video_utils import validate_and_extract_metadata
from ..styles.theme import COLORS, FONTS, SPACING, get_frame_style, get_text_style, get_button_style

# Try to import drag and drop - completely optional
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
    print("✅ Drag & Drop support available")
except ImportError:
    HAS_DND = False
    print("⚠️ Drag & Drop not available - using click-to-select only")

class VideoLoaderComponent(ctk.CTkFrame):
    def __init__(self, parent, on_video_loaded=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callback for when video is loaded
        self.on_video_loaded = on_video_loaded
        
        # State
        self.is_processing = False
        self.loaded_video_info = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create drag and drop area
        self.create_drop_area()
        self.setup_drag_and_drop()
        
    def create_drop_area(self):
        """Create the main drag and drop area"""
        # Main drop area frame
        drop_frame_style = get_frame_style("card")
        self.drop_area = ctk.CTkFrame(
            self,
            height=400,
            **drop_frame_style
        )
        self.drop_area.grid(row=0, column=0, sticky="nsew", padx=SPACING["xl"], pady=SPACING["xl"])
        self.drop_area.grid_columnconfigure(0, weight=1)
        self.drop_area.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.drop_area.grid_propagate(False)
        
        # Video icon (using text for now - we can add real icon later)
        icon_style = get_text_style("large_header")
        self.video_icon = ctk.CTkLabel(
            self.drop_area,
            text="🎬",
            font=(FONTS["main"][0], 64),
            **{k: v for k, v in icon_style.items() if k != 'font'}
        )
        self.video_icon.grid(row=1, column=0, pady=(SPACING["lg"], SPACING["sm"]))
        
        # Main title
        title_style = get_text_style("header")
        self.title_label = ctk.CTkLabel(
            self.drop_area,
            text="Load Your Video",
            **title_style
        )
        self.title_label.grid(row=2, column=0, pady=SPACING["sm"])
        
        # Instruction text (always click-to-select for now)
        instruction_style = get_text_style("default")
        self.instruction_label = ctk.CTkLabel(
            self.drop_area,
            text="Click to select your MP4 video",
            **instruction_style
        )
        self.instruction_label.grid(row=3, column=0, pady=SPACING["sm"])
        
        # Supported format info
        format_style = get_text_style("small")
        self.format_label = ctk.CTkLabel(
            self.drop_area,
            text="Supported format: MP4",
            **format_style
        )
        self.format_label.grid(row=4, column=0, pady=(SPACING["sm"], SPACING["lg"]))
        
        # Make the entire drop area clickable
        self.drop_area.bind("<Button-1>", lambda e: self.handle_click_to_select())
        
        # Bind click events to all child widgets too
        for widget in [self.video_icon, self.title_label, self.instruction_label, self.format_label]:
            widget.bind("<Button-1>", lambda e: self.handle_click_to_select())
        
        # Bind hover events for visual feedback
        self.bind_hover_events()
    
    def setup_drag_and_drop(self):
        """Setup drag and drop functionality (if available)"""
        # For now, we'll disable drag and drop to ensure compatibility
        # Click-to-select will work on all systems
        print("📋 Drag & Drop temporarily disabled - using click-to-select")
        return
        
        # TODO: Implement proper drag & drop for CustomTkinter when stable
        # This would require integrating tkinterdnd2 with CustomTkinter's widget hierarchy
        
    def bind_hover_events(self):
        """Bind hover events for visual feedback"""
        # Hover effects for the drop area
        self.drop_area.bind("<Enter>", self.on_hover_enter)
        self.drop_area.bind("<Leave>", self.on_hover_leave)
        
        # Bind to child widgets too
        for widget in [self.video_icon, self.title_label, self.instruction_label, self.format_label]:
            widget.bind("<Enter>", self.on_hover_enter)
            widget.bind("<Leave>", self.on_hover_leave)
    
    def on_hover_enter(self, event):
        """Handle hover enter event"""
        self.drop_area.configure(border_color=COLORS["accent"])
        self.drop_area.configure(border_width=2)
        
    def on_hover_leave(self, event):
        """Handle hover leave event"""
        if not self.is_processing:
            self.drop_area.configure(border_color=COLORS["border"])
            self.drop_area.configure(border_width=1)
    
    def handle_click_to_select(self):
        """Handle click to select file"""
        if self.is_processing:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select MP4 Video File",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            self.process_video_file(file_path)
    
    def handle_drop_event(self, event):
        """Handle drag and drop event"""
        if self.is_processing:
            return
            
        try:
            # Get dropped files
            files = event.data.split()
            if files:
                # Take the first file
                file_path = files[0].strip('{}')  # Remove braces if present
                self.process_video_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error processing dropped file: {str(e)}")
    
    def process_video_file(self, file_path):
        """Process the selected video file"""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.update_ui_state("processing")
        
        # Validate and extract metadata in one efficient operation
        is_valid, error_message, metadata = validate_and_extract_metadata(file_path)
        
        if not is_valid:
            self.is_processing = False
            self.update_ui_state("error", error_message)
            messagebox.showerror("Invalid File", error_message)
            self.reset_ui_state()
            return
        
        if not metadata:
            self.is_processing = False
            self.update_ui_state("error", "Could not read video metadata")
            messagebox.showerror("Error", "Could not read video metadata")
            self.reset_ui_state()
            return
        
        # Success!
        self.loaded_video_info = metadata
        self.update_ui_state("success")
        
        # Proceed to next phase after a short delay
        self.after(1500, self.proceed_to_next_phase)
    
    def update_ui_state(self, state, message=""):
        """Update UI based on current state"""
        if state == "processing":
            self.title_label.configure(text="Processing Video...")
            self.instruction_label.configure(text="Please wait while we analyze your video")
            self.format_label.configure(text="Extracting metadata...")
            self.video_icon.configure(text="⏳")
            
        elif state == "success" and self.loaded_video_info:
            info = self.loaded_video_info
            self.title_label.configure(text="Video Loaded Successfully!")
            self.instruction_label.configure(text=f"{info['filename']} • {info['duration']} • {info['resolution']}")
            self.format_label.configure(text=f"Size: {info['file_size']} • FPS: {info['fps']}")
            self.video_icon.configure(text="✅")
            
        elif state == "error":
            self.title_label.configure(text="Error Loading Video")
            self.instruction_label.configure(text=message)
            self.format_label.configure(text="Please try again with a valid MP4 file")
            self.video_icon.configure(text="❌")
    
    def reset_ui_state(self):
        """Reset UI to initial state"""
        self.after(3000, self._reset_ui_elements)
    
    def _reset_ui_elements(self):
        """Reset UI elements to initial state"""
        self.title_label.configure(text="Load Your Video")
        self.instruction_label.configure(text="Click to select your MP4 video")
        self.format_label.configure(text="Supported format: MP4")
        self.video_icon.configure(text="🎬")
        self.is_processing = False
    
    def proceed_to_next_phase(self):
        """Proceed to the next phase with loaded video"""
        if self.on_video_loaded and self.loaded_video_info:
            self.on_video_loaded(self.loaded_video_info)

if __name__ == "__main__":
    # Test the component
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from styles.theme import apply_theme
    
    # Create root window with drag and drop support
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = ctk.CTk()
        print("Warning: tkinterdnd2 not available, drag and drop disabled")
    
    apply_theme()
    root.title("Video Loader Test")
    root.geometry("800x600")
    
    def on_video_loaded(video_info):
        print(f"Video loaded: {video_info}")
    
    loader = VideoLoaderComponent(root, on_video_loaded=on_video_loaded)
    loader.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()
