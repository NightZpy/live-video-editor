"""
Progress Dialog Component
Real-time progress tracking for video export operations
"""

import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from typing import Optional, Dict, List
from pathlib import Path
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING
from ...core.video_processor import ThreadedVideoProcessor, VideoExportProgress


class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, video_path: str = "", cut_data: Optional[Dict] = None, 
                 cuts_data: Optional[List[Dict]] = None, output_dir: str = "", 
                 quality: str = "original", **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.video_path = video_path
        self.cut_data = cut_data  # For single export
        self.cuts_data = cuts_data  # For batch export
        self.output_dir = output_dir or str(Path.home() / "Downloads")
        self.quality = quality
        
        # Determine export type
        self.export_type = "single" if cut_data else "batch"
        self.total_files = 1 if self.export_type == "single" else len(cuts_data or [])
        
        # Initialize video processor - use synchronous version for now to avoid segfault
        from ...core.video_processor import VideoProcessor
        self.processor = VideoProcessor()
        self.processor.set_progress_callback(self.update_progress)
        self.processor.set_completion_callback(self.export_completed)
        
        # UI state
        self.is_completed = False
        self.is_cancelled = False
        
        # Configure window
        self.setup_window()
        
        # Setup UI
        self.setup_ui()
        
        # Select output directory before starting
        self.select_output_directory()

    def setup_window(self):
        """Configure the progress window"""
        title = f"Exporting {'1 Cut' if self.export_type == 'single' else f'{self.total_files} Cuts'}"
        self.title(title)
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Center on parent
        self.center_on_parent()
        
        # Make modal
        self.grab_set()
        self.focus_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close_window)

    def center_on_parent(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (250)
        y = parent_y + (parent_height // 2) - (175)
        
        self.geometry(f"500x350+{x}+{y}")

    def setup_ui(self):
        """Setup the progress dialog UI"""
        # Header section
        self.create_header()
        
        # Progress section
        self.create_progress_section()
        
        # Controls section
        self.create_controls()

    def create_header(self):
        """Create the header with title and icon"""
        header_frame_style = get_frame_style("card")
        header_frame = ctk.CTkFrame(self, height=80, **header_frame_style)
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["lg"])
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_propagate(False)
        
        # Icon
        icon_label = ctk.CTkLabel(
            header_frame,
            text="🎬",
            font=("Segoe UI", 32)
        )
        icon_label.grid(row=0, column=0, padx=SPACING["lg"], pady=SPACING["md"])
        
        # Title and subtitle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_style = get_text_style("header")
        title_text = "Export Video Cut" if self.export_type == "single" else f"Export {self.total_files} Video Cuts"
        self.title_label = ctk.CTkLabel(title_frame, text=title_text, **title_style)
        self.title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_style = get_text_style("small")
        self.subtitle_label = ctk.CTkLabel(
            title_frame, 
            text="Preparing export...", 
            **subtitle_style
        )
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(SPACING["xs"], 0))

    def create_progress_section(self):
        """Create the progress display section"""
        progress_frame_style = get_frame_style("card")
        progress_frame = ctk.CTkFrame(self, **progress_frame_style)
        progress_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            progress_color=COLORS["accent"]
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=SPACING["lg"], pady=SPACING["lg"])
        self.progress_bar.set(0)
        
        # Progress percentage
        self.percentage_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=("Segoe UI", 18, "bold"),
            text_color=COLORS["accent"]
        )
        self.percentage_label.grid(row=1, column=0, pady=(0, SPACING["md"]))
        
        # Current file being processed
        self.current_file_label = ctk.CTkLabel(
            progress_frame,
            text="Initializing...",
            font=("Segoe UI", 14),
            text_color=COLORS["text"]
        )
        self.current_file_label.grid(row=2, column=0, pady=(0, SPACING["sm"]))
        
        # File counter
        self.file_counter_label = ctk.CTkLabel(
            progress_frame,
            text=f"File 0 of {self.total_files}",
            font=("Segoe UI", 12),
            text_color=COLORS["text_secondary"]
        )
        self.file_counter_label.grid(row=3, column=0, pady=(0, SPACING["sm"]))
        
        # Time estimate
        self.time_estimate_label = ctk.CTkLabel(
            progress_frame,
            text="Calculating time remaining...",
            font=("Segoe UI", 12),
            text_color=COLORS["text_secondary"]
        )
        self.time_estimate_label.grid(row=4, column=0, pady=(0, SPACING["lg"]))

    def create_controls(self):
        """Create control buttons"""
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))
        controls_frame.grid_columnconfigure(0, weight=1)
        
        # Cancel button
        cancel_btn_style = get_button_style("secondary")
        self.cancel_btn = ctk.CTkButton(
            controls_frame,
            text="Cancel",
            width=120,
            command=self.on_cancel,
            **cancel_btn_style
        )
        self.cancel_btn.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"])

    def select_output_directory(self):
        """Let user select output directory before starting export"""
        # Ask user to select output directory
        selected_dir = filedialog.askdirectory(
            title="Select Export Directory",
            initialdir=self.output_dir
        )
        
        if selected_dir:
            self.output_dir = selected_dir
            self.start_export()
        else:
            # User cancelled directory selection
            self.on_close_window()

    def start_export(self):
        """Start the export process"""
        try:
            if self.export_type == "single" and self.cut_data:
                print(f"🎬 Starting single cut export...")
                print(f"Video: {self.video_path}")
                print(f"Cut data: {self.cut_data}")
                print(f"Output dir: {self.output_dir}")
                
                # Run export synchronously but with UI updates
                self.after(100, self.run_single_export)
            
            elif self.export_type == "batch" and self.cuts_data:
                print(f"🎬 Starting batch export...")
                print(f"Video: {self.video_path}")
                print(f"Cuts count: {len(self.cuts_data)}")
                print(f"Output dir: {self.output_dir}")
                
                # Run export synchronously but with UI updates
                self.after(100, self.run_batch_export)
            else:
                messagebox.showerror("Error", "No valid export data provided")
                self.on_close_window()
                
        except Exception as e:
            print(f"❌ Error starting export: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export Error", f"Failed to start export: {str(e)}")
            self.on_close_window()
    
    def run_single_export(self):
        """Run single export synchronously"""
        try:
            success = self.processor.export_single_cut(
                self.video_path,
                self.cut_data,
                self.output_dir,
                self.quality
            )
            if success:
                print("✅ Single export completed successfully")
            else:
                print("❌ Single export failed")
        except Exception as e:
            print(f"❌ Error in single export: {e}")
            import traceback
            traceback.print_exc()
    
    def run_batch_export(self):
        """Run batch export synchronously"""
        try:
            success = self.processor.export_batch_cuts(
                self.video_path,
                self.cuts_data,
                self.output_dir,
                self.quality
            )
            if success:
                print("✅ Batch export completed successfully")
            else:
                print("❌ Batch export failed")
        except Exception as e:
            print(f"❌ Error in batch export: {e}")
            import traceback
            traceback.print_exc()

    def update_progress(self, progress: VideoExportProgress):
        """Update UI with current progress"""
        # Update progress bar and percentage
        self.progress_bar.set(progress.progress_percent / 100.0)
        self.percentage_label.configure(text=f"{int(progress.progress_percent)}%")
        
        # Update current file
        if progress.current_file:
            self.current_file_label.configure(text=f"Processing: {progress.current_file}")
        
        # Update file counter
        self.file_counter_label.configure(text=f"File {progress.current_index} of {progress.total_files}")
        
        # Update time estimate
        if progress.estimated_time_remaining > 0:
            self.time_estimate_label.configure(
                text=f"Estimated time remaining: {progress.estimated_time_remaining}s"
            )
        
        # Update status-specific UI
        if progress.status == "error":
            self.current_file_label.configure(text=f"❌ Error: {progress.error_message}")
        elif progress.status == "cancelled":
            self.current_file_label.configure(text="❌ Export Cancelled")

    def export_completed(self, success: bool, message: str):
        """Handle export completion"""
        self.is_completed = True
        
        if success:
            self.progress_bar.set(1.0)
            self.percentage_label.configure(text="100%")
            self.current_file_label.configure(text="✅ Export Complete!")
            self.file_counter_label.configure(text=f"All {self.total_files} files processed")
            self.time_estimate_label.configure(text=message)
            
            # Update button
            self.cancel_btn.configure(text="Close", command=self.on_close_window)
            
            # Show success message
            messagebox.showinfo("Export Complete", f"{message}\n\nFiles saved to:\n{self.output_dir}")
            
            # Keep dialog open with Close button (removed auto-close)
        else:
            self.current_file_label.configure(text=f"❌ Export Failed")
            self.time_estimate_label.configure(text=message)
            self.cancel_btn.configure(text="Close", command=self.on_close_window)
            
            # Show error message
            messagebox.showerror("Export Failed", message)

    def on_cancel(self):
        """Handle cancel button"""
        if self.is_completed:
            self.on_close_window()
        else:
            # Cancel the export
            self.processor.cancel_export()
            self.is_cancelled = True
            self.current_file_label.configure(text="❌ Cancelling export...")
            self.cancel_btn.configure(state="disabled")

    def on_close_window(self):
        """Handle window close"""
        if not self.is_completed and not self.is_cancelled:
            # Ask for confirmation if export is running
            if messagebox.askyesno("Cancel Export", "Export is in progress. Are you sure you want to cancel?"):
                self.processor.cancel_export()
                self.grab_release()
                self.destroy()
        else:
            self.grab_release()
            self.destroy()