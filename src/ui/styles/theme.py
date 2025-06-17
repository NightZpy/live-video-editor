"""
Modern Dark Theme Configuration
Live Video Editor UI Theme System
"""

import customtkinter as ctk

# Color Palette
COLORS = {
    "primary": "#1a1a1a",      # Main background
    "secondary": "#2d2d2d",    # Panels
    "accent": "#007acc",       # Main buttons
    "accent_hover": "#005a9e", # Accent hover state
    "success": "#4caf50",      # Success states
    "success_hover": "#45a049", # Success hover state
    "warning": "#ff9800",      # Warnings
    "warning_hover": "#e68900", # Warning hover state
    "error": "#f44336",        # Errors
    "error_hover": "#d32f2f",  # Error hover state
    "text": "#ffffff",         # Main text
    "text_secondary": "#b0b0b0", # Secondary text
    "hover": "#3d3d3d",        # Hover states
    "border": "#404040",       # Borders
    "input_bg": "#262626",     # Input backgrounds
}

# Typography
FONTS = {
    "main": ("Segoe UI", 14),
    "header": ("Segoe UI", 18, "bold"),
    "large_header": ("Segoe UI", 24, "bold"),
    "small": ("Segoe UI", 12),
    "monospace": ("Consolas", 12),
}

# Spacing
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
}

# Border radius
BORDER_RADIUS = 8

def apply_theme():
    """Apply the modern dark theme to CustomTkinter"""
    # Set appearance mode to dark
    ctk.set_appearance_mode("dark")
    
    # Set color theme to blue
    ctk.set_default_color_theme("blue")
    
    # Configure widget colors
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

def get_button_style(variant="primary"):
    """Get button styling configuration"""
    styles = {
        "primary": {
            "fg_color": COLORS["accent"],
            "hover_color": COLORS["accent_hover"],
            "text_color": COLORS["text"],
            "corner_radius": BORDER_RADIUS,
            "font": FONTS["main"],
        },
        "secondary": {
            "fg_color": COLORS["secondary"],
            "hover_color": COLORS["hover"],
            "text_color": COLORS["text"],
            "corner_radius": BORDER_RADIUS,
            "font": FONTS["main"],
        },
        "success": {
            "fg_color": COLORS["success"],
            "hover_color": COLORS["success_hover"],
            "text_color": COLORS["text"],
            "corner_radius": BORDER_RADIUS,
            "font": FONTS["main"],
        },
        "warning": {
            "fg_color": COLORS["warning"],
            "hover_color": COLORS["warning_hover"],
            "text_color": COLORS["text"],
            "corner_radius": BORDER_RADIUS,
            "font": FONTS["main"],
        },
        "error": {
            "fg_color": COLORS["error"],
            "hover_color": COLORS["error_hover"],
            "text_color": COLORS["text"],
            "corner_radius": BORDER_RADIUS,
            "font": FONTS["main"],
        }
    }
    return styles.get(variant, styles["primary"])

def get_frame_style(variant="default"):
    """Get frame styling configuration"""
    styles = {
        "default": {
            "fg_color": COLORS["secondary"],
            "corner_radius": BORDER_RADIUS,
        },
        "primary": {
            "fg_color": COLORS["primary"],
            "corner_radius": BORDER_RADIUS,
        },
        "card": {
            "fg_color": COLORS["secondary"],
            "corner_radius": BORDER_RADIUS,
            "border_width": 1,
            "border_color": COLORS["border"],
        }
    }
    return styles.get(variant, styles["default"])

def get_text_style(variant="default"):
    """Get text styling configuration"""
    styles = {
        "default": {
            "text_color": COLORS["text"],
            "font": FONTS["main"],
        },
        "header": {
            "text_color": COLORS["text"],
            "font": FONTS["header"],
        },
        "large_header": {
            "text_color": COLORS["text"],
            "font": FONTS["large_header"],
        },
        "secondary": {
            "text_color": COLORS["text_secondary"],
            "font": FONTS["main"],
        },
        "small": {
            "text_color": COLORS["text_secondary"],
            "font": FONTS["small"],
        }
    }
    return styles.get(variant, styles["default"])
