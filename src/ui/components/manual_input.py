"""
Manual Input Component
Phase 2.3 - Manual Time Entry Interface
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class ManualInputComponent(ctk.CTkFrame):
    def __init__(self, parent, on_process_complete=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callback for when processing is complete
        self.on_process_complete = on_process_complete
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the manual input interface"""
        # Title section
        self.create_title_section()
        
        # Input area
        self.create_input_area()
        
        # Action buttons
        self.create_action_buttons()
    
    def create_title_section(self):
        """Create title and instructions"""
        title_frame_style = get_frame_style("card")
        title_frame = ctk.CTkFrame(self, height=120, **title_frame_style)
        title_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["lg"])
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_propagate(False)
        
        # Title
        title_style = get_text_style("header")
        title_label = ctk.CTkLabel(
            title_frame,
            text="Manual Time Entry",
            **title_style
        )
        title_label.grid(row=0, column=0, pady=(SPACING["md"], SPACING["xs"]))
        
        # Description
        desc_style = get_text_style("secondary")
        desc_label = ctk.CTkLabel(
            title_frame,
            text="Enter your cut timestamps manually, one per line",
            **desc_style
        )
        desc_label.grid(row=1, column=0, pady=SPACING["xs"])
        
        # Format info
        format_style = get_text_style("small")
        format_label = ctk.CTkLabel(
            title_frame,
            text="Format: hh:mm:ss - hh:mm:ss - title - description",
            **format_style
        )
        format_label.grid(row=2, column=0, pady=(SPACING["xs"], SPACING["md"]))
    
    def create_input_area(self):
        """Create the text input area"""
        input_frame_style = get_frame_style("default")
        input_frame = ctk.CTkFrame(self, **input_frame_style)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)
        
        # Text area with placeholder
        placeholder_text = """00:00:30 - 00:02:15 - Introduction - Welcome message and overview
00:02:15 - 00:05:30 - Main Topic - Core content explanation
00:05:30 - 00:08:45 - Examples - Practical demonstrations
00:08:45 - 00:10:00 - Conclusion - Summary and closing remarks

Enter your timestamps here..."""
        
        self.text_area = ctk.CTkTextbox(
            input_frame,
            font=("Consolas", 14),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=8
        )
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        
        # Insert placeholder text
        self.text_area.insert("1.0", placeholder_text)
        self.text_area.bind("<FocusIn>", self.on_text_focus_in)
        self.text_area.bind("<KeyPress>", self.on_text_change)
        
        # Track if placeholder is active
        self.placeholder_active = True
    
    def create_action_buttons(self):
        """Create action buttons"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Back button
        back_btn_style = get_button_style("secondary")
        back_btn = ctk.CTkButton(
            button_frame,
            text="← Back",
            width=120,
            command=self.on_back,
            **back_btn_style
        )
        back_btn.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="w")
        
        # Clear button
        clear_btn_style = get_button_style("warning")
        clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear All",
            width=120,
            command=self.on_clear,
            **clear_btn_style
        )
        clear_btn.grid(row=0, column=1, padx=SPACING["md"], pady=SPACING["md"])
        
        # Process button
        process_btn_style = get_button_style("primary")
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="Process Timestamps",
            width=160,
            command=self.on_process,
            **process_btn_style
        )
        self.process_btn.grid(row=0, column=2, padx=SPACING["md"], pady=SPACING["md"], sticky="e")
    
    def on_text_focus_in(self, event):
        """Handle text area focus in - clear placeholder"""
        if self.placeholder_active:
            self.text_area.delete("1.0", "end")
            self.text_area.configure(text_color=COLORS["text"])
            self.placeholder_active = False
    
    def on_text_change(self, event):
        """Handle text change - update button state"""
        # Simple validation - check if there's content
        content = self.text_area.get("1.0", "end").strip()
        if content and not self.placeholder_active:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")
    
    def on_back(self):
        """Handle back button"""
        if self.on_process_complete:
            self.on_process_complete("back", None)
    
    def on_clear(self):
        """Handle clear button"""
        self.text_area.delete("1.0", "end")
        self.placeholder_active = False
        self.process_btn.configure(state="disabled")
    
    def on_process(self):
        """Handle process button"""
        content = self.text_area.get("1.0", "end").strip()
        if content and not self.placeholder_active:
            # Simulate processing
            self.process_btn.configure(text="Processing...", state="disabled")
            
            # Simulate delay and complete
            self.after(2000, lambda: self._complete_processing(content))
    
    def _complete_processing(self, content):
        """Complete the processing simulation"""
        print(f"📝 Processing manual timestamps:\n{content}")
        
        if self.on_process_complete:
            # Simulate parsed data
            mock_data = {
                "method": "manual",
                "raw_content": content,
                "cuts_count": len([line for line in content.split('\n') if line.strip()])
            }
            self.on_process_complete("complete", mock_data)
