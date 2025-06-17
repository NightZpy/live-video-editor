"""
Cut Times Input Component
Phase 2.2 - Time Loading Interface UI
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class CutTimesInputComponent(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the cut times input interface"""
        # Title section
        self.create_title_section()
        
        # Main content area
        self.create_content_area()
    
    def create_title_section(self):
        """Create title and description"""
        title_frame_style = get_frame_style("card")
        title_frame = ctk.CTkFrame(self, height=100, **title_frame_style)
        title_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["lg"])
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_propagate(False)
        
        # Title
        title_style = get_text_style("header")
        title_label = ctk.CTkLabel(
            title_frame,
            text="Define Cut Times",
            **title_style
        )
        title_label.grid(row=0, column=0, pady=(SPACING["md"], SPACING["xs"]))
        
        # Description
        desc_style = get_text_style("secondary")
        desc_label = ctk.CTkLabel(
            title_frame,
            text="Choose how to define the timestamps for your video cuts",
            **desc_style
        )
        desc_label.grid(row=1, column=0, pady=(0, SPACING["md"]))
    
    def create_content_area(self):
        """Create the main content with three options"""
        content_frame_style = get_frame_style("default")
        content_frame = ctk.CTkFrame(self, **content_frame_style)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))
        content_frame.grid_columnconfigure((0, 1, 2), weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Three options side by side
        self.create_file_upload_option(content_frame, 0)
        self.create_manual_option(content_frame, 1)
        self.create_automatic_option(content_frame, 2)
    
    def create_file_upload_option(self, parent, column):
        """Create file upload drag & drop area"""
        option_frame_style = get_frame_style("card")
        option_frame = ctk.CTkFrame(parent, **option_frame_style)
        option_frame.grid(row=1, column=column, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure(2, weight=1)
        
        # Icon
        icon_style = get_text_style("header")
        icon_label = ctk.CTkLabel(
            option_frame,
            text="📄",
            font=("Segoe UI", 40)
        )
        icon_label.grid(row=0, column=0, pady=(SPACING["lg"], SPACING["sm"]))
        
        # Title
        title_style = get_text_style("default")
        title_label = ctk.CTkLabel(
            option_frame,
            text="Upload File",
            **title_style
        )
        title_label.grid(row=1, column=0, pady=SPACING["xs"])
        
        # Drag & drop area
        drop_frame_style = get_frame_style("default")
        drop_frame = ctk.CTkFrame(
            option_frame,
            fg_color=COLORS["input_bg"],
            border_width=2,
            border_color=COLORS["border"],
            corner_radius=8
        )
        drop_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        drop_frame.grid_columnconfigure(0, weight=1)
        drop_frame.grid_rowconfigure(0, weight=1)
        
        # Drop area content
        drop_content_frame = ctk.CTkFrame(drop_frame, fg_color="transparent")
        drop_content_frame.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        drop_content_frame.grid_columnconfigure(0, weight=1)
        
        # Drop text
        drop_text_style = get_text_style("secondary")
        drop_text = ctk.CTkLabel(
            drop_content_frame,
            text="Drag & drop your\ntimestamps file here\n\n(.txt format)",
            **drop_text_style
        )
        drop_text.grid(row=0, column=0, pady=SPACING["md"])
        
        # Browse button
        browse_btn_style = get_button_style("secondary")
        browse_btn = ctk.CTkButton(
            drop_content_frame,
            text="Browse File",
            width=120,
            command=self.on_browse_file,
            **browse_btn_style
        )
        browse_btn.grid(row=1, column=0, pady=(SPACING["sm"], SPACING["md"]))
        
        # Format info
        format_info_style = get_text_style("small")
        format_info = ctk.CTkLabel(
            option_frame,
            text="Format: hh:mm:ss - hh:mm:ss - title - description",
            **format_info_style
        )
        format_info.grid(row=3, column=0, pady=(0, SPACING["md"]))
    
    def create_manual_option(self, parent, column):
        """Create manual input option"""
        option_frame_style = get_frame_style("card")
        option_frame = ctk.CTkFrame(parent, **option_frame_style)
        option_frame.grid(row=1, column=column, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure(2, weight=1)
        
        # Icon
        icon_label = ctk.CTkLabel(
            option_frame,
            text="✍️",
            font=("Segoe UI", 40)
        )
        icon_label.grid(row=0, column=0, pady=(SPACING["lg"], SPACING["sm"]))
        
        # Title
        title_style = get_text_style("default")
        title_label = ctk.CTkLabel(
            option_frame,
            text="Manual Entry",
            **title_style
        )
        title_label.grid(row=1, column=0, pady=SPACING["xs"])
        
        # Description area
        desc_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
        desc_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        desc_frame.grid_columnconfigure(0, weight=1)
        desc_frame.grid_rowconfigure(0, weight=1)
        
        # Description text
        desc_text_style = get_text_style("secondary")
        desc_text = ctk.CTkLabel(
            desc_frame,
            text="Type your timestamps\ndirectly into a text area\n\nPerfect for custom\ncut sequences",
            **desc_text_style
        )
        desc_text.grid(row=0, column=0, pady=SPACING["md"])
        
        # Manual button
        manual_btn_style = get_button_style("primary")
        manual_btn = ctk.CTkButton(
            desc_frame,
            text="Enter Manually",
            width=140,
            command=self.on_manual_entry,
            **manual_btn_style
        )
        manual_btn.grid(row=1, column=0, pady=SPACING["sm"])
        
        # Format info
        format_info_style = get_text_style("small")
        format_info = ctk.CTkLabel(
            option_frame,
            text="One timestamp per line",
            **format_info_style
        )
        format_info.grid(row=3, column=0, pady=(0, SPACING["md"]))
    
    def create_automatic_option(self, parent, column):
        """Create automatic LLM option"""
        option_frame_style = get_frame_style("card")
        option_frame = ctk.CTkFrame(parent, **option_frame_style)
        option_frame.grid(row=1, column=column, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure(2, weight=1)
        
        # Icon
        icon_label = ctk.CTkLabel(
            option_frame,
            text="🤖",
            font=("Segoe UI", 40)
        )
        icon_label.grid(row=0, column=0, pady=(SPACING["lg"], SPACING["sm"]))
        
        # Title
        title_style = get_text_style("default")
        title_label = ctk.CTkLabel(
            option_frame,
            text="AI Automatic",
            **title_style
        )
        title_label.grid(row=1, column=0, pady=SPACING["xs"])
        
        # Description area
        desc_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
        desc_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        desc_frame.grid_columnconfigure(0, weight=1)
        desc_frame.grid_rowconfigure(0, weight=1)
        
        # Description text
        desc_text_style = get_text_style("secondary")
        desc_text = ctk.CTkLabel(
            desc_frame,
            text="Let AI analyze your video\nand suggest optimal\ncut points automatically\n\nPowered by LLM",
            **desc_text_style
        )
        desc_text.grid(row=0, column=0, pady=SPACING["md"])
        
        # Auto button
        auto_btn_style = get_button_style("success")
        auto_btn = ctk.CTkButton(
            desc_frame,
            text="Analyze with AI",
            width=140,
            command=self.on_automatic_analysis,
            **auto_btn_style
        )
        auto_btn.grid(row=1, column=0, pady=SPACING["sm"])
        
        # Info
        info_style = get_text_style("small")
        info_label = ctk.CTkLabel(
            option_frame,
            text="Requires API key configuration",
            **info_style
        )
        info_label.grid(row=3, column=0, pady=(0, SPACING["md"]))
    
    # Event handlers (UI only for now)
    def on_browse_file(self):
        """Handle browse file button click"""
        print("Browse file clicked - UI only")
    
    def on_manual_entry(self):
        """Handle manual entry button click"""
        print("Manual entry clicked - UI only")
    
    def on_automatic_analysis(self):
        """Handle automatic analysis button click"""
        print("Automatic analysis clicked - UI only")
