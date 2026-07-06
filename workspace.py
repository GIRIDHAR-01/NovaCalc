"""
NovaCalc Ultimate - Persistent Freeform Notepad Model
File Path: workspace.py
"""
import os

class WorkspaceManager:
    def __init__(self):
        self.filename = "workspace_notes.txt"
        self.notes = self.load_notes()

    def load_notes(self) -> str:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return ""
        return "📝 Scratchpad\nType notes or formulas here..."

    def save_notes(self, text: str):
        self.notes = text
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(text)
        except:
            pass

    def clear_all(self):
        self.notes = ""
        self.save_notes("")

    def get_notes(self) -> str:
        return self.notes