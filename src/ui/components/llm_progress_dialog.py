"""
LLM Progress Dialog
Shows progress during AI-powered video analysis
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional, Dict, Any
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

# Import the processor dynamically to avoid circular imports
def get_llm_processor():
    from ...core.llm_cuts_processor import LLMCutsProcessor
    return LLMCutsProcessor

# Progress phases for UI
PROGRESS_PHASES = {
    "extracting_audio": "Extracting Audio...",
    "generating_transcription": "Generating Transcription...", 
    "analyzing_with_ai": "Analyzing with AI...",
    "finalizing": "Finalizing Results...",
    "complete": "Complete!"
}


class LLMProgressDialog(ctk.CTkToplevel):
    """Progress dialog for LLM processing with real-time updates"""
    
    def __init__(self, parent, video_path: str, video_info: dict, api_key: str, completion_callback: Callable):
        super().__init__(parent)
        
        # Store parameters
        self.video_path = video_path
        self.video_info = video_info
        self.api_key = api_key
        self.completion_callback = completion_callback
        
        # Processing state
        self.processor: Optional[Any] = None
        self.is_cancelled = False
        self.is_completed = False
        
        # Setup dialog
        self.setup_dialog()
        self.create_ui()
        self.start_processing()
    
    def setup_dialog(self):
        """Configure dialog window"""
        self.title("AI Video Analysis")
        self.geometry("600x450")  # Increased height to show error messages properly
        self.resizable(True, True)  # Allow resizing to see long error messages
        
        # Center on parent
        if hasattr(self.master, 'winfo_x'):
            parent_x = self.master.winfo_x() + (self.master.winfo_width() // 2) - 300
            parent_y = self.master.winfo_y() + (self.master.winfo_height() // 2) - 225
            self.geometry(f"600x450+{parent_x}+{parent_y}")
        
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Handle close button
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_ui(self):
        """Create the progress interface"""
        # Main frame
        main_frame_style = get_frame_style("card")
        main_frame = ctk.CTkFrame(self, **main_frame_style)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=SPACING["lg"], pady=SPACING["lg"])
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_style = get_text_style("header")
        title_label = ctk.CTkLabel(
            main_frame,
            text="🤖 AI Video Analysis",
            **title_style
        )
        title_label.grid(row=0, column=0, pady=(SPACING["lg"], SPACING["md"]))
        
        # Video info
        video_name = self.video_info.get("filename", "Unknown video")
        video_duration = self.video_info.get("duration", "Unknown")
        
        info_style = get_text_style("secondary")
        info_label = ctk.CTkLabel(
            main_frame,
            text=f"Processing: {video_name}\\nDuration: {video_duration}",
            **info_style
        )
        info_label.grid(row=1, column=0, pady=(0, SPACING["lg"]))
        
        # Current phase label
        phase_style = get_text_style("default")
        self.phase_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            **phase_style
        )
        self.phase_label.grid(row=2, column=0, pady=(0, SPACING["sm"]))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            main_frame,
            width=400,
            height=20,
            progress_color=COLORS["accent"]
        )
        self.progress_bar.grid(row=3, column=0, pady=(0, SPACING["sm"]), padx=SPACING["lg"], sticky="ew")
        self.progress_bar.set(0)
        
        # Progress percentage
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="0%",
            font=("Consolas", 12, "bold"),
            text_color=COLORS["accent"]
        )
        self.progress_label.grid(row=4, column=0, pady=(0, SPACING["lg"]))
        
        # Status message (make it larger for error messages)
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Starting AI analysis...",
            font=("Segoe UI", 11),
            text_color=COLORS["text_secondary"],
            wraplength=550  # Allow text wrapping for long messages
        )
        self.status_label.grid(row=5, column=0, pady=(0, SPACING["lg"]), padx=SPACING["md"], sticky="ew")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, pady=(0, SPACING["lg"]))
        
        # Cancel button (initially visible)
        cancel_style = get_button_style("secondary")
        self.cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            width=100,
            command=self.on_cancel,
            **cancel_style
        )
        self.cancel_btn.grid(row=0, column=0, padx=SPACING["sm"])
        
        # Close button (initially hidden)
        close_style = get_button_style("primary")
        self.close_btn = ctk.CTkButton(
            buttons_frame,
            text="Close",
            width=100,
            command=self.on_close,
            **close_style
        )
        # Don't grid it yet - will show when complete
    
    def start_processing(self):
        """Start the LLM processing"""
        try:
            # Create processor
            LLMCutsProcessor = get_llm_processor()
            self.processor = LLMCutsProcessor(self.api_key)
            self.processor.set_progress_callback(self.on_progress_update)
            
            # Start async processing
            self.processor.process_video_async(
                self.video_path,
                self.video_info,
                self.on_processing_complete
            )
            
        except Exception as e:
            self.on_processing_complete(False, {}, str(e))
    
    def on_progress_update(self, phase: str, progress: float, message: str):
        """Handle progress updates from processor"""
        if self.is_cancelled:
            return
        
        # Update UI on main thread
        self.after(0, self._update_ui_progress, phase, progress, message)
    
    def _update_ui_progress(self, phase: str, progress: float, message: str):
        """Update UI elements with progress (runs on main thread)"""
        if self.is_cancelled:
            return
        
        # Update phase
        phase_text = PROGRESS_PHASES.get(phase, phase.replace("_", " ").title())
        self.phase_label.configure(text=phase_text)
        
        # Update progress bar
        progress_fraction = progress / 100.0
        self.progress_bar.set(progress_fraction)
        
        # Update percentage
        self.progress_label.configure(text=f"{progress:.0f}%")
        
        # Update status message
        if message:
            self.status_label.configure(text=message)
        
        # Special handling for completion
        if phase == "complete":
            self.on_analysis_complete()
    
    def on_analysis_complete(self):
        """Handle successful completion of analysis"""
        self.is_completed = True
        
        # Update UI for completion
        self.phase_label.configure(
            text="✅ Analysis Complete!",
            text_color=COLORS["success"]
        )
        self.status_label.configure(text="AI has successfully analyzed your video and generated cuts.")
        
        # Hide cancel button, show close button
        self.cancel_btn.grid_remove()
        self.close_btn.grid(row=0, column=0, padx=SPACING["sm"])
        
        # Auto-close after 2 seconds
        self.after(2000, self.auto_close)
    
    def auto_close(self):
        """Auto-close dialog and proceed to main editor"""
        if not self.is_cancelled:
            self.on_close()
    
    def on_processing_complete(self, success: bool, result: Optional[Dict], error: Optional[str]):
        """Handle completion of processing"""
        if self.is_cancelled:
            return
        
        # Schedule UI update on main thread
        self.after(0, self._handle_completion, success, result, error)
    
    def _handle_completion(self, success: bool, result: Optional[Dict], error: Optional[str]):
        """Handle completion on main thread"""
        if self.is_cancelled:
            return
        
        if success and result:
            # Store result and let the progress complete naturally
            self.result = result
        else:
            # Show error
            error_msg = error or "Unknown error occurred"
            self.show_error(error_msg)
    
    def show_error(self, error_message: str):
        """Show error state"""
        print(f"❌ Dialog showing error: {error_message}")
        
        self.phase_label.configure(
            text="❌ Analysis Failed",
            text_color=COLORS["error"]
        )
        
        # Show full error message without truncation
        self.status_label.configure(
            text=f"Error: {error_message}",
            text_color=COLORS["error"],
            wraplength=550  # Allow wrapping for long error messages
        )
        self.progress_bar.configure(progress_color=COLORS["error"])
        
        # Hide cancel button, show close button
        self.cancel_btn.grid_remove()
        self.close_btn.grid(row=0, column=0, padx=SPACING["sm"])
    
    def on_cancel(self):
        """Handle cancel button"""
        if self.is_completed:
            self.on_close()
            return
        
        self.is_cancelled = True
        
        # Cancel processor
        if self.processor:
            self.processor.cancel_processing()
        
        # Update UI
        self.phase_label.configure(
            text="⏹️ Cancelling...",
            text_color=COLORS["warning"]
        )
        self.status_label.configure(text="Cancelling analysis...")
        self.cancel_btn.configure(state="disabled")
        
        # Close after short delay
        self.after(1000, self.destroy)
    
    def on_close(self):
        """Handle close button - proceed with results"""
        if hasattr(self, 'result') and self.result:
            # Call completion callback with results
            self.completion_callback(True, self.result)
        else:
            # Call completion callback with cancellation
            self.completion_callback(False, None)
        
        self.destroy()


# Convenience function for easy usage
def show_llm_progress_dialog(parent, video_path: str, video_info: dict, api_key: str, completion_callback: Callable):
    """
    Show LLM progress dialog
    
    Args:
        parent: Parent window
        video_path: Path to video file
        video_info: Video metadata
        api_key: OpenAI API key
        completion_callback: Function to call when complete (success: bool, result: dict)
    """
    dialog = LLMProgressDialog(parent, video_path, video_info, api_key, completion_callback)
    return dialog
