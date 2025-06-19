"""
Video Preview Component
Main Editor - Video Preview and Controls Panel
"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
from ..styles.theme import get_frame_style, get_text_style, get_button_style, COLORS, SPACING
from ...utils.video_player import VideoPlayerManager, cv2_frame_to_tkinter

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
        
        # Video player manager
        self.video_player = VideoPlayerManager()
        
        # UI state
        self.info_panel_expanded = False  # Default closed
        
        # Video display components
        self.video_canvas: Optional[tk.Canvas] = None
        self.current_photo_image = None  # Keep reference to prevent garbage collection
        
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
        """Create video preview area with Canvas for video display"""
        preview_frame_style = get_frame_style("card")
        preview_frame = ctk.CTkFrame(self, height=300, **preview_frame_style)
        preview_frame.grid(row=1, column=0, sticky="ew", padx=SPACING["md"], pady=SPACING["md"])
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_propagate(False)
        
        # Video canvas for OpenCV frame display
        self.video_canvas = tk.Canvas(
            preview_frame,
            bg=COLORS["input_bg"],
            highlightthickness=0
        )
        self.video_canvas.grid(row=0, column=0, sticky="nsew", padx=SPACING["md"], pady=SPACING["md"])
        
        # Placeholder text (shown when no video is loaded)
        self.placeholder_text_id = self.video_canvas.create_text(
            150, 120,  # Center position (will be updated on resize)
            text="Video Preview\n(Select a cut to view)",
            fill=COLORS["text_secondary"],
            font=("Segoe UI", 14),
            justify=tk.CENTER
        )
        
        # Bind canvas resize event to center content
        self.video_canvas.bind("<Configure>", self.on_canvas_resize)
    
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
    
    def setup_video_callbacks(self):
        """Setup callbacks for video player events"""
        self.video_player.set_callbacks(
            frame_callback=self.on_video_frame,
            time_callback=self.on_time_update,
            end_callback=self.on_playback_end
        )
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for playback control"""
        # Bind spacebar to play/pause (need to focus the widget first)
        self.bind("<KeyPress-space>", self.on_space_pressed)
        self.focus_set()  # Allow the widget to receive keyboard events
    
    def on_space_pressed(self, event):
        """Handle spacebar press for play/pause toggle"""
        self.toggle_play_pause()
        return "break"  # Prevent the event from propagating
    
    def on_canvas_resize(self, event):
        """Handle canvas resize to center placeholder text"""
        if hasattr(self, 'placeholder_text_id') and self.video_canvas:
            canvas_width = event.width
            canvas_height = event.height
            self.video_canvas.coords(self.placeholder_text_id, canvas_width//2, canvas_height//2)
    
    # === Playback Control Methods ===
    
    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.video_player.is_loaded or not self.selected_cut:
            print("⚠️ No video or cut selected for playback")
            return
        
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start video playback from current position"""
        if not self.video_player.is_loaded or not self.selected_cut:
            return
        
        # For now, just show a message instead of actual playback to avoid bus error
        # This will be properly implemented in a future iteration
        print(f"▶️ Playback requested for cut: {self.selected_cut.get('title', 'Unknown')}")
        print("⚠️ Full playback functionality will be implemented in next iteration")
        
        # Update button state
        self.is_playing = True
        self.is_paused = False
        self.play_pause_btn.configure(text="⏸️ Pause")
        
        # Simulate playback by just updating the button state
        # TODO: Implement actual video playback without threading issues
    
    def pause_playback(self):
        """Pause video playback"""
        if not self.video_player.is_loaded:
            return
        
        # For now, just update button state to avoid bus error
        self.is_playing = False
        self.is_paused = True
        
        # Update button text
        self.play_pause_btn.configure(text="▶️ Play")
        
        print("⏸️ Playback paused (simulation mode)")
    
    def stop_playback(self):
        """Stop video playback and return to cut start"""
        if not self.video_player.is_loaded or not self.selected_cut:
            return
        
        # Reset playback state
        self.is_playing = False
        self.is_paused = False
        
        # Return to start of cut (this is safe - no threading)
        start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
        self.video_player.seek_to_time(start_time)
        
        # Show the frame at start position
        self.show_current_frame()
        
        # Update button text
        self.play_pause_btn.configure(text="▶️ Play")
        
        print(f"⏹️ Playback stopped, returned to start of cut")
    
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
        
        # Load video in video player
        success = self.video_player.load_video(video_path)
        
        if success:
            print(f"✅ Video loaded successfully: {video_path}")
            # Hide placeholder text
            if hasattr(self, 'placeholder_text_id') and self.video_canvas:
                self.video_canvas.itemconfig(self.placeholder_text_id, state='hidden')
        else:
            print(f"❌ Failed to load video: {video_path}")
            self.show_placeholder("Failed to load video")
    
    def load_cut_preview(self, cut_data: dict):
        """
        Load a specific cut for preview
        
        Args:
            cut_data: Cut information with start_time, end_time, etc.
        """
        if not self.video_player.is_loaded:
            print("⚠️ No video loaded for preview")
            return
        
        # Store selected cut data
        self.selected_cut = cut_data
        
        # Parse times (assuming they're in "HH:MM:SS" format)
        start_time = self.parse_time_to_seconds(cut_data.get("start_time", "00:00:00"))
        end_time = self.parse_time_to_seconds(cut_data.get("end_time", "00:00:00"))
        
        # Set cut boundaries
        self.video_player.set_cut_boundaries(start_time, end_time)
        
        # Seek to start of cut and show preview frame
        self.video_player.seek_to_time(start_time)
        
        # Force display of current frame
        self.show_current_frame()
        
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
    
    def show_current_frame(self):
        """
        Force display of current video frame
        """
        if not self.video_player.is_loaded:
            return
        
        # Get current frame
        frame_result = self.video_player.get_current_frame()
        if frame_result:
            ret, frame = frame_result
            if ret:
                current_time = self.video_player.current_time
                self.on_video_frame(frame, current_time)
                print(f"🖼️ Showing frame at time: {current_time:.1f}s")
            else:
                print("❌ Failed to get current frame")
        else:
            print("❌ No frame available")

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
    
    def on_video_frame(self, frame, time_seconds: float):
        """
        Callback for new video frame
        
        Args:
            frame: OpenCV frame
            time_seconds: Current time in seconds
        """
        if not self.video_canvas:
            return
        
        try:
            # Get canvas size
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return  # Canvas not ready
            
            # Convert frame to tkinter format and resize
            tk_image = cv2_frame_to_tkinter(frame, (canvas_width-20, canvas_height-20))
            
            if tk_image is None:
                print("❌ Failed to convert frame to tkinter format")
                return
            
            # Keep reference to prevent garbage collection
            self.current_photo_image = tk_image
            
            # Clear canvas and display frame
            self.video_canvas.delete("video_frame")
            
            image_id = self.video_canvas.create_image(
                canvas_width//2, canvas_height//2,
                image=tk_image,
                tags="video_frame"
            )
            
        except Exception as e:
            print(f"Error displaying video frame: {e}")
    
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
        if self.selected_cut:
            start_time = self.parse_time_to_seconds(self.selected_cut.get("start_time", "00:00:00"))
            self.video_player.seek_to_time(start_time)
            self.show_current_frame()
            
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
            if self.video_player.is_loaded:
                self.load_cut_preview(cut_data)
    
    def release_video(self):
        """Release video resources"""
        self.video_player.release()
        self.current_photo_image = None
        self.show_placeholder()

    # Event handlers (UI only for now)
    def on_export_single(self):
        """Handle export single cut"""
        print(f"🎬 Export single cut: {self.selected_cut.get('title', 'Unknown') if self.selected_cut else 'None'}")
        
        # Import here to avoid circular imports
        from .progress_dialog import ProgressDialog
        
        # Open progress dialog
        progress_dialog = ProgressDialog(self.winfo_toplevel(), export_type="single")
    
    def on_export_all(self):
        """Handle export all cuts"""
        print("🎬 Export all cuts")
        
        # Import here to avoid circular imports
        from .progress_dialog import ProgressDialog
        
        # Open progress dialog
        progress_dialog = ProgressDialog(self.winfo_toplevel(), export_type="all")
    
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
