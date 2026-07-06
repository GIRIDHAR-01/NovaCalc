"""
NovaCalc Ultimate - Global Theme Architecture Engine
File Path: theme.py
"""

from settings import THEME_PALETTES

class ThemeEngine:
    """Manages system-wide UI skins across 5 dynamic workspaces."""
    
    @staticmethod
    def get_palette(mode: str) -> dict:
        """Fetches styling hex maps securely, falling back to 'midnight' if not found."""
        if mode in THEME_PALETTES:
            return THEME_PALETTES[mode]
        return THEME_PALETTES["midnight"]