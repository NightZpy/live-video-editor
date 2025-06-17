"""
Main Window
Live Video Editor - Main Application Window
"""

import customtkinter as ctk
from .styles.theme import apply_theme, COLORS, FONTS, SPACING, get_frame_style, get_text_style
from .components import VideoLoaderComponent, CutTimesInputComponent, ManualInputComponent
from .components.video_loader import VideoLoaderComponent

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
        
        # Current phase tracking
        self.current_phase = "video_loading"
        self.loaded_video = None
        
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
        
        # Show appropriate phase
        self.show_current_phase()
    
    def show_current_phase(self):
        """Show the current phase UI"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if self.current_phase == "video_loading":
            self.show_video_loading_phase()
        elif self.current_phase == "cut_times_input":
            self.show_cut_times_input_phase()
        elif self.current_phase == "manual_input":
            self.show_manual_input_phase()
    
    def show_video_loading_phase(self):
        """Show video loading phase"""
        video_loader = VideoLoaderComponent(
            self.content_frame,
            on_video_loaded=self.on_video_loaded
        )
        video_loader.grid(row=0, column=0, sticky="nsew", padx=SPACING["lg"], pady=SPACING["lg"])
    
    def show_cut_times_input_phase(self):
        """Show cut times input phase"""
        cut_times_input = CutTimesInputComponent(
            self.content_frame,
            on_option_selected=self.on_cut_times_option_selected
        )
        cut_times_input.grid(row=0, column=0, sticky="nsew", padx=SPACING["lg"], pady=SPACING["lg"])
    
    def show_manual_input_phase(self):
        """Show manual input phase"""
        manual_input = ManualInputComponent(
            self.content_frame,
            on_process_complete=self.on_manual_input_complete
        )
        manual_input.grid(row=0, column=0, sticky="nsew", padx=SPACING["lg"], pady=SPACING["lg"])
    
    def on_video_loaded(self, video_path):
        """Handle video loaded event"""
        self.loaded_video = video_path
        self.current_phase = "cut_times_input"
        self.show_current_phase()
        print(f"📹 Video loaded: {video_path} - Moving to cut times input phase")
    
    def on_cut_times_option_selected(self, option, data=None):
        """Handle cut times option selection"""
        print(f"🎯 Cut times option selected: {option}")
        
        if option == "manual_entry":
            self.current_phase = "manual_input"
            self.show_current_phase()
        elif option == "file_upload":
            print("📄 File upload selected - will implement in Phase 3")
        elif option == "automatic_analysis":
            api_key = data.get('api_key', 'N/A') if data else 'N/A'
            print(f"🤖 AI analysis selected with API key: {api_key}")
    
    def on_manual_input_complete(self, action, data=None):
        """Handle manual input completion"""
        if action == "back":
            self.current_phase = "cut_times_input"
            self.show_current_phase()
        elif action == "complete":
            print(f"✅ Manual input complete: {data}")
            # Will navigate to editor phase in future

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
