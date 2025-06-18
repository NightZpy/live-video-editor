"""
Cuts List Component
Main Editor - Left Panel with Cuts List
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class CutsListComponent(ctk.CTkFrame):
    def __init__(self, parent, on_cut_selected=None, video_info=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callback for when a cut is selected
        self.on_cut_selected = on_cut_selected
        self.video_info = video_info
        
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
        """Create a single cut item"""
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
        
        # Thumbnail placeholder
        thumbnail = ctk.CTkFrame(
            cut_frame,
            width=80,
            height=60,
            fg_color=COLORS["input_bg"],
            corner_radius=6
        )
        thumbnail.grid(row=0, column=0, rowspan=3, padx=SPACING["md"], pady=SPACING["md"], sticky="ns")
        thumbnail.grid_propagate(False)
        
        # Thumbnail icon
        thumb_icon = ctk.CTkLabel(
            thumbnail,
            text="🎬",
            font=("Segoe UI", 20)
        )
        thumb_icon.grid(row=0, column=0, sticky="nsew")
        thumb_icon.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
        
        # Cut information
        info_frame = ctk.CTkFrame(cut_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(0, SPACING["md"]), pady=SPACING["sm"])
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_style = get_text_style("default")
        title_label = ctk.CTkLabel(
            info_frame,
            text=cut_data.get("title", f"Cut {index + 1}"),
            **title_style
        )
        title_label.grid(row=0, column=0, sticky="w", pady=(SPACING["sm"], SPACING["xs"]))
        title_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
        
        # Time range
        time_style = get_text_style("small")
        start_time = cut_data.get("start_time", "00:00:00")
        end_time = cut_data.get("end_time", "00:00:00")
        time_label = ctk.CTkLabel(
            info_frame,
            text=f"{start_time} - {end_time}",
            **time_style
        )
        time_label.grid(row=1, column=0, sticky="w", pady=SPACING["xs"])
        time_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
        
        # Duration
        duration = cut_data.get("duration", "00:00:00")
        duration_label = ctk.CTkLabel(
            info_frame,
            text=f"Duration: {duration}",
            **time_style
        )
        duration_label.grid(row=2, column=0, sticky="w", pady=(SPACING["xs"], SPACING["sm"]))
        duration_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
        
        # Status indicator
        status = cut_data.get("status", "ready")
        status_color = COLORS["success"] if status == "ready" else COLORS["warning"]
        status_label = ctk.CTkLabel(
            info_frame,
            text=f"● {status.title()}",
            text_color=status_color,
            font=("Segoe UI", 12)
        )
        status_label.grid(row=0, column=1, sticky="e", pady=(SPACING["sm"], SPACING["xs"]))
        status_label.bind("<Button-1>", lambda e, idx=index: self.select_cut(idx))
    
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
        """Update the cuts counter"""
        count = len(self.cuts_data)
        self.counter_label.configure(text=f"{count} cut{'s' if count != 1 else ''}")
    
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
