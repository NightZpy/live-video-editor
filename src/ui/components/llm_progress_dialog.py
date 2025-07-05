"""
LLM Progress Dialog
Shows progress during AI-powered video analysis
"""

import customtkinter as ctk
import tkinter as tk
import queue
import threading
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
    
    def __init__(self, parent, video_path: str, video_info: dict, api_key: Optional[str], completion_callback: Callable):
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
        
        # Thread-safe communication
        self.update_queue = queue.Queue()
        self.completion_queue = queue.Queue()
        
        # Setup dialog
        self.setup_dialog()
        self.create_ui()
        self.start_queue_processing()
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
            print(f"🔄 Dialog starting LLM processing...")
            
            # Test UI updates first
            self.test_ui_updates()
            
            # Create processor
            LLMCutsProcessor = get_llm_processor()
            self.processor = LLMCutsProcessor(self.api_key)
            print(f"🔄 Dialog setting progress callback...")
            self.processor.set_progress_callback(self.on_progress_update)
            
            print(f"🔄 Dialog starting async processing...")
            # Start async processing
            self.processor.process_video_async(
                self.video_path,
                self.video_info,
                self.on_processing_complete
            )
            print(f"🔄 Dialog async processing started")
            
        except Exception as e:
            print(f"❌ Dialog error starting processing: {str(e)}")
            self.on_processing_complete(False, {}, str(e))
    
    def test_ui_updates(self):
        """Test if UI updates work at all"""
        print(f"🧪 Testing UI updates...")
        try:
            # Test immediate update
            self.phase_label.configure(text="Testing UI Updates...")
            self.progress_bar.set(0.1)
            self.progress_label.configure(text="10%")
            self.status_label.configure(text="UI test in progress...")
            self.update_idletasks()
            self.update()
            print(f"🧪 UI test update completed")
            
            # Schedule a reset after 1 second
            def reset_ui():
                self.phase_label.configure(text="Initializing...")
                self.progress_bar.set(0)
                self.progress_label.configure(text="0%")
                self.status_label.configure(text="Starting AI analysis...")
                self.update_idletasks()
                print(f"🧪 UI reset completed")
            
            self.after(1000, reset_ui)
            
        except Exception as e:
            print(f"❌ UI test failed: {str(e)}")
    
    def on_progress_update(self, phase: str, progress: float, message: str):
        """Handle progress updates from processor - THREAD SAFE ONLY"""
        print(f"📊 Dialog received progress update: phase={phase}, progress={progress:.1f}%, message='{message}'")
        
        if self.is_cancelled:
            print(f"⚠️ Dialog ignoring progress update - cancelled")
            return
        
        # Use thread-safe queue instead of direct UI updates
        print(f"📊 Dialog queuing UI update safely...")
        try:
            # Put update in queue - this is thread-safe
            self.update_queue.put((phase, progress, message))
            print(f"📊 Dialog UI update queued successfully")
        except Exception as e:
            print(f"❌ Dialog error queuing UI update: {str(e)}")
            # Do NOT attempt any fallback that touches UI directly
    
    def start_queue_processing(self):
        """Start processing the update queue safely from main thread"""
        print(f"🔄 Starting queue processing timer...")
        self.process_queue()
    
    def process_queue(self):
        """Process pending updates from the queue (main thread only)"""
        try:
            # Process all pending progress updates
            while True:
                try:
                    update_data = self.update_queue.get_nowait()
                    phase, progress, message = update_data
                    print(f"📥 Processing queued update: {phase}, {progress:.1f}%")
                    self._safe_update_ui_progress(phase, progress, message)
                except queue.Empty:
                    break
            
            # Process completion updates
            try:
                completion_data = self.completion_queue.get_nowait()
                success, result, error = completion_data
                print(f"📥 Processing queued completion: success={success}")
                self._handle_completion(success, result, error)
            except queue.Empty:
                pass
                
        except Exception as e:
            print(f"❌ Error processing queue: {str(e)}")
        
        # Schedule next queue check (every 100ms)
        if not self.is_cancelled:
            self.after(100, self.process_queue)
    
    def _safe_update_ui_progress(self, phase: str, progress: float, message: str):
        """THREAD-SAFE UI update method - ONLY call from main thread"""
        print(f"🎨 Dialog SAFELY updating UI: phase={phase}, progress={progress:.1f}%")
        
        if self.is_cancelled:
            print(f"⚠️ Dialog ignoring UI update - cancelled")
            return
        
        try:
            # Check that widgets still exist before updating
            if not hasattr(self, 'phase_label') or not hasattr(self, 'progress_bar'):
                print(f"⚠️ Dialog widgets not available for update")
                return
            
            # Update phase
            phase_text = PROGRESS_PHASES.get(phase, phase.replace("_", " ").title())
            self.phase_label.configure(text=phase_text)
            print(f"🎨 Phase label updated to: {phase_text}")
            
            # Update progress bar CAREFULLY
            progress_fraction = max(0.0, min(1.0, progress / 100.0))  # Clamp between 0 and 1
            self.progress_bar.set(progress_fraction)
            print(f"🎨 Progress bar set to: {progress_fraction:.2f}")
            
            # Update percentage
            self.progress_label.configure(text=f"{progress:.0f}%")
            print(f"🎨 Progress percentage updated to: {progress:.0f}%")
            
            # Update status message
            if message:
                self.status_label.configure(text=message)
                print(f"🎨 Status message updated to: {message}")
            
            # Force UI refresh (this is safe on main thread)
            self.update_idletasks()
            print(f"🎨 UI refresh completed safely")
            
            # Special handling for completion
            if phase == "complete":
                print(f"🎯 Dialog detected completion phase")
                # Don't call on_analysis_complete directly, let completion_queue handle it
                
        except Exception as e:
            print(f"❌ CRITICAL: Error in safe UI update: {str(e)}")
            import traceback
            print(f"❌ Safe UI update traceback: {traceback.format_exc()}")
    
    def _update_ui_progress(self, phase: str, progress: float, message: str):
        """Update UI elements with progress (runs on main thread)"""
        print(f"🎨 Dialog updating UI: phase={phase}, progress={progress:.1f}%")
        
        if self.is_cancelled:
            print(f"⚠️ Dialog ignoring UI update - cancelled")
            return
        
        try:
            # Debug: Check if widgets exist
            print(f"🎨 Checking widgets: phase_label={hasattr(self, 'phase_label')}, progress_bar={hasattr(self, 'progress_bar')}")
            
            # Update phase
            phase_text = PROGRESS_PHASES.get(phase, phase.replace("_", " ").title())
            if hasattr(self, 'phase_label'):
                old_text = self.phase_label.cget("text")
                self.phase_label.configure(text=phase_text)
                new_text = self.phase_label.cget("text")
                print(f"🎨 Phase label: '{old_text}' -> '{new_text}'")
            
            # Update progress bar
            progress_fraction = progress / 100.0
            if hasattr(self, 'progress_bar'):
                old_progress = self.progress_bar.get()
                self.progress_bar.set(progress_fraction)
                new_progress = self.progress_bar.get()
                print(f"🎨 Progress bar: {old_progress:.2f} -> {new_progress:.2f}")
            
            # Update percentage
            if hasattr(self, 'progress_label'):
                old_percent = self.progress_label.cget("text")
                new_percent = f"{progress:.0f}%"
                self.progress_label.configure(text=new_percent)
                print(f"🎨 Progress label: '{old_percent}' -> '{new_percent}'")
            
            # Update status message
            if message and hasattr(self, 'status_label'):
                old_status = self.status_label.cget("text")
                self.status_label.configure(text=message)
                new_status = self.status_label.cget("text")
                print(f"🎨 Status message: '{old_status}' -> '{new_status}'")
            
            # Force multiple types of UI refresh
            print(f"🎨 Forcing UI refresh...")
            self.update_idletasks()  # Process pending idle tasks
            self.update()  # Process all pending events
            print(f"🎨 UI refresh completed")
            
            # Check if values actually changed in UI
            if hasattr(self, 'progress_bar'):
                actual_progress = self.progress_bar.get()
                print(f"🎨 Actual progress bar value after update: {actual_progress:.2f}")
            
            # Special handling for completion
            if phase == "complete":
                print(f"🎯 Dialog detected completion phase, triggering analysis complete")
                self.on_analysis_complete()
                
        except Exception as e:
            print(f"❌ Error updating UI: {str(e)}")
            import traceback
            print(f"❌ UI update traceback: {traceback.format_exc()}")
    
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
        """Handle completion of processing - THREAD SAFE"""
        print(f"🎯 Dialog received processing completion: success={success}, has_result={result is not None}")
        
        if self.is_cancelled:
            print(f"⚠️ Dialog was cancelled, ignoring completion")
            return
        
        # Use thread-safe queue for completion
        print(f"🎯 Dialog queuing completion safely...")
        try:
            self.completion_queue.put((success, result, error))
            print(f"🎯 Dialog completion queued successfully")
        except Exception as e:
            print(f"❌ Dialog error queuing completion: {str(e)}")
    
    def _handle_completion(self, success: bool, result: Optional[Dict], error: Optional[str]):
        """Handle completion on main thread"""
        print(f"🎯 Dialog handling completion on main thread: success={success}")
        
        if self.is_cancelled:
            print(f"⚠️ Dialog was cancelled, ignoring completion")
            return
        
        if success and result:
            # Store result and trigger completion
            print(f"✅ Dialog storing result and triggering completion")
            self.result = result
            self.on_analysis_complete()  # Trigger completion immediately
        else:
            # Show error
            error_msg = error or "Unknown error occurred"
            print(f"❌ Dialog showing error: {error_msg}")
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
def show_llm_progress_dialog(parent, video_path: str, video_info: dict, api_key: Optional[str], completion_callback: Callable):
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
