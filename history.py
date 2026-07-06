"""
NovaCalc - History Tracking Engine
File Path: history.py
"""

class HistoryManager:
    """Manages a list of past calculations in memory."""
    
    def __init__(self) -> None:
        # This list will store our past calculations as strings
        self._history_log = []

    def add_record(self, expression: str, result: str) -> None:
        """Saves a completed calculation into the history list."""
        if expression and result and result != "Error":
            record = f"{expression} = {result}"
            self._history_log.append(record)

    def get_all_records(self) -> list:
        """Returns the entire list of past calculations."""
        return self._history_log

    def clear_history(self) -> None:
        """Empties the history log."""
        self._history_log.clear()