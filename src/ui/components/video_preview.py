"""
Video Preview Component
Main Editor - Video Preview and Controls Panel
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class VideoPreviewComponent(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Current selected cut data
        self.selected_cut = None
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the video preview interface"""
        # Video preview area
        self.create_video_preview()
        
        # Timeline area
        self.create_timeline()
        
        # Cut information
        self.create_cut_info()
        
        # Export controls
        self.create_export_controls()
    
    def create_video_preview(self):
        """Create video preview area"""
        preview_frame_style = get_frame_style("card")
        preview_frame = ctk.CTkFrame(self, height=300, **preview_frame_style)
        preview_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_propagate(False)
        
        # Video placeholder
        video_placeholder = ctk.CTkFrame(
            preview_frame,
            fg_color=COLORS["input_bg"],
            corner_radius=8
        )
        video_placeholder.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        video_placeholder.grid_columnconfigure(0, weight=1)
        video_placeholder.grid_rowconfigure(0, weight=1)
        
        # Play icon and text
        play_icon = ctk.CTkLabel(
            video_placeholder,
            text="▶️",
            font=("Segoe UI", 60)
        )
        play_icon.grid(row=0, column=0)
        
        preview_text_style = get_text_style("secondary")
        preview_text = ctk.CTkLabel(
            video_placeholder,
            text="Video Preview\n(Will show selected cut)",
            **preview_text_style
        )
        preview_text.grid(row=1, column=0, pady=(SPACING["sm"], 0))
    
    def create_timeline(self):
        """Create timeline area"""
        timeline_frame_style = get_frame_style("default")
        timeline_frame = ctk.CTkFrame(self, height=80, **timeline_frame_style)
        timeline_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        timeline_frame.grid_columnconfigure(1, weight=1)
        timeline_frame.grid_propagate(False)
        
        # Timeline label
        timeline_label_style = get_text_style("small")
        timeline_label = ctk.CTkLabel(
            timeline_frame,
            text="Timeline:",
            **timeline_label_style
        )
        timeline_label.grid(row=0, column=0, padx=(SPACING["md"], SPACING["sm"]), pady=SPACING["md"], sticky="w")
        
        # Timeline bar placeholder
        timeline_bar = ctk.CTkFrame(
            timeline_frame,
            height=30,
            fg_color=COLORS["input_bg"],
            corner_radius=15
        )
        timeline_bar.grid(row=0, column=1, sticky="ew", padx=(0, SPACING["md"]), pady=SPACING["md"])
        timeline_bar.grid_columnconfigure(0, weight=1)
        
        # Timeline markers placeholder
        markers_frame = ctk.CTkFrame(timeline_bar, fg_color="transparent")
        markers_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["sm"])
        markers_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Start marker
        start_marker = ctk.CTkLabel(
            markers_frame,
            text="│",
            text_color=COLORS["success"],
            font=("Segoe UI", 16, "bold")
        )
        start_marker.grid(row=0, column=0, sticky="w")
        
        # Progress line
        progress_line = ctk.CTkLabel(
            markers_frame,
            text="────────────",
            text_color=COLORS["accent"]
        )
        progress_line.grid(row=0, column=1)
        
        # End marker
        end_marker = ctk.CTkLabel(
            markers_frame,
            text="│",
            text_color=COLORS["error"],
            font=("Segoe UI", 16, "bold")
        )
        end_marker.grid(row=0, column=2, sticky="e")
    
    def create_cut_info(self):
        """Create cut information panel"""
        info_frame_style = get_frame_style("card")
        info_frame = ctk.CTkFrame(self, **info_frame_style)
        info_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        info_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Title
        info_title_style = get_text_style("default")
        info_title = ctk.CTkLabel(
            info_frame,
            text="Cut Information",
            **info_title_style
        )
        info_title.grid(row=0, column=0, columnspan=3, pady=(SPACING["md"], SPACING["sm"]))
        
        # Time information
        self.create_time_info(info_frame)
        
        # Title and description
        self.create_cut_details(info_frame)
    
    def create_time_info(self, parent):
        """Create time information section"""
        # Start time
        start_label_style = get_text_style("small")
        start_label = ctk.CTkLabel(parent, text="Start Time:", **start_label_style)
        start_label.grid(row=1, column=0, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        self.start_time_label = ctk.CTkLabel(
            parent,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["success"]
        )
        self.start_time_label.grid(row=2, column=0, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
        
        # End time
        end_label = ctk.CTkLabel(parent, text="End Time:", **start_label_style)
        end_label.grid(row=1, column=1, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        self.end_time_label = ctk.CTkLabel(
            parent,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["error"]
        )
        self.end_time_label.grid(row=2, column=1, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
        
        # Duration
        duration_label = ctk.CTkLabel(parent, text="Duration:", **start_label_style)
        duration_label.grid(row=1, column=2, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        self.duration_label = ctk.CTkLabel(
            parent,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["accent"]
        )
        self.duration_label.grid(row=2, column=2, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
    
    def create_cut_details(self, parent):
        """Create cut title and description section"""
        # Title entry
        title_label_style = get_text_style("small")
        title_label = ctk.CTkLabel(parent, text="Title:", **title_label_style)
        title_label.grid(row=3, column=0, columnspan=3, padx=SPACING["md"], pady=(SPACING["sm"], SPACING["xs"]), sticky="w")
        
        self.title_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Enter cut title...",
            font=("Segoe UI", 14),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"]
        )
        self.title_entry.grid(row=4, column=0, columnspan=3, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))
        
        # Description entry
        desc_label = ctk.CTkLabel(parent, text="Description:", **title_label_style)
        desc_label.grid(row=5, column=0, columnspan=3, padx=SPACING["md"], pady=(0, SPACING["xs"]), sticky="w")
        
        self.desc_entry = ctk.CTkEntry(
            parent,
            placeholder_text="Enter cut description...",
            font=("Segoe UI", 14),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"]
        )
        self.desc_entry.grid(row=6, column=0, columnspan=3, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
    
    def create_export_controls(self):
        """Create export controls"""
        export_frame = ctk.CTkFrame(self, fg_color="transparent")
        export_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        export_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Export single button
        export_single_style = get_button_style("primary")
        export_single_btn = ctk.CTkButton(
            export_frame,
            text="Export This Cut",
            command=self.on_export_single,
            **export_single_style
        )
        export_single_btn.grid(row=0, column=0, padx=SPACING["sm"], pady=SPACING["sm"])
        
        # Export all button
        export_all_style = get_button_style("success")
        export_all_btn = ctk.CTkButton(
            export_frame,
            text="Export All Cuts",
            command=self.on_export_all,
            **export_all_style
        )
        export_all_btn.grid(row=0, column=1, padx=SPACING["sm"], pady=SPACING["sm"])
        
        # Quality selector placeholder
        quality_btn_style = get_button_style("secondary")
        quality_btn = ctk.CTkButton(
            export_frame,
            text="Quality: Original",
            command=self.on_quality_settings,
            **quality_btn_style
        )
        quality_btn.grid(row=0, column=2, padx=SPACING["sm"], pady=SPACING["sm"])
    
    def update_cut_info(self, cut_data):
        """Update the display with selected cut information"""
        self.selected_cut = cut_data
        
        if cut_data:
            self.start_time_label.configure(text=cut_data.get("start_time", "00:00:00"))
            self.end_time_label.configure(text=cut_data.get("end_time", "00:00:00"))
            self.duration_label.configure(text=cut_data.get("duration", "00:00:00"))
            
            # Update entries
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, cut_data.get("title", ""))
            
            self.desc_entry.delete(0, "end")
            self.desc_entry.insert(0, cut_data.get("description", ""))
    
    # Event handlers (UI only for now)
    def on_export_single(self):
        """Handle export single cut"""
        print(f"🎬 Export single cut: {self.selected_cut.get('title', 'Unknown') if self.selected_cut else 'None'}")
    
    def on_export_all(self):
        """Handle export all cuts"""
        print("🎬 Export all cuts")
    
    def on_quality_settings(self):
        """Handle quality settings"""
        print("⚙️ Quality settings")
