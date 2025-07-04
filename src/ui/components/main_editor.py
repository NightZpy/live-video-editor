"""
Main Editor Component
Phase 2.4 - Main Editor Layout with Cuts List and Video Preview
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, COLORS, SPACING
from .cuts_list import CutsListComponent
from .video_preview import VideoPreviewComponent

class MainEditorComponent(ctk.CTkFrame):
    def __init__(self, parent, cuts_data=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid - 30/70 split
        self.grid_columnconfigure(0, weight=3)  # Left panel (30%)
        self.grid_columnconfigure(1, weight=7)  # Right panel (70%)
        self.grid_rowconfigure(0, weight=1)
        
        # Store cuts data
        self.cuts_data = cuts_data or []
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        if self.cuts_data:
            self.load_cuts_data()
    
    def setup_ui(self):
        """Setup the main editor interface"""
        # Left panel - Cuts list (30%)
        self.create_cuts_panel()
        
        # Right panel - Video preview and controls (70%)
        self.create_preview_panel()
    
    def create_cuts_panel(self):
        """Create the left panel with cuts list"""
        cuts_panel_style = get_frame_style("default")
        cuts_panel = ctk.CTkFrame(self, **cuts_panel_style)
        cuts_panel.grid(row=0, column=0, sticky="nsew", padx=(SPACING["lg"], SPACING["sm"]), pady=SPACING["lg"])
        cuts_panel.grid_columnconfigure(0, weight=1)
        cuts_panel.grid_rowconfigure(0, weight=1)
        
        # Cuts list component
        self.cuts_list = CutsListComponent(
            cuts_panel,
            on_cut_selected=self.on_cut_selected
        )
        self.cuts_list.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    def create_preview_panel(self):
        """Create the right panel with video preview and controls"""
        preview_panel_style = get_frame_style("default")
        preview_panel = ctk.CTkFrame(self, **preview_panel_style)
        preview_panel.grid(row=0, column=1, sticky="nsew", padx=(SPACING["sm"], SPACING["lg"]), pady=SPACING["lg"])
        preview_panel.grid_columnconfigure(0, weight=1)
        preview_panel.grid_rowconfigure(0, weight=1)
        
        # Video preview component
        self.video_preview = VideoPreviewComponent(preview_panel)
        self.video_preview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    
    def load_cuts_data(self):
        """Load cuts data into the interface"""
        self.cuts_list.load_cuts(self.cuts_data)
    
    def on_cut_selected(self, cut_data, index):
        """Handle cut selection from the cuts list"""
        print(f"📝 Cut selected: {cut_data.get('title', 'Unknown')} (Index: {index})")
        
        # Update video preview with selected cut data
        self.video_preview.update_cut_info(cut_data)
    
    def set_mock_data(self):
        """Set mock data for testing"""
        mock_cuts = self.cuts_list.get_mock_cuts_data()
        self.cuts_data = mock_cuts
        self.load_cuts_data()
