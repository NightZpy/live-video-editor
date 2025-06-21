"""
Cuts List Component
Main Editor - Left Panel with Cuts List
"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class CutsListComponent(ctk.CTkFrame):
    def __init__(self, parent, on_cut_selected=None, video_info=None, thumbnail_cache=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callback for when a cut is selected
        self.on_cut_selected = on_cut_selected
        self.video_info = video_info
        self.thumbnail_cache = thumbnail_cache
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Cuts data and selection
        self.cuts_data = []
        self.selected_cut_id = None
        self.cut_widgets = []
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the cuts list interface"""
        # Header
        self.create_header()
        
        # Scrollable cuts list
        self.create_cuts_list()
    
    def create_header(self):
        """Create header with title and counter"""
        header_frame_style = get_frame_style("card")
        header_frame = ctk.CTkFrame(self, height=80, **header_frame_style)
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_propagate(False)
        
        # Title
        title_style = get_text_style("header")
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Video Cuts",
            **title_style
        )
        self.title_label.grid(row=0, column=0, pady=(SPACING["md"], SPACING["xs"]))
        
        # Video info (if available)
        if self.video_info:
            video_name = self.video_info.get('filename', 'Unknown video')
            video_duration = self.video_info.get('duration', 'Unknown duration')
            video_info_text = f"📹 {video_name} • {video_duration}"
            
            video_info_style = get_text_style("small")
            video_info_label = ctk.CTkLabel(
                header_frame,
                text=video_info_text,
                **video_info_style
            )
            video_info_label.grid(row=1, column=0, pady=SPACING["xs"])
        
        # Counter
        counter_style = get_text_style("secondary")
        self.counter_label = ctk.CTkLabel(
            header_frame,
            text="0 cuts",
            **counter_style
        )
        counter_row = 2 if self.video_info else 1
        self.counter_label.grid(row=counter_row, column=0, pady=(SPACING["xs"], SPACING["sm"]))
    
    def create_cuts_list(self):
        """Create scrollable cuts list"""
        # Scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["secondary"],
            corner_radius=8
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
    
    def load_cuts(self, cuts_data):
        """Load cuts data and create UI elements"""
        self.cuts_data = cuts_data
        self.clear_cuts_list()
        
        for i, cut in enumerate(cuts_data):
            self.create_cut_item(cut, i)
        
        # Update counter
        self.update_counter()
        
        # Select first cut by default
        if cuts_data:
            self.select_cut(0)
    
    def clear_cuts_list(self):
        """Clear all cut items from the list"""
        for widget in self.cut_widgets:
            widget.destroy()
        self.cut_widgets.clear()
    
    def create_cut_item(self, cut_data, index):
        """Create a single cut item with enhanced information display"""
        # Main cut frame
        cut_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color=COLORS["primary"],
            corner_radius=8,
            border_width=2,
            border_color=COLORS["border"]
        )
        cut_frame.grid(row=index, column=0, sticky="ew", padx=SPACING["sm"], pady=SPACING["sm"])
        cut_frame.grid_columnconfigure(1, weight=1)

        # Store reference and add click binding
        self.cut_widgets.append(cut_frame)
        cut_frame.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))

        # Thumbnail with real video frame
        thumbnail = ctk.CTkFrame(
            cut_frame,
            width=80,
            height=60,
            fg_color=COLORS["input_bg"],
            corner_radius=6
        )
        thumbnail.grid(row=0, column=0, rowspan=3, padx=SPACING["md"], pady=SPACING["md"], sticky="ns")
        thumbnail.grid_propagate(False)

        # Try to get real video thumbnail
        thumbnail_image = None
        if self.thumbnail_cache:
            start_time = cut_data.get("start_time", cut_data.get("start", "00:00:00"))
            thumbnail_image = self.thumbnail_cache.get_thumbnail(start_time)

        if thumbnail_image:
            try:
                # Resize original frame to thumbnail size (80x60)
                thumbnail_resized = thumbnail_image.resize((80, 60), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(thumbnail_resized)
                thumb_label = tk.Label(
                    thumbnail,
                    image=photo_image,
                    bg=COLORS["input_bg"],
                    bd=0,
                    highlightthickness=0
                )
                # Store reference to prevent garbage collection
                if not hasattr(self, '_photo_images'):
                    self._photo_images = []
                self._photo_images.append(photo_image)
                thumb_label.place(relx=0.5, rely=0.5, anchor="center")
                thumb_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
            except Exception as e:
                print(f"⚠️ Error displaying thumbnail: {e}")
                self._create_fallback_thumbnail_icon(thumbnail, cut_data, index)
        else:
            self._create_fallback_thumbnail_icon(thumbnail, cut_data, index)

        # Cut information
        info_frame = ctk.CTkFrame(cut_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(0, SPACING["md"]), pady=SPACING["sm"])
        info_frame.grid_columnconfigure(0, weight=1)

        # Title with type icon as prefix
        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(SPACING["sm"], SPACING["xs"]))
        title_frame.grid_columnconfigure(0, weight=1)

        title_style = get_text_style("default")
        # Get icon for type
        content_type = cut_data.get("content_type", "unknown")
        cut_type = cut_data.get("type", self._map_content_type_to_type(content_type))
        if cut_type == "major_theme":
            thumb_icon_text = "📚"
        elif cut_type == "thematic_segment":
            thumb_icon_text = "📖"
        elif cut_type == "standard_clip":
            thumb_icon_text = "🎬"
        elif cut_type == "quick_insight":
            thumb_icon_text = "⚡"
        else:
            thumb_icon_text = "🎥"
        # Title with icon prefix
        title_with_icon = f"{thumb_icon_text} {cut_data.get('title', f'Cut {index + 1}') }"
        title_label = ctk.CTkLabel(
            title_frame,
            text=title_with_icon,
            **title_style
        )
        title_label.grid(row=0, column=0, sticky="w")
        title_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))

        # Type badge (opcional, solo para algunos tipos)
        if cut_type in ["major_theme", "highlight_clip"]:
            badge_text = "THEME" if cut_type == "major_theme" else "CLIP"
            badge_color = COLORS["accent"] if cut_type == "major_theme" else COLORS["accent"]
            type_badge = ctk.CTkLabel(
                title_frame,
                text=badge_text,
                font=("Segoe UI", 9, "bold"),
                text_color="white",
                fg_color=badge_color,
                corner_radius=3,
                width=50,
                height=18
            )
            type_badge.grid(row=0, column=1, sticky="e", padx=(SPACING["sm"], 0))
            type_badge.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))

    def _create_fallback_thumbnail_icon(self, parent, cut_data, index):
        """Fallback: show icon in thumbnail area if no real frame available"""
        content_type = cut_data.get("content_type", "unknown")
        cut_type = cut_data.get("type", self._map_content_type_to_type(content_type))
        if cut_type == "major_theme":
            thumb_icon_text = "📚"
        elif cut_type == "thematic_segment":
            thumb_icon_text = "📖"
        elif cut_type == "standard_clip":
            thumb_icon_text = "🎬"
        elif cut_type == "quick_insight":
            thumb_icon_text = "⚡"
        else:
            thumb_icon_text = "🎥"
        icon_label = ctk.CTkLabel(
            parent,
            text=thumb_icon_text,
            font=("Segoe UI", 28),
            text_color=COLORS["text_secondary"]
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        icon_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
    
    def select_cut(self, index):
        """Select a cut and update visual feedback"""
        if 0 <= index < len(self.cuts_data):
            # Update selection
            self.selected_cut_id = index
            
            # Update visual feedback
            self.update_selection_visual()
            
            # Notify parent
            if self.on_cut_selected:
                self.on_cut_selected(self.cuts_data[index], index)
    
    def update_selection_visual(self):
        """Update visual feedback for selected cut"""
        for i, widget in enumerate(self.cut_widgets):
            if i == self.selected_cut_id:
                # Selected state
                widget.configure(
                    border_color=COLORS["accent"],
                    border_width=3,
                    fg_color=COLORS["hover"]
                )
            else:
                # Unselected state
                widget.configure(
                    border_color=COLORS["border"],
                    border_width=2,
                    fg_color=COLORS["primary"]
                )
    
    def update_counter(self):
        """Update the cuts counter with type breakdown"""
        total_count = len(self.cuts_data)
        
        # Count by type
        theme_count = len([cut for cut in self.cuts_data if cut.get("type") == "major_theme"])
        clip_count = len([cut for cut in self.cuts_data if cut.get("type") == "highlight_clip"])
        
        # Count by social media value
        high_value_count = len([cut for cut in self.cuts_data if cut.get("social_media_value") == "high"])
        
        if total_count == 0:
            counter_text = "No cuts available"
        else:
            # Build counter text with breakdown
            counter_parts = [f"{total_count} total"]
            
            if theme_count > 0:
                counter_parts.append(f"{theme_count} themes")
            if clip_count > 0:
                counter_parts.append(f"{clip_count} clips")
            if high_value_count > 0:
                counter_parts.append(f"{high_value_count} high-value")
                
            counter_text = " • ".join(counter_parts)
        
        self.counter_label.configure(text=counter_text)
    
    def _map_content_type_to_type(self, content_type: str) -> str:
        """
        Map content_type from JSON data to internal type system
        
        Args:
            content_type: The content_type from JSON (e.g., "topic_segment", "concept_explanation")
            
        Returns:
            Internal type string (e.g., "major_theme", "thematic_segment")
        """
        content_type_mapping = {
            "topic_segment": "thematic_segment",
            "concept_explanation": "standard_clip", 
            "key_moment": "quick_insight",
            "major_discussion": "major_theme",  # Map major discussions as themes
            "major_theme": "major_theme",
            "thematic_segment": "thematic_segment",
            "standard_clip": "standard_clip",
            "quick_insight": "quick_insight",
            "highlight_clip": "standard_clip"
        }
        
        return content_type_mapping.get(content_type, "standard_clip")

    def get_mock_cuts_data(self):
        """Generate mock cuts data for testing"""
        return [
            {
                "id": 1,
                "title": "Introduction",
                "description": "Welcome message and overview",
                "start_time": "00:00:30",
                "end_time": "00:02:15",
                "duration": "00:01:45",
                "status": "ready"
            },
            {
                "id": 2,
                "title": "Main Topic",
                "description": "Core content explanation",
                "start_time": "00:02:15",
                "end_time": "00:05:30",
                "duration": "00:03:15",
                "status": "ready"
            },
            {
                "id": 3,
                "title": "Examples",
                "description": "Practical demonstrations",
                "start_time": "00:05:30",
                "end_time": "00:08:45",
                "duration": "00:03:15",
                "status": "ready"
            },
            {
                "id": 4,
                "title": "Conclusion",
                "description": "Summary and closing remarks",
                "start_time": "00:08:45",
                "end_time": "00:10:00",
                "duration": "00:01:15",
                "status": "processing"
            }
        ]
