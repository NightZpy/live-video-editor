"""
Main Window
Live Video Editor - Main Application Window
"""

import customtkinter as ctk
from .styles.theme import apply_theme, COLORS, FONTS, SPACING, get_frame_style, get_text_style
from .components import VideoLoaderComponent, CutTimesInputComponent, ManualInputComponent, MainEditorComponent
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
        self.loaded_video_info = None
        self.loaded_cuts_data = None
        self.has_cached_transcription = False
        
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
        elif self.current_phase == "main_editor":
            self.show_main_editor_phase()
    
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
        
        # Pass cache information to the component if it supports it
        if hasattr(cut_times_input, 'set_cache_status'):
            cut_times_input.set_cache_status(self.has_cached_transcription)
    
    def show_manual_input_phase(self):
        """Show manual input phase"""
        manual_input = ManualInputComponent(
            self.content_frame,
            on_process_complete=self.on_manual_input_complete
        )
        manual_input.grid(row=0, column=0, sticky="nsew", padx=SPACING["lg"], pady=SPACING["lg"])
    
    def show_main_editor_phase(self):
        """Show main editor phase"""
        # Convert loaded cuts data to the format expected by MainEditorComponent
        cuts_data = self._convert_cuts_data_for_editor(self.loaded_cuts_data)
        
        # Create thumbnail cache for video frames
        thumbnail_cache = None
        if self.loaded_video_info and cuts_data:
            from ..utils.thumbnail_cache import create_thumbnail_cache
            video_path = self.loaded_video_info.get('file_path')
            if video_path:
                print(f"🎬 Creating frame cache for {len(cuts_data)} cuts...")
                thumbnail_cache = create_thumbnail_cache(video_path, cuts_data)
                if thumbnail_cache:
                    print(f"✅ Frame cache created successfully")
                else:
                    print("⚠️ Failed to create frame cache, using fallback icons")
        
        main_editor = MainEditorComponent(
            self.content_frame, 
            cuts_data=cuts_data,
            video_info=self.loaded_video_info,
            thumbnail_cache=thumbnail_cache
        )
        main_editor.grid(row=0, column=0, sticky="nsew")
        
        # Store reference for potential updates
        self.main_editor = main_editor
    
    def _convert_cuts_data_for_editor(self, cuts_data):
        """Convert loaded cuts data to the format expected by MainEditorComponent"""
        if not cuts_data or 'cuts' not in cuts_data:
            return []
        
        # Convert from text_utils format to UI format
        converted_cuts = []
        for cut in cuts_data['cuts']:
            converted_cut = {
                "id": cut.get("id"),
                "title": cut.get("title", f"Cut {cut.get('id', 1)}"),
                "description": cut.get("description", ""),
                "start_time": cut.get("start", "00:00:00"),
                "end_time": cut.get("end", "00:00:00"),
                "duration": cut.get("duration", "00:00:00"),
                "content_type": cut.get("content_type", "unknown"),  # Preserve content_type from JSON
                "quality_score": cut.get("quality_score", "unknown"),  # Preserve quality_score
                "social_media_value": cut.get("quality_score", "unknown"),  # Map quality_score to social_media_value
                "status": "ready"  # Default status for parsed cuts
            }
            converted_cuts.append(converted_cut)
        
        return converted_cuts
    
    def on_video_loaded(self, video_info, cached_cuts=None, has_transcription=False):
        """
        Handle video loaded event with cache verification
        
        Args:
            video_info: Información del video
            cached_cuts: Cuts cargados desde caché (si existen)
            has_transcription: Si existe transcripción en caché
        """
        self.loaded_video_info = video_info
        
        if cached_cuts:
            # Ir directo al editor principal con cuts cargados
            print("🎯 Loading cuts from cache, going directly to main editor")
            self.loaded_cuts_data = cached_cuts
            self._go_to_main_editor()
            
        elif has_transcription:
            # Ir a ventana de selección con indicador de transcripción disponible
            print("📝 Transcription available, going to input selection with indicator")
            self._go_to_cut_times_input(has_cached_transcription=True)
            
        else:
            # Flujo normal
            print("🔄 No cache, proceeding with normal flow")
            self._go_to_cut_times_input()
    
    def _go_to_main_editor(self):
        """Navigate directly to main editor"""
        self.current_phase = "main_editor"
        self.show_current_phase()
        if self.loaded_video_info:
            print(f"📹 Video loaded: {self.loaded_video_info['filename']} - Going directly to main editor")
    
    def _go_to_cut_times_input(self, has_cached_transcription=False):
        """Navigate to cut times input with cache information"""
        self.current_phase = "cut_times_input"
        self.has_cached_transcription = has_cached_transcription  # Store for later use
        self.show_current_phase()
        if self.loaded_video_info:
            print(f"📹 Video loaded: {self.loaded_video_info['filename']} - Moving to cut times input phase")
    
    def on_cut_times_option_selected(self, option, data=None):
        """Handle cut times option selection"""
        print(f"🎯 Cut times option selected: {option}")
        
        if option == "manual_entry":
            self.current_phase = "manual_input"
            self.show_current_phase()
        elif option == "file_upload":
            if data:
                # File was successfully loaded and parsed
                self.loaded_cuts_data = data
                print(f"📄 File upload completed: {data.get('total_cuts', 0)} cuts loaded")
                # Skip manual input and go directly to main editor
                self.current_phase = "main_editor"
                self.show_current_phase()
            else:
                print("📄 File upload selected but no data provided")
        elif option == "automatic_analysis":
            if data:
                # AI analysis was successfully completed
                self.loaded_cuts_data = data
                print(f"🤖 AI analysis completed: {data.get('video_info', {}).get('total_cuts', 0)} cuts generated")
                print(f"🤖 Moving to main editor with AI-generated cuts")
                # Skip manual input and go directly to main editor
                self.current_phase = "main_editor"
                self.show_current_phase()
            else:
                print("🤖 AI analysis selected but no data provided")
    
    def on_manual_input_complete(self, action, data=None):
        """Handle manual input completion"""
        if action == "back":
            self.current_phase = "cut_times_input"
            self.show_current_phase()
        elif action == "complete":
            if data:
                # Manual input was completed successfully
                self.loaded_cuts_data = data
                print(f"✅ Manual input complete: {data.get('total_cuts', 0)} cuts processed")
            # Navigate to main editor
            self.current_phase = "main_editor"
            self.show_current_phase()
    
    def reset_to_video_loading(self):
        """Reset the application to video loading phase"""
        print("🔄 Resetting to video loading phase")
        
        # Reset state
        self.current_phase = "video_loading"
        self.loaded_video_info = None
        self.loaded_cuts_data = None
        
        # Show video loading phase
        self.show_current_phase()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
