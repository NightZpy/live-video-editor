"""
Video Preview Component
Main Editor - Video Preview and Controls Panel
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
import cv2
import time
from PIL import Image, ImageTk
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING

class VideoPreviewComponent(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Current selected cut data
        self.selected_cut = None
        
        # Video data
        self.video_path: Optional[str] = None
        self.video_info: Optional[dict] = None
        
        # UI state
        self.info_panel_expanded = False  # Default closed
        
        # Video player widget (OpenCV-based for reliable playback)
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.video_canvas: Optional[tk.Canvas] = None
        self.current_frame: Optional[Image.Image] = None
        self.current_photo_image: Optional[ImageTk.PhotoImage] = None
        
        # Video playback settings
        self.video_fps: float = 30.0  # Default FPS, will be updated when video is loaded
        self.frame_delay: float = 33.333  # Delay between frames in milliseconds (more precise)
        
        # Playback timing
        self.playback_start_time: Optional[float] = None
        self.expected_frame_time: float = 0.0
        
        # Setup UI
        self.setup_ui()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Setup video player callbacks
        self.setup_video_callbacks()
    
    def setup_ui(self):
        """Setup the video preview interface"""
        # Export controls (moved to top for visibility)
        self.create_export_controls()
        
        # Video preview area
        self.create_video_preview()
        
        # Playback controls
        self.create_playback_controls()
        
        # Timeline area
        self.create_timeline()
        
        # Cut information
        self.create_cut_info()
    
    def create_video_preview(self):
        """Create video preview area with OpenCV and Canvas"""
        preview_frame_style = get_frame_style("card")
        preview_frame = ctk.CTkFrame(self, height=300, **preview_frame_style)
        preview_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_propagate(False)
        
        # Create Canvas for video display
        self.video_canvas = tk.Canvas(
            preview_frame,
            bg="#2B2B2B",  # Dark background
            highlightthickness=0
        )
        self.video_canvas.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        
        # Show initial placeholder
        self.show_placeholder()
        
        # Bind canvas resize event
        self.video_canvas.bind("<Configure>", self.on_canvas_resize)
    
    def on_canvas_resize(self, event):
        """Handle canvas resize events to maintain video aspect ratio"""
        if self.current_frame and self.video_canvas:
            self.display_frame(self.current_frame)
    
    def setup_video_callbacks(self):
        """Setup callbacks for video player events"""
        # OpenCV doesn't need specific callbacks, we handle them manually
        pass
    
    def create_playback_controls(self):
        """Create playback controls panel with Play/Pause/Stop buttons and time display"""
        controls_frame_style = get_frame_style("default")
        controls_frame = ctk.CTkFrame(self, height=60, **controls_frame_style)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["sm"]))
        controls_frame.grid_columnconfigure(2, weight=1)  # Time display area gets extra space
        controls_frame.grid_propagate(False)
        
        # Playback state variables
        self.is_playing = False
        self.is_paused = False
        
        # Control buttons frame
        buttons_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=0, padx=SPACING["md"], pady=SPACING["sm"], sticky="w")
        
        # Play/Pause button
        play_button_style = get_button_style("primary")
        self.play_pause_btn = ctk.CTkButton(
            buttons_frame,
            text="▶️ Play",
            width=80,
            command=self.toggle_play_pause,
            **play_button_style
        )
        self.play_pause_btn.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        
        # Stop button
        stop_button_style = get_button_style("secondary")
        self.stop_btn = ctk.CTkButton(
            buttons_frame,
            text="⏹️ Stop",
            width=80,
            command=self.stop_playback,
            **stop_button_style
        )
        self.stop_btn.grid(row=0, column=1, padx=(0, SPACING["sm"]))
        
        # Time display
        time_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        time_frame.grid(row=0, column=2, padx=SPACING["md"], pady=SPACING["sm"], sticky="ew")
        time_frame.grid_columnconfigure(0, weight=1)
        
        # Current time / Total time
        time_text_style = get_text_style("small")
        self.time_label = ctk.CTkLabel(
            time_frame,
            text="00:00 / 00:00",
            **time_text_style
        )
        self.time_label.grid(row=0, column=0, sticky="e")
        
        # Initially disable controls (no video loaded)
        self.set_controls_enabled(False)
    
    def create_timeline(self):
        """Create timeline area"""
        timeline_frame_style = get_frame_style("default")
        timeline_frame = ctk.CTkFrame(self, height=80, **timeline_frame_style)
        timeline_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
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
        """Create cut information panel with toggle"""
        # Main info frame
        info_frame_style = get_frame_style("card")
        self.info_frame = ctk.CTkFrame(self, **info_frame_style)
        self.info_frame.grid(row=4, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # Toggle header
        self.create_info_toggle_header()
        
        # Content frame (initially hidden)
        self.create_info_content()
        
        # Initially hide content
        self.toggle_info_panel(show=False)
    
    def create_info_toggle_header(self):
        """Create the toggle header for cut info"""
        header_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Toggle button with arrow and title
        self.info_toggle_btn = ctk.CTkButton(
            header_frame,
            text="▶ Cut Information",
            command=self.on_toggle_info,
            fg_color="transparent",
            text_color=COLORS["text"],
            hover_color=COLORS["hover"],
            font=get_text_style("default")["font"],
            anchor="w"
        )
        self.info_toggle_btn.grid(row=0, column=0, sticky="ew")
    
    def create_info_content(self):
        """Create the content area for cut information"""
        self.info_content_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.info_content_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=(0, SPACING["md"]))
        self.info_content_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Time information and cut details
        self.create_time_info(self.info_content_frame)
        self.create_cut_details(self.info_content_frame)
    
    def toggle_info_panel(self, show=None):
        """Toggle the info panel visibility"""
        if show is None:
            self.info_panel_expanded = not self.info_panel_expanded
        else:
            self.info_panel_expanded = show
            
        if self.info_panel_expanded:
            self.info_content_frame.grid()
            self.info_toggle_btn.configure(text="▼ Cut Information")
        else:
            self.info_content_frame.grid_remove()
            self.info_toggle_btn.configure(text="▶ Cut Information")
    
    def on_toggle_info(self):
        """Handle info toggle button click"""
        self.toggle_info_panel()
    
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
        export_frame.grid(row=0, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        export_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # New Video button (first)
        new_video_btn_style = get_button_style("warning")
        new_video_btn = ctk.CTkButton(
            export_frame,
            text="← New Video",
            command=self.on_new_video,
            **new_video_btn_style
        )
        new_video_btn.grid(row=0, column=0, padx=SPACING["sm"], pady=SPACING["sm"])
        
        # Export single button
        export_single_style = get_button_style("primary")
        export_single_btn = ctk.CTkButton(
            export_frame,
            text="Export This Cut",
            command=self.on_export_single,
            **export_single_style
        )
        export_single_btn.grid(row=0, column=1, padx=SPACING["sm"], pady=SPACING["sm"])
        
        # Export all button
        export_all_style = get_button_style("success")
        export_all_btn = ctk.CTkButton(
            export_frame,
            text="Export All Cuts",
            command=self.on_export_all,
            **export_all_style
        )
        export_all_btn.grid(row=0, column=2, padx=SPACING["sm"], pady=SPACING["sm"])
        
        # Quality selector placeholder
        quality_btn_style = get_button_style("secondary")
        quality_btn = ctk.CTkButton(
            export_frame,
            text="Quality: Original",
            command=self.on_quality_settings,
            **quality_btn_style
        )
        quality_btn.grid(row=0, column=3, padx=SPACING["sm"], pady=SPACING["sm"])
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for playback control"""
        # Bind spacebar to play/pause (need to focus the widget first)
        self.bind("<KeyPress-space>", self.on_space_pressed)
        self.focus_set()  # Allow the widget to receive keyboard events
    
    def on_space_pressed(self, event):
        """Handle spacebar press for play/pause toggle"""
        self.toggle_play_pause()
        return "break"  # Prevent the event from propagating
    
    # === Playback Control Methods ===
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.video_capture or not self.selected_cut:
            print("⚠️ No video or cut selected for playback")
            return
        
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start video playback from current position"""
        if not self.video_capture or not self.selected_cut:
            return
        
        # Start playback using OpenCV timer
        self.is_playing = True
        self.is_paused = False
        
        # Initialize timing for accurate playback
        self.playback_start_time = time.time()
        self.expected_frame_time = 0.0
        
        # Update button text
        self.play_pause_btn.configure(text="⏸️ Pause")
        
        # Start monitoring playback to auto-stop at cut end
        self.start_cut_monitoring()
        
        # Start the playback loop
        self.play_frame()
        
        print(f"▶️ Started playback for cut: {self.selected_cut.get('title', 'Unknown')}")
    
    def pause_playback(self):
        """Pause video playback"""
        if not self.video_capture:
            return
        
        # Pause playback by stopping the timer
        self.is_playing = False
        self.is_paused = True
        
        # Reset timing variables
        self.playback_start_time = None
        self.expected_frame_time = 0.0
        
        # Stop monitoring
        self.stop_cut_monitoring()
        
        # Update button text
        self.play_pause_btn.configure(text="▶️ Play")
        
        print("⏸️ Playback paused")
    
    def stop_playback(self):
        """Stop video playback and return to cut start"""
        if not self.video_capture or not self.selected_cut:
            return
        
        # Stop playback
        self.is_playing = False
        self.is_paused = False
        
        # Reset timing variables
        self.playback_start_time = None
        self.expected_frame_time = 0.0
        if hasattr(self, '_frame_count'):
            delattr(self, '_frame_count')
        
        # Stop monitoring
        self.stop_cut_monitoring()
        
        # Return to start of cut
        start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
        start_frame = int(start_time * self.video_capture.get(cv2.CAP_PROP_FPS))
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Show the first frame of the cut
        ret, frame = self.video_capture.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(frame_rgb)
            self.display_frame(frame_image)
            # Reset to the start frame position
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Update button text
        self.play_pause_btn.configure(text="▶️ Play")
        
        print(f"⏹️ Playback stopped, returned to start of cut")
    
    def start_cut_monitoring(self):
        """Start monitoring playback to auto-stop at cut end"""
        if not self.selected_cut:
            return
        
        # Schedule periodic checks to see if we've reached the cut end
        self.check_cut_end()
    
    def stop_cut_monitoring(self):
        """Stop monitoring cut playback"""
        # Cancel any scheduled checks
        if hasattr(self, '_monitoring_after_id'):
            self.after_cancel(self._monitoring_after_id)
    
    def check_cut_end(self):
        """Check if playback has reached the end of the current cut"""
        if not self.is_playing or not self.selected_cut or not self.video_capture:
            return
        
        try:
            # Get current position from OpenCV
            current_time = self.video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            end_time = self.parse_time_to_seconds(self.selected_cut.get("end_time", "00:00:00"))
            
            if current_time >= end_time:
                # Auto-stop when reaching cut end
                self.stop_playback()
                print(f"🏁 Cut playback ended at {end_time:.1f}s")
            else:
                # Continue monitoring
                self._monitoring_after_id = self.after(100, self.check_cut_end)  # Check every 100ms
                
                # Update time display
                start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
                cut_current_time = current_time - start_time
                cut_duration = end_time - start_time
                self.update_time_display(cut_current_time, cut_duration)
        except Exception as e:
            print(f"Error monitoring cut end: {e}")
            # Continue monitoring despite error
            self._monitoring_after_id = self.after(100, self.check_cut_end)
    
    def set_controls_enabled(self, enabled: bool):
        """Enable or disable playback controls"""
        state = "normal" if enabled else "disabled"
        self.play_pause_btn.configure(state=state)
        self.stop_btn.configure(state=state)
    
    def update_time_display(self, current_seconds: float, total_seconds: float):
        """Update the time display with current/total time"""
        current_time_str = self.seconds_to_time_string(current_seconds)
        total_time_str = self.seconds_to_time_string(total_seconds)
        self.time_label.configure(text=f"{current_time_str} / {total_time_str}")
    
    def seconds_to_time_string(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    # === Video Loading Methods ===
    
    def load_video(self, video_path: str, video_info: Optional[dict] = None):
        """
        Load video file for preview
        
        Args:
            video_path: Path to the video file
            video_info: Optional video metadata
        """
        self.video_path = video_path
        self.video_info = video_info
        
        try:
            # Load video in OpenCV
            if self.video_capture:
                self.video_capture.release()
            
            self.video_capture = cv2.VideoCapture(video_path)
            if not self.video_capture.isOpened():
                raise Exception("Could not open video file")
            
            # Get video FPS for correct playback timing
            # First try to get it from video_info if provided
            if video_info and 'fps' in video_info:
                self.video_fps = float(video_info['fps'])
                print(f"📊 Using FPS from video_info: {self.video_fps:.2f}")
            else:
                # Fallback to getting FPS from OpenCV
                self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                if self.video_fps <= 0:
                    self.video_fps = 30.0  # Final fallback
                print(f"📊 Using FPS from OpenCV: {self.video_fps:.2f}")
            
            # Calculate frame delay in milliseconds with more precision
            self.frame_delay = 1000.0 / self.video_fps
            
            print(f"✅ Video loaded successfully: {video_path}")
            print(f"📊 Video FPS: {self.video_fps:.2f}, Frame delay: {self.frame_delay}ms")
            
        except Exception as e:
            print(f"❌ Failed to load video: {video_path} - {e}")
    
    def load_cut_preview(self, cut_data: dict):
        """
        Load a specific cut for preview
        
        Args:
            cut_data: Cut information with start_time, end_time, etc.
        """
        if not self.video_capture:
            print("⚠️ Video not loaded for cut preview")
            return
        
        # Store selected cut data
        self.selected_cut = cut_data
        
        try:
            # Parse times (assuming they're in "HH:MM:SS" format)
            start_time = self.parse_time_to_seconds(cut_data.get("start_time", "00:00:00"))
            end_time = self.parse_time_to_seconds(cut_data.get("end_time", "00:00:00"))
            
            # Seek to start of cut - this will show the frame at that position
            start_frame = int(start_time * self.video_capture.get(cv2.CAP_PROP_FPS))
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Read and display the first frame of the cut
            ret, frame = self.video_capture.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_image = Image.fromarray(frame_rgb)
                self.display_frame(frame_image)
                # Reset to the start frame position for playback
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Enable playback controls now that we have a cut selected
            self.set_controls_enabled(True)
            
            # Update time display
            cut_duration = end_time - start_time
            self.update_time_display(0, cut_duration)  # Start at 0 relative to cut
            
            # Reset playback state
            self.is_playing = False
            self.is_paused = False
            self.play_pause_btn.configure(text="▶️ Play")
            
            print(f"📺 Cut preview loaded: {cut_data.get('title', 'Unknown')} ({start_time:.1f}s - {end_time:.1f}s)")
            
        except Exception as e:
            print(f"❌ Error loading cut preview: {e}")
    
    def parse_time_to_seconds(self, time_str: str) -> float:
        """
        Parse time string (HH:MM:SS) to seconds
        
        Args:
            time_str: Time in "HH:MM:SS" format
            
        Returns:
            Time in seconds as float
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:
                return float(parts[0])
        except (ValueError, IndexError):
            return 0.0
    
    def on_time_update(self, time_seconds: float):
        """
        Callback for time updates during playback
        
        Args:
            time_seconds: Current playback time in seconds
        """
        if self.selected_cut:
            # Calculate time relative to cut start
            start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
            end_time = self.parse_time_to_seconds(self.selected_cut.get("end_time", "00:00:00"))
            
            # Time elapsed in the cut
            cut_current_time = time_seconds - start_time
            cut_duration = end_time - start_time
            
            # Update time display
            self.update_time_display(cut_current_time, cut_duration)
    
    def on_playback_end(self):
        """Callback when playback reaches the end of cut"""
        # Reset playback state
        self.is_playing = False
        self.is_paused = False
        self.play_pause_btn.configure(text="▶️ Play")
        
        # Return to start of cut
        if self.selected_cut and self.video_capture:
            start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
            start_frame = int(start_time * self.video_capture.get(cv2.CAP_PROP_FPS))
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Show the first frame
            ret, frame = self.video_capture.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_image = Image.fromarray(frame_rgb)
                self.display_frame(frame_image)
                # Reset to the start frame position
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Reset time display
            end_time = self.parse_time_to_seconds(self.selected_cut.get("end_time", "00:00:00"))
            cut_duration = end_time - start_time
            self.update_time_display(0, cut_duration)
        
        print("🏁 Cut playback ended, returned to start")
    
    def show_placeholder(self, message: str = "Video Preview\n(Select a cut to view)"):
        """
        Show placeholder message in video canvas
        
        Args:
            message: Message to display
        """
        if not self.video_canvas:
            return
        
        # Clear any video frames
        self.video_canvas.delete("video_frame")
        
        # Show/update placeholder text
        if hasattr(self, 'placeholder_text_id'):
            self.video_canvas.itemconfig(self.placeholder_text_id, text=message, state='normal')
        else:
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                self.placeholder_text_id = self.video_canvas.create_text(
                    canvas_width//2, canvas_height//2,
                    text=message,
                    fill=COLORS["text_secondary"],
                    font=("Segoe UI", 14),
                    justify=tk.CENTER
                )
    
    def update_cut_info(self, cut_data):
        """Update the display with selected cut information and load cut preview"""
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
            
            # Load cut preview if video is available
            if self.video_capture and self.video_capture.isOpened():
                self.load_cut_preview(cut_data)
    
    def release_video(self):
        """Release video resources"""
        if self.video_capture:
            try:
                self.video_capture.release()
            except:
                pass
        self.current_photo_image = None
        self.show_placeholder()

    # Event handlers (UI only for now)
    def on_export_single(self):
        """Handle export single cut"""
        if not self.selected_cut:
            print("⚠️ No cut selected for export")
            return
            
        if not self.video_path:
            print("⚠️ No video loaded for export")
            return
        
        print(f"🎬 Export single cut: {self.selected_cut.get('title', 'Unknown')}")
        
        # Convert the cut data to the expected format for export
        cut_export_data = {
            "start": self.selected_cut.get("start_time", "00:00:00"),
            "end": self.selected_cut.get("end_time", "00:00:00"), 
            "title": self.selected_cut.get("title", "Untitled Cut"),
            "description": self.selected_cut.get("description", ""),
            "id": self.selected_cut.get("id", 1)
        }
        
        # Import here to avoid circular imports
        from .progress_dialog import ProgressDialog
        
        # Create and show export dialog with real data
        dialog = ProgressDialog(
            parent=self.winfo_toplevel(),
            video_path=self.video_path,
            cut_data=cut_export_data,
            quality="original"
        )
    
    def on_export_all(self):
        """Handle export all cuts"""
        print("🎬 Export all cuts")
        
        if not self.video_path:
            print("⚠️ No video loaded for export")
            return
        
        # Get all cuts data from the main window
        main_window = self.winfo_toplevel()
        cuts_data = []
        
        # Try to get cuts data from main window (using loaded_cuts_data)
        if hasattr(main_window, 'loaded_cuts_data') and main_window.loaded_cuts_data:
            raw_cuts = main_window.loaded_cuts_data.get('cuts', [])
            
            # Convert cuts to expected format for export
            for cut in raw_cuts:
                cut_export_data = {
                    "start": cut.get("start", cut.get("start_time", "00:00:00")),
                    "end": cut.get("end", cut.get("end_time", "00:00:00")),
                    "title": cut.get("title", "Untitled Cut"),
                    "description": cut.get("description", ""),
                    "id": cut.get("id", len(cuts_data) + 1)
                }
                cuts_data.append(cut_export_data)
        
        # Also try to get from main_editor component as a fallback
        elif hasattr(main_window, 'main_editor') and hasattr(main_window.main_editor, 'cuts_list'):
            # Get cuts from the CutsListComponent
            cuts_list_component = main_window.main_editor.cuts_list
            if hasattr(cuts_list_component, 'cuts_data') and cuts_list_component.cuts_data:
                raw_cuts = cuts_list_component.cuts_data
                
                # Convert cuts to expected format for export
                for cut in raw_cuts:
                    cut_export_data = {
                        "start": cut.get("start_time", "00:00:00"),
                        "end": cut.get("end_time", "00:00:00"),
                        "title": cut.get("title", "Untitled Cut"),
                        "description": cut.get("description", ""),
                        "id": cut.get("id", len(cuts_data) + 1)
                    }
                    cuts_data.append(cut_export_data)
        
        if not cuts_data:
            print("⚠️ No cuts data available for batch export")
            print(f"Debug: main_window has loaded_cuts_data: {hasattr(main_window, 'loaded_cuts_data')}")
            if hasattr(main_window, 'loaded_cuts_data'):
                print(f"Debug: loaded_cuts_data value: {main_window.loaded_cuts_data}")
            return
        
        print(f"📊 Found {len(cuts_data)} cuts for batch export")
        
        # Import here to avoid circular imports
        from .progress_dialog import ProgressDialog
        
        # Create and show export dialog with real data
        dialog = ProgressDialog(
            parent=self.winfo_toplevel(),
            video_path=self.video_path,
            cuts_data=cuts_data,
            quality="original"
        )
        
        # Import here to avoid circular imports
        from .progress_dialog import ProgressDialog
        
        # Create and show export dialog with real data
        dialog = ProgressDialog(
            parent=self.winfo_toplevel(),
            video_path=self.video_path,
            cuts_data=cuts_data,
            quality="original"
        )
    
    def on_quality_settings(self):
        """Handle quality settings"""
        print("⚙️ Quality settings")
    
    def on_new_video(self):
        """Handle new video button - go back to video loading"""
        print("🔄 New video requested")
        
        # We need to communicate this to the main window
        # For now, we'll use a simple approach - find the main window and reset
        main_window = self.winfo_toplevel()
        
        # Check if main_window has the method to reset to video loading
        if hasattr(main_window, 'reset_to_video_loading'):
            main_window.reset_to_video_loading()
        else:
            print("⚠️ Main window doesn't have reset_to_video_loading method")
            print("   This will be implemented when the main window is updated")
    
    def play_frame(self):
        """Play a single frame and schedule the next one with accurate timing"""
        if not self.is_playing or not self.video_capture or not self.selected_cut:
            return
        
        try:
            # Calculate timing for accurate playback
            current_time = time.time()
            if self.playback_start_time is None:
                self.playback_start_time = current_time
                self.expected_frame_time = 0.0
            
            # Get current frame
            ret, frame = self.video_capture.read()
            if ret:
                # Convert frame from BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_image = Image.fromarray(frame_rgb)
                
                # Display the frame
                self.display_frame(frame_image)
                
                # Get current position
                current_pos = self.video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                end_time = self.parse_time_to_seconds(self.selected_cut.get("end_time", "00:00:00"))
                
                # Check if we've reached the end of the cut
                if current_pos >= end_time:
                    self.stop_playback()
                    return
                
                # Update time display
                start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
                cut_current_time = current_pos - start_time
                cut_duration = end_time - start_time
                self.update_time_display(cut_current_time, cut_duration)
                
                # Calculate next frame timing with better accuracy
                self.expected_frame_time += self.frame_delay
                elapsed_time = (current_time - self.playback_start_time) * 1000  # Convert to ms
                time_until_next_frame = max(1, int(self.expected_frame_time - elapsed_time))
                
                # Schedule next frame with calculated delay
                self.after(time_until_next_frame, self.play_frame)
                
                # Debug timing info (remove this in production)
                if hasattr(self, '_frame_count'):
                    self._frame_count += 1
                else:
                    self._frame_count = 1
                
                if self._frame_count % 30 == 0:  # Print every 30 frames
                    actual_fps = self._frame_count / ((current_time - self.playback_start_time) or 1)
                    print(f"🎬 Playback FPS: {actual_fps:.2f} (target: {self.video_fps:.2f})")
                    
            else:
                # End of video reached
                self.stop_playback()
        except Exception as e:
            print(f"Error playing frame: {e}")
            self.stop_playback()
    
    def display_frame(self, frame_image):
        """Display a frame in the canvas"""
        if not self.video_canvas or not frame_image:
            return
        
        try:
            # Get canvas dimensions
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                # Canvas not ready yet
                return
            
            # Calculate scaling to fit canvas while maintaining aspect ratio
            img_width, img_height = frame_image.size
            
            # Calculate scale factors
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)
            
            # Calculate new dimensions
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = frame_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create PhotoImage
            self.current_photo_image = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and display image
            self.video_canvas.delete("video_frame")
            
            # Center the image on canvas
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.video_canvas.create_image(
                x, y, 
                anchor="nw", 
                image=self.current_photo_image, 
                tags="video_frame"
            )
            
            # Store current frame for resize events
            self.current_frame = frame_image
            
        except Exception as e:
            print(f"Error displaying frame: {e}")
