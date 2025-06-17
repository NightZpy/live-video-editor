"""
Video Loader Component
Drag & Drop interface for video file loading (UI Only)
"""

import customtkinter as ctk
from ..styles.theme import COLORS, FONTS, SPACING, get_frame_style, get_text_style, get_button_style

class VideoLoaderComponent(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create drag and drop area
        self.create_drop_area()
        
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
        
        # Instruction text
        instruction_style = get_text_style("default")
        self.instruction_label = ctk.CTkLabel(
            self.drop_area,
            text="Drag your MP4 video here or click to select",
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
        
        # Select file button
        button_style = get_button_style("primary")
        self.select_button = ctk.CTkButton(
            self.drop_area,
            text="Select Video File",
            width=200,
            height=40,
            command=self.on_select_file,
            **button_style
        )
        self.select_button.grid(row=5, column=0, pady=SPACING["md"])
        
        # Bind hover events for visual feedback
        self.bind_hover_events()
        
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
        self.drop_area.configure(border_color=COLORS["border"])
        self.drop_area.configure(border_width=1)
    
    def on_select_file(self):
        """Handle file selection (placeholder for now)"""
        # For now, just show a message - functionality will be added in Phase 3
        print("🎬 File selection clicked! (UI Only - no functionality yet)")
        
        # Visual feedback
        self.select_button.configure(text="Selected! (Demo)")
        self.after(2000, lambda: self.select_button.configure(text="Select Video File"))

if __name__ == "__main__":
    # Test the component
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from styles.theme import apply_theme
    
    root = ctk.CTk()
    apply_theme()
    root.title("Video Loader Test")
    root.geometry("800x600")
    
    loader = VideoLoaderComponent(root)
    loader.pack(fill="both", expand=True, padx=20, pady=20)
    
    root.mainloop()
