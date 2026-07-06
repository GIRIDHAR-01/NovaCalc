"""
NovaCalc Ultimate - Unified Design System Tokens
File Path: settings.py
"""

# --- GLOBAL APPLICATION SPECIFICATIONS ---
APP_NAME = "NovaCalc Workspace"
CORNER_RADIUS = 12          # Preserved for backward compatibility
BUTTON_MIN_HEIGHT = 55      # Preserved for backward compatibility
CORNER_RADIUS_LARGE = 16
CORNER_RADIUS_SMALL = 8
DEFAULT_PADDING = 16
SIDEBAR_WIDTH = 220
PANEL_MIN_HEIGHT = 55

# --- SYSTEM WIDE COMPREHENSIVE PALETTES MATRIX ---
THEME_PALETTES = {
    "midnight": {
        "PRIMARY": "#4F8CFF",       # Neon Electric Blue
        "ACCENT": "#00D4FF",        # Cyan Glow
        "BACKGROUND": "#0B0D12",    # Deep Infinite Black Canvas
        "SURFACE": "#161922",       # Elevated Soft Dark Sidebar/Panels
        "SURFACE_ALT": "#1E2330",   # Inner Active Interactive States
        "TEXT_MAIN": "#F5F6F8",     # Main Stark White Content
        "TEXT_MUTED": "#6B7A99",    # Faded Slate Blueprint Labels
        "OPERATOR": "#1A2233",      # Specialized Operator Buttons Bg
        "FUNCTIONAL": "#222B3D",    # Specialty Action Button Bg
        "ERROR": "#FF4D6A"
    },
    "aurora": {
        "PRIMARY": "#00E676",       # Matrix Neon Green
        "ACCENT": "#00B0FF",        # Aurora Sky Blue
        "BACKGROUND": "#0A1118",    # Deep Arctic Teal Black
        "SURFACE": "#121E2B",       # Soft Emerald Midnight Slate
        "SURFACE_ALT": "#1B2D3F",   # Active Rows
        "TEXT_MAIN": "#E0F2F1",     # Ice Mint Content Text
        "TEXT_MUTED": "#546E7A",    # Dark Sea Foam Labels
        "OPERATOR": "#102636",
        "FUNCTIONAL": "#17354A",
        "ERROR": "#FF5252"
    },
    "cyber": {
        "PRIMARY": "#FF007F",       # Hot Synthwave Pink
        "ACCENT": "#7B2CBF",        # Laser Purple
        "BACKGROUND": "#05050A",    # Void Black
        "SURFACE": "#0F0C1B",       # Cyber Deck Terminal Background
        "SURFACE_ALT": "#1D1635",   # Grid Highlight
        "TEXT_MAIN": "#00FFFF",     # Pure Neon Cyan Text
        "TEXT_MUTED": "#5A3E8A",    # Dark Laser Purple Subtitles
        "OPERATOR": "#140727",
        "FUNCTIONAL": "#220C3E",
        "ERROR": "#FF0055"
    },
    "glass": {
        "PRIMARY": "#A29BFE",       # Frosted Amethyst Lavender
        "ACCENT": "#74B9FF",        # Soft Pastel Blue
        "BACKGROUND": "#1E1E24",    # Warm Slate Dark Background
        "SURFACE": "#2A2A35",       # Translucent Simulated Card Plate
        "SURFACE_ALT": "#353545",   # Hover Frosted State
        "TEXT_MAIN": "#F1F2F6",     # Cream Content Text
        "TEXT_MUTED": "#A4B0BE",    # Soft Silver Dust Sub-labels
        "OPERATOR": "#23232F",
        "FUNCTIONAL": "#2E2E3E",
        "ERROR": "#FF6B6B"
    },
    "light": {
        "PRIMARY": "#3B82F6",       # Clean Corporate Slate Blue
        "ACCENT": "#06B6D4",        # Modern Clean Teal
        "BACKGROUND": "#F8FAFC",    # Pure White Canvas
        "SURFACE": "#FFFFFF",       # Paper White Sidebar Elements
        "SURFACE_ALT": "#E2E8F0",   # Soft Gray Divided Active Plates
        "TEXT_MAIN": "#0F172A",     # Ultra High Contrast Charcoal Bold
        "TEXT_MUTED": "#64748B",    # Muted Gray Blue Subtitle Descriptions
        "OPERATOR": "#F1F5F9",
        "FUNCTIONAL": "#E2E8F0",
        "ERROR": "#EF4444"
    }
}