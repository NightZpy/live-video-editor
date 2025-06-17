"""
Progress Dialog Component
Phase 2.5 - Progress Window UI
"""

import customtkinter as ctk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, parent, export_type="single", **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configuration
        self.export_type = export_type  # "single" or "all"
        self.progress_value = 0.0
        self.current_file_index = 0
        self.total_files = 1 if export_type == "single" else 4
        self.is_cancelled = False
        
        # Mock file data
        self.files_to_process = self.get_mock_files()
        
        # Configure window
        self.setup_window()
        
        # Setup UI
        self.setup_ui()
        
        # Start simulation
        self.start_progress_simulation()
    
    def setup_window(self):
        """Configure the progress window"""
        # Window properties
        self.title("Exporting Video Cuts")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Center on parent
        self.center_on_parent()
        
        # Make modal
        self.grab_set()
        self.focus_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def center_on_parent(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (450 // 2)
        y = parent_y + (parent_height // 2) - (300 // 2)
        
        self.geometry(f"450x300+{x}+{y}")
    
    def get_mock_files(self):
        """Get mock files for simulation"""
        if self.export_type == "single":
            return ["Introduction.mp4"]
        else:
            return [
                "Introduction.mp4",
                "Main_Content.mp4", 
                "Examples.mp4",
                "Conclusion.mp4"
            ]
    
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
        icon_label.grid(row=0, column=0, padx=(SPACING["lg"], SPACING["md"]), pady=SPACING["md"])
        
        # Title and subtitle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew", pady=SPACING["md"])
        title_frame.grid_columnconfigure(0, weight=1)
        
        # Main title
        title_style = get_text_style("header")
        title_label = ctk.CTkLabel(
            title_frame,
            text="Exporting Video Cuts",
            **title_style
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Subtitle
        subtitle_style = get_text_style("secondary")
        export_text = "Single cut" if self.export_type == "single" else f"{self.total_files} cuts"
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text=f"Processing {export_text}...",
            **subtitle_style
        )
        subtitle_label.grid(row=1, column=0, sticky="w")
    
    def create_progress_section(self):
        """Create the progress section"""
        progress_frame_style = get_frame_style("default")
        progress_frame = ctk.CTkFrame(self, **progress_frame_style)
        progress_frame.grid(row=1, column=0, sticky="nsew", padx=SPACING["lg"], pady=(0, SPACING["md"]))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Current file being processed
        self.current_file_label = ctk.CTkLabel(
            progress_frame,
            text="Preparing...",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["text"]
        )
        self.current_file_label.grid(row=0, column=0, pady=(SPACING["lg"], SPACING["md"]))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=350,
            height=20,
            progress_color=COLORS["accent"],
            fg_color=COLORS["input_bg"]
        )
        self.progress_bar.grid(row=1, column=0, pady=SPACING["md"])
        self.progress_bar.set(0)
        
        # Percentage label - more visible
        self.percentage_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["accent"]  # Use accent color to stand out
        )
        self.percentage_label.grid(row=2, column=0, pady=(SPACING["md"], SPACING["md"]))
        
        # File counter
        self.file_counter_label = ctk.CTkLabel(
            progress_frame,
            text=f"File 0 of {self.total_files}",
            **get_text_style("secondary")
        )
        self.file_counter_label.grid(row=3, column=0, pady=SPACING["xs"])
        
        # Time estimate
        self.time_estimate_label = ctk.CTkLabel(
            progress_frame,
            text="Calculating time...",
            **get_text_style("small")
        )
        self.time_estimate_label.grid(row=4, column=0, pady=(SPACING["xs"], SPACING["lg"]))
    
    def create_controls(self):
        """Create control buttons"""
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["lg"], pady=(0, SPACING["lg"]))
        controls_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Cancel button
        cancel_btn_style = get_button_style("error")
        self.cancel_btn = ctk.CTkButton(
            controls_frame,
            text="Cancel",
            width=120,
            command=self.on_cancel,
            **cancel_btn_style
        )
        self.cancel_btn.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["md"], sticky="w")
        
        # Minimize button
        minimize_btn_style = get_button_style("secondary")
        self.minimize_btn = ctk.CTkButton(
            controls_frame,
            text="Minimize",
            width=120,
            command=self.on_minimize,
            **minimize_btn_style
        )
        self.minimize_btn.grid(row=0, column=1, padx=SPACING["md"], pady=SPACING["md"], sticky="e")
    
    def start_progress_simulation(self):
        """Start the progress simulation"""
        print("🚀 Starting progress simulation")
        # Small delay to ensure UI is ready
        self.after(200, self.simulate_progress)
    
    def simulate_progress(self):
        """Simulate export progress"""
        if self.is_cancelled:
            return
            
        # Calculate progress increment
        total_steps = 100
        increment = 1.0 / total_steps
        
        # Update progress
        self.progress_value += increment
        self.progress_bar.set(self.progress_value)
        
        # Update percentage
        percentage = int(self.progress_value * 100)
        self.percentage_label.configure(text=f"{percentage}%")
        print(f"📊 Progress: {percentage}%")  # Debug
        
        # Update current file based on progress
        files_completed = int(self.progress_value * self.total_files)
        if files_completed < self.total_files:
            current_file = self.files_to_process[files_completed]
            self.current_file_label.configure(text=f"Processing: {current_file}")
            self.file_counter_label.configure(text=f"File {files_completed + 1} of {self.total_files}")
        
        # Update time estimate
        if percentage > 10:  # Start showing estimate after 10%
            remaining_time = max(1, int((100 - percentage) * 0.1))  # Rough estimate
            self.time_estimate_label.configure(text=f"Estimated time remaining: {remaining_time}s")
        
        # Check if complete
        if self.progress_value >= 1.0:
            self.complete_export()
        else:
            # Continue simulation
            self.after(50, self.simulate_progress)  # Update every 50ms for smooth animation
    
    def complete_export(self):
        """Handle export completion"""
        self.current_file_label.configure(text="✅ Export Complete!")
        self.percentage_label.configure(text="100%")
        self.file_counter_label.configure(text=f"All {self.total_files} files processed")
        self.time_estimate_label.configure(text="Export finished successfully")
        
        # Update buttons
        self.cancel_btn.configure(text="Close", command=self.on_close)
        self.minimize_btn.configure(state="disabled")
        
        # Auto-close after 3 seconds
        self.after(3000, self.on_close)
    
    def on_cancel(self):
        """Handle cancel button"""
        if self.progress_value >= 1.0:
            # Export complete, close normally
            self.on_close()
        else:
            # Cancel export
            self.is_cancelled = True
            self.current_file_label.configure(text="❌ Export Cancelled")
            self.time_estimate_label.configure(text="Export was cancelled by user")
            self.cancel_btn.configure(text="Close", command=self.on_close)
            self.minimize_btn.configure(state="disabled")
    
    def on_minimize(self):
        """Handle minimize button"""
        self.iconify()
    
    def on_close(self):
        """Handle close dialog"""
        self.grab_release()
        self.destroy()
