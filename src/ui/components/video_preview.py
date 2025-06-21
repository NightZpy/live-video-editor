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
    def __init__(self, parent, thumbnail_cache=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Current selected cut data
        self.selected_cut = None
        
        # Video data
        self.video_path: Optional[str] = None
        self.video_info: Optional[dict] = None
        
        # Thumbnail cache for shared frames
        self.thumbnail_cache = thumbnail_cache
        
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
        
        # Audio integration
        # Audio state tracking
        self.audio_cache_manager = None
        self.audio_loading_thread = None
        self.audio_pause_position = None  # Track where audio was paused (in seconds relative to cut start)
        self.audio_is_resuming = False   # Flag to indicate if we're resuming from pause
        
        # Cut editing state
        self.original_cut_data = None  # Store original cut data for reset functionality
        self.is_editing_cut = False    # Track if we're in editing mode
        self.editing_start_time = False  # Track which field is being edited
        self.editing_end_time = False
        
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
        """Create time information section with editable times"""
        # Start time
        start_label_style = get_text_style("small")
        start_label = ctk.CTkLabel(parent, text="Start Time (double-click to edit):", **start_label_style)
        start_label.grid(row=1, column=0, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        # Start time container for switching between label and entry
        self.start_time_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.start_time_container.grid(row=2, column=0, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
        
        # Start time label (default view)
        self.start_time_label = ctk.CTkLabel(
            self.start_time_container,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["success"]
        )
        self.start_time_label.grid(row=0, column=0, sticky="w")
        self.start_time_label.bind("<Double-Button-1>", lambda e: self.start_edit_time("start"))
        
        # Start time entry (for editing)
        self.start_time_entry = ctk.CTkEntry(
            self.start_time_container,
            width=100,
            font=("Consolas", 14, "bold"),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["success"]
        )
        self.start_time_entry.bind("<Return>", lambda e: self.save_time_edit("start"))
        self.start_time_entry.bind("<Escape>", lambda e: self.cancel_time_edit("start"))
        self.start_time_entry.bind("<FocusOut>", lambda e: self.on_focus_out("start"))
        self.start_time_entry.bind("<Button-1>", lambda e: self.on_entry_click("start"))
        
        # End time
        end_label_style = get_text_style("small")
        end_label = ctk.CTkLabel(parent, text="End Time (double-click to edit):", **end_label_style)
        end_label.grid(row=1, column=1, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        # End time container
        self.end_time_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.end_time_container.grid(row=2, column=1, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
        
        # End time label (default view)
        self.end_time_label = ctk.CTkLabel(
            self.end_time_container,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["error"]
        )
        self.end_time_label.grid(row=0, column=0, sticky="w")
        self.end_time_label.bind("<Double-Button-1>", lambda e: self.start_edit_time("end"))
        
        # End time entry (for editing)
        self.end_time_entry = ctk.CTkEntry(
            self.end_time_container,
            width=100,
            font=("Consolas", 14, "bold"),
            fg_color=COLORS["input_bg"],
            border_color=COLORS["error"]
        )
        self.end_time_entry.bind("<Return>", lambda e: self.save_time_edit("end"))
        self.end_time_entry.bind("<Escape>", lambda e: self.cancel_time_edit("end"))
        self.end_time_entry.bind("<FocusOut>", lambda e: self.on_focus_out("end"))
        self.end_time_entry.bind("<Button-1>", lambda e: self.on_entry_click("end"))
        
        # Duration (read-only)
        duration_label = ctk.CTkLabel(parent, text="Duration:", **start_label_style)
        duration_label.grid(row=1, column=2, padx=SPACING["md"], pady=SPACING["xs"], sticky="w")
        
        self.duration_label = ctk.CTkLabel(
            parent,
            text="00:00:00",
            font=("Consolas", 14, "bold"),
            text_color=COLORS["accent"]
        )
        self.duration_label.grid(row=2, column=2, padx=SPACING["md"], pady=(0, SPACING["sm"]), sticky="w")
        
        # Edit controls (Save/Reset buttons) - initially hidden
        self.edit_controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.edit_controls_frame.grid(row=3, column=0, columnspan=3, padx=SPACING["md"], pady=SPACING["sm"], sticky="ew")
        
        # Status label for validation messages
        self.status_label = ctk.CTkLabel(
            self.edit_controls_frame,
            text="",
            font=("Segoe UI", 11),
            text_color=COLORS["error"]
        )
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, SPACING["xs"]))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.edit_controls_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, columnspan=3)
        
        # Save button
        save_button_style = get_button_style("success")
        self.save_cut_btn = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Changes",
            width=120,
            command=self.save_cut_changes,
            **save_button_style
        )
        self.save_cut_btn.grid(row=0, column=0, padx=(0, SPACING["sm"]))
        
        # Reset button
        reset_button_style = get_button_style("secondary")
        self.reset_cut_btn = ctk.CTkButton(
            buttons_frame,
            text="🔄 Reset",
            width=100,
            command=self.reset_cut_changes,
            **reset_button_style
        )
        self.reset_cut_btn.grid(row=0, column=1)
        
        # Initially hide edit controls
        self.edit_controls_frame.grid_remove()
    
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
        
        # Check if we're resuming from a pause
        is_resuming = self.audio_pause_position is not None
        
        # Start playback using OpenCV timer
        self.is_playing = True
        self.is_paused = False
        
        # Initialize timing for accurate playback
        self.playback_start_time = time.time()
        self.expected_frame_time = 0.0
        
        # Update button text
        self.play_pause_btn.configure(text="⏸️ Pause")
        
        # Start audio playback if available (pass resume position if resuming)
        if is_resuming:
            self._start_audio_playback(resume_from_position=self.audio_pause_position)
            print(f"🔄 Resuming audio from position: {self.audio_pause_position:.1f}s")
            self.audio_pause_position = None  # Clear pause position
        else:
            self._start_audio_playback()
        
        # Start monitoring playback to auto-stop at cut end
        self.start_cut_monitoring()
        
        # Start the playback loop
        self.play_frame()
        
        audio_status = self._get_audio_status()
        resume_text = " (resumed)" if is_resuming else ""
        print(f"▶️ Started playback for cut: {self.selected_cut.get('title', 'Unknown')} (audio: {audio_status}){resume_text}")
    
    def pause_playback(self):
        """Pause video playback"""
        if not self.video_capture:
            return
        
        # Calculate current position relative to cut start for audio resume
        if self.selected_cut and self.video_capture:
            try:
                current_video_time = self.video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                cut_start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
                self.audio_pause_position = current_video_time - cut_start_time
                print(f"⏸️ Audio paused at position: {self.audio_pause_position:.1f}s (relative to cut start)")
            except Exception as e:
                print(f"⚠️ Error calculating pause position: {e}")
                self.audio_pause_position = None
        
        # Pause playback by stopping the timer
        self.is_playing = False
        self.is_paused = True
        
        # Reset timing variables
        self.playback_start_time = None
        self.expected_frame_time = 0.0
        
        # Pause audio
        self._pause_audio_playback()
        
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
        
        # Clear audio pause position (since we're stopping, not pausing)
        self.audio_pause_position = None
        
        # Reset timing variables
        self.playback_start_time = None
        self.expected_frame_time = 0.0
        if hasattr(self, '_frame_count'):
            delattr(self, '_frame_count')
        
        # Stop audio
        self._stop_audio_playback()
        
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
        Load video file for preview with audio integration
        
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
            
            # Initialize audio cache manager for this video
            self._init_audio_cache_manager()
            
            # Start loading audio in background (non-blocking)
            self._start_audio_loading(video_path)
            
        except Exception as e:
            print(f"❌ Failed to load video: {video_path} - {e}")
    
    def _init_audio_cache_manager(self):
        """Initialize audio cache manager if not already done"""
        if self.audio_cache_manager is None:
            try:
                from ...utils.audio_cache_manager import AudioCacheManager
                self.audio_cache_manager = AudioCacheManager()
                print(f"🎵 Audio cache manager initialized for video preview")
            except Exception as e:
                print(f"⚠️ Failed to initialize audio cache manager: {e}")
                self.audio_cache_manager = None
    
    def _start_audio_loading(self, video_path: str):
        """Start loading audio in background thread"""
        if self.audio_cache_manager is None:
            print(f"⚠️ No audio cache manager, skipping audio loading")
            return
        
        try:
            # Cancel any existing loading
            if self.audio_loading_thread and self.audio_loading_thread.is_alive():
                print(f"🎵 Cancelling previous audio loading...")
            
            # Start new audio loading
            self.audio_loading_thread = self.audio_cache_manager.load_audio_for_video(video_path)
            print(f"🎵 Started background audio loading for: {video_path}")
            
        except Exception as e:
            print(f"⚠️ Failed to start audio loading: {e}")
    
    def _is_audio_ready(self) -> bool:
        """Check if audio is ready for the current video"""
        if not self.audio_cache_manager or not self.video_path:
            return False
        return self.audio_cache_manager.is_audio_ready(self.video_path)
    
    def _get_audio_status(self) -> str:
        """Get current audio loading status"""
        if not self.audio_cache_manager or not self.video_path:
            return "no_audio_manager"
        
        if self.audio_cache_manager.is_audio_ready(self.video_path):
            return "ready"
        elif self.audio_cache_manager.is_loading(self.video_path):
            return "loading"
        else:
            return "not_started"
    
    def load_cut_preview(self, cut_data: dict):
        """
        Load a specific cut for preview
        
        Args:
            cut_data: Cut information with start_time, end_time, etc.
        """
        if not self.video_capture:
            print("⚠️ Video not loaded for cut preview")
            return
        
        # Stop any current playback before loading new cut
        if self.is_playing or self.is_paused:
            self.stop_playback()
            print("⏹️ Stopped previous playback to load new cut")
        
        # Clear any pause position since we're loading a new cut
        self.audio_pause_position = None
        
        # Store selected cut data
        self.selected_cut = cut_data
        
        try:
            # Parse times (assuming they're in "HH:MM:SS" format)
            start_time = self.parse_time_to_seconds(cut_data.get("start_time", "00:00:00"))
            end_time = self.parse_time_to_seconds(cut_data.get("end_time", "00:00:00"))
            
            # Try to get frame from cache first
            frame_image = None
            if self.thumbnail_cache:
                start_time_str = cut_data.get("start_time", cut_data.get("start", "00:00:00"))
                cached_frame = self.thumbnail_cache.get_thumbnail(start_time_str)
                if cached_frame:
                    frame_image = cached_frame
                    print(f"✅ Using cached frame for {start_time_str}")
            
            # If no cached frame, extract from video
            if not frame_image:
                # Seek to start of cut - this will show the frame at that position
                start_frame = int(start_time * self.video_capture.get(cv2.CAP_PROP_FPS))
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                
                # Read and display the first frame of the cut
                ret, frame = self.video_capture.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_image = Image.fromarray(frame_rgb)
                    print(f"📺 Extracted frame from video for {start_time}s")
                    # Reset to the start frame position for playback
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Display the frame
            if frame_image:
                self.display_frame(frame_image)
            
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
    
    def get_video_duration(self) -> float:
        """
        Get total video duration in seconds
        
        Returns:
            Video duration in seconds, or 0 if not available
        """
        # Try to get from video_info first
        if self.video_info and 'duration_seconds' in self.video_info:
            return float(self.video_info['duration_seconds'])
        
        # Fallback to OpenCV if video is loaded
        if self.video_capture and self.video_capture.isOpened():
            frame_count = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                return frame_count / fps
        
        return 0.0
    
    def seconds_to_time_string_precise(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format with precision"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def validate_time_format(self, time_str: str) -> bool:
        """
        Validate time string format
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if format is valid
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return (0 <= hours <= 23 and 
                       0 <= minutes <= 59 and 
                       0 <= seconds <= 59)
            elif len(parts) == 2:
                minutes, seconds = map(int, parts)
                return (0 <= minutes <= 59 and 
                       0 <= seconds <= 59)
            else:
                seconds = int(parts[0])
                return seconds >= 0
        except (ValueError, IndexError):
            return False
    
    def validate_cut_times(self, start_time_str: str, end_time_str: str) -> tuple[bool, str]:
        """
        Validate cut times
        
        Args:
            start_time_str: Start time string
            end_time_str: End time string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate format
        if not self.validate_time_format(start_time_str):
            return False, "Invalid start time format. Use HH:MM:SS or MM:SS"
        
        if not self.validate_time_format(end_time_str):
            return False, "Invalid end time format. Use HH:MM:SS or MM:SS"
        
        # Convert to seconds
        start_seconds = self.parse_time_to_seconds(start_time_str)
        end_seconds = self.parse_time_to_seconds(end_time_str)
        
        # Validate logical constraints
        if start_seconds >= end_seconds:
            return False, "Start time must be before end time"
        
        # Validate against video duration
        video_duration = self.get_video_duration()
        if video_duration > 0:
            if start_seconds >= video_duration:
                return False, f"Start time exceeds video duration ({self.seconds_to_time_string_precise(video_duration)})"
            
            if end_seconds > video_duration:
                return False, f"End time exceeds video duration ({self.seconds_to_time_string_precise(video_duration)})"
        
        # Validate minimum cut duration (e.g., at least 1 second)
        if (end_seconds - start_seconds) < 1.0:
            return False, "Cut must be at least 1 second long"
        
        return True, ""
    
    # === Cut Editing Methods ===
    
    def start_edit_time(self, time_type: str):
        """
        Start editing a time field
        
        Args:
            time_type: Either "start" or "end"
        """
        if not self.selected_cut:
            return
        
        # Store original data if not already stored
        if self.original_cut_data is None:
            self.original_cut_data = self.selected_cut.copy()
            print(f"📋 Stored original cut data for reset functionality")
        
        if time_type == "start":
            self.editing_start_time = True
            # Hide label, show entry
            self.start_time_label.grid_remove()
            self.start_time_entry.grid(row=0, column=0, sticky="w")
            
            # Set current value and select all text
            current_value = self.start_time_label.cget("text")
            self.start_time_entry.delete(0, "end")
            self.start_time_entry.insert(0, current_value)
            self.start_time_entry.select_range(0, "end")
            self.start_time_entry.focus()
            
        elif time_type == "end":
            self.editing_end_time = True
            # Hide label, show entry
            self.end_time_label.grid_remove()
            self.end_time_entry.grid(row=0, column=0, sticky="w")
            
            # Set current value and select all text
            current_value = self.end_time_label.cget("text")
            self.end_time_entry.delete(0, "end")
            self.end_time_entry.insert(0, current_value)
            self.end_time_entry.select_range(0, "end")
            self.end_time_entry.focus()
        
        # Show edit controls if any field is being edited
        self.is_editing_cut = True
        self.edit_controls_frame.grid()
        self.status_label.configure(text="")  # Clear any previous messages
        
        print(f"✏️ Started editing {time_type} time")
    
    def save_time_edit(self, time_type: str):
        """
        Save individual time field edit
        
        Args:
            time_type: Either "start" or "end"
        """
        if time_type == "start" and self.editing_start_time:
            new_value = self.start_time_entry.get().strip()
            
            # Basic format validation
            if not self.validate_time_format(new_value):
                self.status_label.configure(
                    text="Invalid start time format. Use HH:MM:SS or MM:SS",
                    text_color=COLORS["error"]
                )
                return
            
            # Update the label
            self.start_time_label.configure(text=new_value)
            
            # Switch back to label view
            self.start_time_entry.grid_remove()
            self.start_time_label.grid(row=0, column=0, sticky="w")
            self.editing_start_time = False
            
        elif time_type == "end" and self.editing_end_time:
            new_value = self.end_time_entry.get().strip()
            
            # Basic format validation
            if not self.validate_time_format(new_value):
                self.status_label.configure(
                    text="Invalid end time format. Use HH:MM:SS or MM:SS",
                    text_color=COLORS["error"]
                )
                return
            
            # Update the label
            self.end_time_label.configure(text=new_value)
            
            # Switch back to label view
            self.end_time_entry.grid_remove()
            self.end_time_label.grid(row=0, column=0, sticky="w")
            self.editing_end_time = False
        
        # Update duration display
        self.update_duration_display()
        
        # Clear status if no errors
        self.status_label.configure(text="")
        
        # If no fields are being edited, validate the complete cut
        if not self.editing_start_time and not self.editing_end_time:
            self.validate_current_edit()
        
        print(f"✅ Saved {time_type} time edit")
    
    def cancel_time_edit(self, time_type: str):
        """
        Cancel time field edit and restore original value
        
        Args:
            time_type: Either "start" or "end"
        """
        if time_type == "start" and self.editing_start_time:
            # Restore original value
            if self.original_cut_data:
                original_value = self.original_cut_data.get("start_time", "00:00:00")
                self.start_time_label.configure(text=original_value)
            
            # Switch back to label view
            self.start_time_entry.grid_remove()
            self.start_time_label.grid(row=0, column=0, sticky="w")
            self.editing_start_time = False
            
        elif time_type == "end" and self.editing_end_time:
            # Restore original value
            if self.original_cut_data:
                original_value = self.original_cut_data.get("end_time", "00:00:00")
                self.end_time_label.configure(text=original_value)
            
            # Switch back to label view
            self.end_time_entry.grid_remove()
            self.end_time_label.grid(row=0, column=0, sticky="w")
            self.editing_end_time = False
        
        # Update duration and clear status
        self.update_duration_display()
        self.status_label.configure(text="")
        
        # Hide edit controls if no fields are being edited
        if not self.editing_start_time and not self.editing_end_time:
            self.is_editing_cut = False
            self.edit_controls_frame.grid_remove()
        
        print(f"❌ Cancelled {time_type} time edit")
    
    def update_duration_display(self):
        """Update the duration display based on current start/end times"""
        try:
            start_time_str = self.start_time_label.cget("text")
            end_time_str = self.end_time_label.cget("text")
            
            start_seconds = self.parse_time_to_seconds(start_time_str)
            end_seconds = self.parse_time_to_seconds(end_time_str)
            
            if end_seconds > start_seconds:
                duration_seconds = end_seconds - start_seconds
                duration_str = self.seconds_to_time_string_precise(duration_seconds)
                self.duration_label.configure(text=duration_str)
            else:
                self.duration_label.configure(text="--:--:--")
                
        except Exception as e:
            print(f"Error updating duration: {e}")
            self.duration_label.configure(text="--:--:--")
    
    def validate_current_edit(self):
        """Validate current time values and show status"""
        start_time_str = self.start_time_label.cget("text")
        end_time_str = self.end_time_label.cget("text")
        
        is_valid, error_msg = self.validate_cut_times(start_time_str, end_time_str)
        
        if is_valid:
            self.status_label.configure(
                text="✅ Times are valid - Click 'Save Changes' to apply",
                text_color=COLORS["success"]
            )
        else:
            self.status_label.configure(
                text=f"❌ {error_msg}",
                text_color=COLORS["error"]
            )
    
    def save_cut_changes(self):
        """Save all cut changes and update the data"""
        if not self.selected_cut or not self.original_cut_data:
            return
        
        # Get current values - check if we're still editing and use entry values if so
        if self.editing_start_time:
            new_start_time = self.start_time_entry.get().strip()
        else:
            new_start_time = self.start_time_label.cget("text")
            
        if self.editing_end_time:
            new_end_time = self.end_time_entry.get().strip()
        else:
            new_end_time = self.end_time_label.cget("text")
        
        print(f"🔄 Attempting to save changes: {new_start_time} - {new_end_time}")
        
        # Validate before saving
        is_valid, error_msg = self.validate_cut_times(new_start_time, new_end_time)
        
        if not is_valid:
            self.status_label.configure(
                text=f"❌ Cannot save: {error_msg}",
                text_color=COLORS["error"]
            )
            return
        
        # Update selected cut data
        self.selected_cut["start_time"] = new_start_time
        self.selected_cut["end_time"] = new_end_time
        
        # Calculate and update duration
        start_seconds = self.parse_time_to_seconds(new_start_time)
        end_seconds = self.parse_time_to_seconds(new_end_time)
        duration_seconds = end_seconds - start_seconds
        duration_str = self.seconds_to_time_string_precise(duration_seconds)
        self.selected_cut["duration"] = duration_str
        
        # Update all displays with the new values
        self.start_time_label.configure(text=new_start_time)
        self.end_time_label.configure(text=new_end_time)
        self.duration_label.configure(text=duration_str)
        
        # Hide any active editing fields and show labels
        if self.editing_start_time:
            self.start_time_entry.grid_remove()
            self.start_time_label.grid(row=0, column=0, sticky="w")
            self.editing_start_time = False
            
        if self.editing_end_time:
            self.end_time_entry.grid_remove()
            self.end_time_label.grid(row=0, column=0, sticky="w")
            self.editing_end_time = False
        
        # Notify that changes were saved
        self.status_label.configure(
            text="💾 Changes saved successfully!",
            text_color=COLORS["success"]
        )
        
        # Reset editing state but keep original data for future resets
        self.is_editing_cut = False
        self.edit_controls_frame.grid_remove()
        
        # Only update time display without reloading the video preview
        # (The video frame doesn't need to change, just the time info)
        if self.video_capture and self.video_capture.isOpened():
            # Update time display for the new cut duration
            start_seconds = self.parse_time_to_seconds(new_start_time)
            end_seconds = self.parse_time_to_seconds(new_end_time)
            cut_duration = end_seconds - start_seconds
            self.update_time_display(0, cut_duration)  # Start at 0 relative to cut
        
        # Notify cuts list component about the change (if available)
        # Note: This may cause visual refresh - could be disabled if not critical
        try:
            self.notify_cut_data_changed()
        except Exception as e:
            print(f"⚠️ Non-critical error notifying cuts list: {e}")
        
        print(f"💾 Cut changes saved: {new_start_time} - {new_end_time} (duration: {duration_str})")
        print(f"📊 Updated cut data: start_time={self.selected_cut['start_time']}, end_time={self.selected_cut['end_time']}")
    
    def reset_cut_changes(self):
        """Reset cut to original values"""
        if not self.original_cut_data:
            return
        
        # Restore original values
        original_start = self.original_cut_data.get("start_time", "00:00:00")
        original_end = self.original_cut_data.get("end_time", "00:00:00")
        original_duration = self.original_cut_data.get("duration", "00:00:00")
        
        # Update displays
        self.start_time_label.configure(text=original_start)
        self.end_time_label.configure(text=original_end)
        self.duration_label.configure(text=original_duration)
        
        # Update selected cut data
        self.selected_cut["start_time"] = original_start
        self.selected_cut["end_time"] = original_end
        self.selected_cut["duration"] = original_duration
        
        # Reset editing state
        self.is_editing_cut = False
        self.editing_start_time = False
        self.editing_end_time = False
        
        # Hide entries if visible and show labels
        self.start_time_entry.grid_remove()
        self.end_time_entry.grid_remove()
        self.start_time_label.grid(row=0, column=0, sticky="w")
        self.end_time_label.grid(row=0, column=0, sticky="w")
        
        # Hide edit controls
        self.edit_controls_frame.grid_remove()
        
        # Update video preview to original cut times
        if self.video_capture and self.video_capture.isOpened():
            self.load_cut_preview(self.selected_cut)
        
        # Clear status
        self.status_label.configure(text="")
        
        print(f"🔄 Cut reset to original: {original_start} - {original_end}")
    
    def notify_cut_data_changed(self):
        """Notify other components that cut data has changed"""
        try:
            # Try to find the main editor and cuts list to refresh data
            main_window = self.winfo_toplevel()
            
            if hasattr(main_window, 'main_editor') and hasattr(main_window.main_editor, 'cuts_list'):
                cuts_list_component = main_window.main_editor.cuts_list
                
                # Find the index of current cut in the cuts_data and update only that specific item
                if hasattr(cuts_list_component, 'cuts_data') and self.selected_cut:
                    for i, cut in enumerate(cuts_list_component.cuts_data):
                        if cut is self.selected_cut:  # Same object reference
                            # Try to update only the specific cut item rather than refreshing everything
                            if hasattr(cuts_list_component, 'update_cut_display'):
                                cuts_list_component.update_cut_display(i, self.selected_cut)
                            elif hasattr(cuts_list_component, 'refresh_cut_display'):
                                cuts_list_component.refresh_cut_display(i)
                            else:
                                # Last resort: refresh all (causes the visual refresh issue)
                                print("⚠️ Using full refresh - may cause visual glitch")
                                cuts_list_component.load_cuts(cuts_list_component.cuts_data)
                            break
                
                print("📋 Notified cuts list about data changes (optimized)")
            else:
                print("⚠️ Could not find cuts list component to notify")
                
        except Exception as e:
            print(f"⚠️ Error notifying cut data change: {e}")
    
    # === Updated Methods ===
    
    def update_cut_info(self, cut_data):
        """Update the display with selected cut information and load cut preview"""
        # Clear any existing editing state first
        self.cancel_all_editing()
        
        self.selected_cut = cut_data
        
        if cut_data:
            # Store original data for reset functionality
            self.original_cut_data = cut_data.copy()
            
            # Update time displays
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
        else:
            # Clear all data
            self.original_cut_data = None
            self.start_time_label.configure(text="00:00:00")
            self.end_time_label.configure(text="00:00:00")
            self.duration_label.configure(text="00:00:00")
            self.title_entry.delete(0, "end")
            self.desc_entry.delete(0, "end")
    
    def cancel_all_editing(self):
        """Cancel any active editing and reset UI to display mode"""
        if self.editing_start_time:
            self.start_time_entry.grid_remove()
            self.start_time_label.grid(row=0, column=0, sticky="w")
            self.editing_start_time = False
        
        if self.editing_end_time:
            self.end_time_entry.grid_remove()
            self.end_time_label.grid(row=0, column=0, sticky="w")
            self.editing_end_time = False
        
        if self.is_editing_cut:
            self.is_editing_cut = False
            self.edit_controls_frame.grid_remove()
            self.status_label.configure(text="")
    
    def release_video(self):
        """Release video resources"""
        if self.video_capture:
            try:
                self.video_capture.release()
            except:
                pass
        self.current_photo_image = None
        self.show_placeholder()
    
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
    
    def _start_audio_playback(self, resume_from_position=None):
        """
        Start audio playback for the current cut
        
        Args:
            resume_from_position: Optional position in seconds (relative to cut start) to resume from
        """
        if not self.audio_cache_manager or not self.video_path or not self.selected_cut:
            print(f"⚠️ Cannot start audio: manager={self.audio_cache_manager is not None}, path={self.video_path is not None}, cut={self.selected_cut is not None}")
            return
        
        try:
            # Get cut timing
            start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
            end_time = self.parse_time_to_seconds(self.selected_cut.get("end_time", "00:00:00"))
            duration = end_time - start_time
            
            if duration <= 0:
                print(f"⚠️ Invalid cut duration: {duration}s")
                return
            
            # If resuming from a specific position, adjust the start time and duration
            if resume_from_position is not None and resume_from_position > 0:
                # Adjust start time to resume position
                actual_start_time = start_time + resume_from_position
                actual_duration = duration - resume_from_position
                
                if actual_duration <= 0:
                    print(f"⚠️ Resume position too late: {resume_from_position}s >= {duration}s")
                    return
                
                print(f"🔄 Resuming audio from {resume_from_position:.1f}s into cut")
            else:
                # Start from beginning
                actual_start_time = start_time
                actual_duration = duration
            
            # Create audio segment for this cut (from current position)
            self.current_audio_segment = self.audio_cache_manager.create_audio_segment(
                self.video_path, actual_start_time, actual_duration
            )
            
            if self.current_audio_segment:
                # Start audio playback
                self.current_audio_segment.play()
                action = "resumed" if resume_from_position is not None else "started"
                print(f"🎵 Audio {action} for cut: {actual_start_time:.1f}s - {end_time:.1f}s")
            else:
                audio_status = self._get_audio_status()
                print(f"⚠️ Could not create audio segment (status: {audio_status})")
                
        except Exception as e:
            print(f"❌ Error starting audio playback: {e}")
    
    def _pause_audio_playback(self):
        """Pause audio playback"""
        try:
            import pygame
            pygame.mixer.pause()
            print(f"⏸️ Audio paused")
        except Exception as e:
            print(f"⚠️ Error pausing audio: {e}")
    
    def _resume_audio_playback(self):
        """Resume audio playback"""
        try:
            import pygame
            pygame.mixer.unpause()
            print(f"▶️ Audio resumed")
        except Exception as e:
            print(f"⚠️ Error resuming audio: {e}")
    
    def _stop_audio_playback(self):
        """Stop audio playback"""
        try:
            import pygame
            pygame.mixer.stop()
            self.current_audio_segment = None
            print(f"🛑 Audio stopped")
        except Exception as e:
            print(f"⚠️ Error stopping audio: {e}")
    
    def on_entry_click(self, time_type: str):
        """Handle when entry is clicked to track focus"""
        self.last_focused_entry = time_type
        # print(f"🎯 Entry clicked: {time_type}")

    def on_focus_out(self, time_type: str):
        """Handle when entry loses focus - with delayed check"""
        # print(f"⚡ Focus out triggered for: {time_type}")
        if self.focus_check_after_id:
            self.after_cancel(self.focus_check_after_id)
        self.focus_check_after_id = self.after(100, lambda: self.check_and_save_focus_out(time_type))

    def check_and_save_focus_out(self, time_type: str):
        """Check if focus truly moved away and save if needed"""
        try:
            focused_widget = self.focus_get()
            # print(f"🔍 Focus check - current widget: {focused_widget}")
            should_save = True
            if time_type == "start":
                should_save = focused_widget != self.start_time_entry
            elif time_type == "end":
                should_save = focused_widget != self.end_time_entry
            if focused_widget == self.start_time_entry or focused_widget == self.end_time_entry:
                should_save = False
            if focused_widget == self.save_cut_btn or focused_widget == self.reset_cut_btn:
                should_save = False
            if time_type == "start" and not self.editing_start_time:
                should_save = False
            elif time_type == "end" and not self.editing_end_time:
                should_save = False
            if should_save:
                self.save_time_edit(time_type)
            # else:
            #     print(f"⏸️ Skipped auto-save for: {time_type}")
        except Exception as e:
            print(f"⚠️ Error in focus check: {e}")
        finally:
            self.focus_check_after_id = None
    
    def setup_global_click_binding(self):
        """Setup global click binding to catch clicks outside entries for auto-save"""
        # Bind to the main window to catch all clicks
        main_window = self.winfo_toplevel()
        main_window.bind("<Button-1>", self.on_global_click, add=True)
        
        # Also bind to this component specifically
        self.bind("<Button-1>", self.on_global_click, add=True)

    def on_global_click(self, event):
        """Handle global clicks to save entries when clicking elsewhere"""
        if not self.is_editing_cut:
            return
            
        try:
            # Get the widget that was clicked
            clicked_widget = event.widget
            
            # List of widgets where clicking should NOT trigger auto-save
            excluded_widgets = [
                self.start_time_entry,
                self.end_time_entry, 
                self.save_cut_btn,
                self.reset_cut_btn
            ]
            
            # Check if the clicked widget is one we should ignore
            should_save = True
            for widget in excluded_widgets:
                if clicked_widget == widget:
                    should_save = False
                    break
                    
                # Also check if clicked widget is a child of excluded widgets
                try:
                    if str(clicked_widget).startswith(str(widget)):
                        should_save = False
                        break
                except:
                    pass
            
            if should_save:
                # Auto-save any active editing fields
                if self.editing_start_time:
                    self.after_idle(lambda: self.save_time_edit("start"))
                    
                if self.editing_end_time:
                    self.after_idle(lambda: self.save_time_edit("end"))
                    
        except Exception as e:
            print(f"⚠️ Error in global click handler: {e}")
