"""
NovaCalc - Core Application Launcher
File Path: app.py
"""

import sys
from PySide6.QtWidgets import QApplication
from main import MainWindow

def main():
    """Starts the application run-loop."""
    # 1. Initialize the low-level engine architecture
    app = QApplication(sys.argv)
    
    # 2. Spin up our window interface layout
    window = MainWindow()
    window.show()
    
    # 3. Hand control over to the desktop event handler loop safely
    sys.exit(app.exec())

if __name__ == "__main__":
    main()