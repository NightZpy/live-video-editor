"""
Cut Times Input Component
Phase 2.2 - Time Loading Interface with real functionality
"""

import customtkinter as ctk
import os
import sys
from tkinter import filedialog, messagebox

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.utils.text_utils import validate_and_parse_cuts_file, format_cuts_preview
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class CutTimesInputComponent(ctk.CTkFrame):
    def __init__(self, parent, on_option_selected=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Callback for when an option is selected
        self.on_option_selected = on_option_selected
        
        # State
        self.is_processing = False
        self.loaded_cuts_data = None
        
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
        
        # Content area
        content_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        
        # Description text
        desc_text_style = get_text_style("secondary")
        desc_text = ctk.CTkLabel(
            content_frame,
            text="Let AI analyze your video\nand suggest optimal cut points",
            **desc_text_style
        )
        desc_text.grid(row=0, column=0, pady=(SPACING["md"], SPACING["sm"]))
        
        # API Key input section
        api_frame = ctk.CTkFrame(content_frame, fg_color=COLORS["input_bg"], corner_radius=6)
        api_frame.grid(row=1, column=0, sticky="ew", pady=SPACING["sm"])
        api_frame.grid_columnconfigure(0, weight=1)
        
        # API Key label
        api_label_style = get_text_style("small")
        api_label = ctk.CTkLabel(
            api_frame,
            text="OpenAI API Key:",
            **api_label_style
        )
        api_label.grid(row=0, column=0, sticky="w", padx=SPACING["sm"], pady=(SPACING["sm"], SPACING["xs"]))
        
        # API Key entry
        self.api_key_entry = ctk.CTkEntry(
            api_frame,
            placeholder_text="sk-...",
            show="*",
            font=("Consolas", 12),
            fg_color=COLORS["secondary"],
            border_color=COLORS["border"],
            border_width=1
        )
        self.api_key_entry.grid(row=1, column=0, sticky="ew", padx=SPACING["sm"], pady=(0, SPACING["sm"]))
        self.api_key_entry.bind("<KeyRelease>", self.on_api_key_change)
        
        # Auto button
        auto_btn_style = get_button_style("success")
        self.auto_btn = ctk.CTkButton(
            content_frame,
            text="Analyze with AI",
            width=140,
            state="disabled",  # Initially disabled
            command=self.on_automatic_analysis,
            **auto_btn_style
        )
        self.auto_btn.grid(row=2, column=0, pady=SPACING["sm"])
        
        # Info
        info_style = get_text_style("small")
        info_label = ctk.CTkLabel(
            option_frame,
            text="Requires valid OpenAI API key",
            **info_style
        )
        info_label.grid(row=3, column=0, pady=(0, SPACING["md"]))
    
    # Event handlers with real functionality
    def on_browse_file(self):
        """Handle browse file button click with real file dialog"""
        if self.is_processing:
            return
            
        file_path = filedialog.askopenfilename(
            title="Select Cut Times File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            self.process_cuts_file(file_path)
    
    def process_cuts_file(self, file_path):
        """Process the selected cuts file"""
        if self.is_processing:
            return
            
        self.is_processing = True
        
        # Update UI to show processing state
        self.update_file_upload_ui("processing")
        
        # Validate and parse file
        is_valid, error_message, cuts_data = validate_and_parse_cuts_file(file_path)
        
        if not is_valid:
            self.is_processing = False
            self.update_file_upload_ui("error", error_message)
            messagebox.showerror("Invalid File", error_message)
            self.reset_file_upload_ui()
            return
        
        if not cuts_data:
            self.is_processing = False
            self.update_file_upload_ui("error", "Could not parse file content")
            messagebox.showerror("Error", "Could not parse file content")
            self.reset_file_upload_ui()
            return
        
        # Success!
        self.loaded_cuts_data = cuts_data
        self.update_file_upload_ui("success")
        
        # Show preview and proceed after delay
        self.after(2000, self.proceed_with_file_data)
    
    def update_file_upload_ui(self, state, message=""):
        """Update file upload UI based on current state"""
        # Find the drop text label (we'll need to store reference to it)
        # For now, we'll just show a message box or update via callback
        if state == "processing":
            print("📂 Processing cut times file...")
        elif state == "success" and self.loaded_cuts_data:
            preview = format_cuts_preview(self.loaded_cuts_data)
            print(f"✅ Cut times loaded successfully!\n{preview}")
        elif state == "error":
            print(f"❌ Error: {message}")
    
    def reset_file_upload_ui(self):
        """Reset file upload UI to initial state"""
        self.after(3000, self._reset_file_upload_elements)
    
    def _reset_file_upload_elements(self):
        """Reset file upload elements to initial state"""
        print("🔄 Resetting file upload UI")
        self.is_processing = False
    
    def proceed_with_file_data(self):
        """Proceed to next phase with loaded file data"""
        if self.on_option_selected and self.loaded_cuts_data:
            self.on_option_selected("file_upload", self.loaded_cuts_data)

    def on_manual_entry(self):
        """Handle manual entry button click"""
        print("✍️ Manual entry selected")
        if self.on_option_selected:
            self.on_option_selected("manual_entry")
    
    def on_automatic_analysis(self):
        """Handle automatic analysis button click"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            print(f"🤖 Automatic analysis selected with API key")
            
            # Get video info from parent
            main_window = self.winfo_toplevel()
            if hasattr(main_window, 'loaded_video_info') and main_window.loaded_video_info:
                video_info = main_window.loaded_video_info
                video_path = video_info.get('file_path')
                
                if video_path:
                    # Show LLM progress dialog
                    from .llm_progress_dialog import show_llm_progress_dialog
                    show_llm_progress_dialog(
                        parent=self.winfo_toplevel(),
                        video_path=video_path,
                        video_info=video_info,
                        api_key=api_key,
                        completion_callback=self.on_llm_analysis_complete
                    )
                else:
                    print("⚠️ Video file path not found in loaded video info")
            else:
                print("⚠️ No video loaded for analysis")
        else:
            print("⚠️ No API key provided")
    
    def on_llm_analysis_complete(self, success: bool, result: dict):
        """Handle completion of LLM analysis"""
        print(f"🎯 Cut times input received LLM completion: success={success}, has_result={result is not None}")
        
        if success and result:
            print("✅ LLM analysis completed successfully")
            print(f"📊 Generated {len(result.get('cuts', []))} cuts")
            print(f"📊 Result structure: {type(result)}")
            print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Pass the complete result to the callback (same format as manual/file input)
            if self.on_option_selected:
                print(f"🎯 Calling on_option_selected callback with automatic_analysis and complete data")
                print(f"🎯 About to advance to main editor with {len(result.get('cuts', []))} cuts")
                self.on_option_selected("automatic_analysis", result)
                print(f"✅ on_option_selected callback completed - should advance to main editor")
            else:
                print(f"⚠️ No on_option_selected callback set")
        else:
            print("❌ LLM analysis failed or was cancelled")
            print(f"❌ Success: {success}, Result: {result}")
    
    def on_api_key_change(self, event):
        """Handle API key input change"""
        api_key = self.api_key_entry.get().strip()
        if len(api_key) >= 10:  # Basic validation
            self.auto_btn.configure(state="normal")
            self.api_key_entry.configure(border_color=COLORS["success"])
        else:
            self.auto_btn.configure(state="disabled")
            self.api_key_entry.configure(border_color=COLORS["border"])
