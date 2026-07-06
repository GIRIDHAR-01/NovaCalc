"""
NovaCalc Ultimate - Unified Production Application Engine
Features: Cloud OCR, Camera, Voice, Graphing, Error Boundaries, Session Export & Asset Icons
File Path: main.py
"""

import speech_recognition as sr
from PIL import Image
import requests
import cv2
import os
import sys
import numpy as np

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QPushButton, QGridLayout, QLabel, 
                             QFrame, QStackedWidget, QDialog, QComboBox, QListWidget,
                             QFileDialog, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon

from settings import CORNER_RADIUS
from logic import CalculatorLogic
from history import HistoryManager
from workspace import WorkspaceManager
from theme import ThemeEngine


def get_asset_path(relative_path):
    """Handles absolute file paths dynamically for both raw script runs and PyInstaller builds."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class VoiceWorker(QThread):
    finished_signal = Signal(str)
    status_signal = Signal(str)

    def run(self):
        r = sr.Recognizer()
        r.dynamic_energy_threshold = False
        r.energy_threshold = 300 
        try:
            with sr.Microphone() as source:
                self.status_signal.emit("🎙️ Listening... Speak your equation now.")
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=3, phrase_time_limit=4)
                
            self.status_signal.emit("🧠 Processing your voice expression...")
            spoken_text = r.recognize_google(audio).lower()
            
            replacements = {
                "plus": "+", "minus": "-", "times": "×", "multiplied by": "×", 
                "divided by": "÷", "divided": "÷", "open bracket": "(", "close bracket": ")",
                "into": "×"
            }
            for phrase, symbol in replacements.items():
                spoken_text = spoken_text.replace(phrase, symbol)
            self.finished_signal.emit(spoken_text)
        except sr.WaitTimeoutError:
            self.finished_signal.emit("ERROR: Silence timeout reached.")
        except sr.UnknownValueError:
            self.finished_signal.emit("ERROR: Could not understand speech audio.")
        except Exception as e:
            self.finished_signal.emit(f"ERROR: Microphone issue ({str(e)})")


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1E293B')
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#0F172A')
        self.axes.tick_params(colors='#94A3B8', labelsize=9)
        self.axes.grid(True, color='#334155', linestyle='--', linewidth=0.5)
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
        super().__init__(fig)


class SettingsModal(QDialog):
    def __init__(self, parent=None, current_theme="midnight", theme_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setFixedSize(320, 240)
        self.theme_callback = theme_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Calculator Settings")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #FFFFFF;")
        layout.addWidget(title)
        
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Application Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["midnight", "aurora", "cyber", "glass", "light"])
        self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)
        
        close_btn = QPushButton("Done")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet("background-color: #2563EB; color: white; border-radius: 6px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setStyleSheet("background-color: #131A26; color: #F8FAFC;")

    def _on_theme_changed(self, text):
        if self.theme_callback: self.theme_callback(text)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NovaCalc Workspace")
        self.setMinimumSize(QSize(1050, 720))
        
        # --- WINDOW GRAPHICS BRANDING LAYOUT ---
        icon_path = get_asset_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Forces native Windows architectures to separate taskbar instances correctly
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("novacalc.workspace.engine.1.0")
        
        self.history_manager = HistoryManager()
        self.workspace_manager = WorkspaceManager()
        self.current_theme_mode = "midnight"
        self.theme_colors = ThemeEngine.get_palette(self.current_theme_mode)
        
        self._init_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_ui(self) -> None:
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.root_layout = QHBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # --- COLLAPSIBLE LEFT NAVIGATION SIDEBAR ---
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar_frame)
        self.sidebar_layout.setContentsMargins(12, 20, 12, 20)
        self.sidebar_layout.setSpacing(8)
        
        brand_label = QLabel(" 🔢 NovaCalc")
        brand_label.setStyleSheet("font-weight: bold; font-size: 18px; margin-bottom: 10px;")
        self.sidebar_layout.addWidget(brand_label)
        
        modes = [
            ("🧮 Standard", 0), ("🔬 Scientific", 1), ("💻 Programmer", 2),
            ("📊 Matrix", 3),   ("📈 Statistics", 4), ("🔄 Converter", 5)
        ]
        self.mode_buttons = []
        for name, idx in modes:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.setMinimumHeight(38)
            btn.setStyleSheet("text-align: left; padding-left: 12px;")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, i=idx: self._switch_calculator_mode(i))
            self.sidebar_layout.addWidget(btn)
            self.mode_buttons.append(btn)
            
        self.sidebar_layout.addSpacing(15)
        
        history_title = QLabel("📜 Calculation History")
        history_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #94A3B8; margin-top: 10px;")
        self.sidebar_layout.addWidget(history_title)
        
        self.history_list_widget = QListWidget()
        self.history_list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.history_list_widget.itemClicked.connect(self._on_history_item_clicked)
        self.sidebar_layout.addWidget(self.history_list_widget)
        
        self.sidebar_layout.addStretch()
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.setMinimumHeight(38)
        self.settings_btn.clicked.connect(self._open_settings_modal)
        self.sidebar_layout.addWidget(self.settings_btn)
        
        self.root_layout.addWidget(self.sidebar_frame)
        self.sidebar_frame.setVisible(False)

        # --- CENTRAL CALCULATOR HOUSING CONTAINER ---
        self.calc_container = QWidget()
        self.calc_layout = QVBoxLayout(self.calc_container)
        self.calc_layout.setContentsMargins(24, 20, 24, 24)
        self.calc_layout.setSpacing(14)
        
        top_utility_row = QHBoxLayout()
        
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(36, 36)
        self.menu_btn.setCheckable(True)
        self.menu_btn.setChecked(False)
        self.menu_btn.clicked.connect(self._toggle_sidebar_navigation)
        top_utility_row.addWidget(self.menu_btn)
        
        self.voice_type_btn = QPushButton("🎙️ Voice Input")
        self.voice_type_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.voice_type_btn.clicked.connect(self._trigger_voice_typing)
        
        self.image_calc_btn = QPushButton("📸 Image Math")
        self.image_calc_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.image_calc_btn.clicked.connect(self._trigger_image_calculation)
        
        self.workspace_toggle = QPushButton("📂 Toggle Notepad")
        self.workspace_toggle.setCheckable(True)
        self.workspace_toggle.setChecked(False)  
        self.workspace_toggle.clicked.connect(self._toggle_workspace_drawer)
        
        top_utility_row.addWidget(self.voice_type_btn)
        top_utility_row.addWidget(self.image_calc_btn)
        top_utility_row.addWidget(self.workspace_toggle)
        top_utility_row.addStretch()
        top_utility_row.addWidget(QLabel("DEG"))
        self.calc_layout.addLayout(top_utility_row)

        # INTERACTIVE PLOTTING PANEL LAYER
        self.plot_frame = QFrame()
        self.plot_frame.setMinimumHeight(180)
        self.plot_frame.setVisible(False) 
        plot_box_layout = QVBoxLayout(self.plot_frame)
        plot_box_layout.setContentsMargins(6, 6, 6, 6)
        
        plot_header = QHBoxLayout()
        plot_header.addWidget(QLabel("📈 Function Visualization Engine"))
        plot_header.addStretch()
        close_plot_btn = QPushButton("✕")
        close_plot_btn.setFixedSize(20, 20)
        close_plot_btn.setStyleSheet("background: transparent; color: #94A3B8; border: none; font-weight: bold;")
        close_plot_btn.clicked.connect(lambda: self.plot_frame.setVisible(False))
        plot_header.addWidget(close_plot_btn)
        plot_box_layout.addLayout(plot_header)
        
        self.canvas = MplCanvas(self, width=5, height=3, dpi=100)
        plot_box_layout.addWidget(self.canvas)
        self.calc_layout.addWidget(self.plot_frame)

        # DISPLAY MONITOR
        self.display_frame = QFrame()
        self.display_layout = QVBoxLayout(self.display_frame)
        self.display_frame.setMinimumHeight(120)
        self.display_layout.setContentsMargins(20, 15, 20, 15)
        
        self.formula_preview = QLabel("")
        self.display_layout.addWidget(self.formula_preview)
        
        self.display_area = QTextEdit()
        self.display_area.setReadOnly(False) 
        self.display_area.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 
        self.display_area.setPlaceholderText("0")
        self.display_area.setFrameStyle(QFrame.Shape.NoFrame)
        self.display_area.setMaximumHeight(70)
        self.display_area.installEventFilter(self)
        self.display_layout.addWidget(self.display_area)
        self.calc_layout.addWidget(self.display_frame)

        # KEYPADS
        self.keypad_stack = QStackedWidget()
        self.keypad_stack.addWidget(self._build_standard_keypad())
        self.keypad_stack.addWidget(self._build_scientific_keypad())
        self.keypad_stack.addWidget(self._build_programmer_keypad())
        self.keypad_stack.addWidget(self._build_matrix_keypad())
        self.keypad_stack.addWidget(self._build_statistics_keypad())
        self.keypad_stack.addWidget(self._build_converter_keypad())
        self.calc_layout.addWidget(self.keypad_stack)
        
        self.root_layout.addWidget(self.calc_container, stretch=4)

        # --- RIGHT FREEFORM NOTEPAD DRAWER (WITH EXPORT ENGINE) ---
        self.workspace_frame = QFrame()
        self.workspace_frame.setFixedWidth(280)
        ws_layout = QVBoxLayout(self.workspace_frame)
        ws_layout.setContentsMargins(12, 16, 12, 16)
        
        ws_title_bar = QHBoxLayout()
        ws_title_bar.addWidget(QLabel("📝 Notepad Workspace"))
        self.clear_ws_btn = QPushButton("Clear")
        self.clear_ws_btn.setFixedSize(45, 24)
        self.clear_ws_btn.setStyleSheet("font-size: 11px; background-color: #EF4444; color: white; border: none; border-radius: 4px;")
        self.clear_ws_btn.clicked.connect(self._clear_notebook_data)
        ws_title_bar.addWidget(self.clear_ws_btn)
        ws_layout.addLayout(ws_title_bar)
        
        self.notepad_edit = QTextEdit()
        self.notepad_edit.setAcceptRichText(False)
        self.notepad_edit.setText(self.workspace_manager.get_notes())
        self.notepad_edit.textChanged.connect(self._on_notepad_content_changed)
        ws_layout.addWidget(self.notepad_edit)
        
        self.export_session_btn = QPushButton("💾 Export Engineering Log")
        self.export_session_btn.setMinimumHeight(32)
        self.export_session_btn.clicked.connect(self._export_full_session)
        ws_layout.addWidget(self.export_session_btn)
        
        self.root_layout.addWidget(self.workspace_frame)
        self.workspace_frame.setVisible(False)  
        
        self._refresh_history_ui()
        self._apply_theme_styles()

    def eventFilter(self, obj, event) -> bool:
        if obj is self.display_area and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._handle_button_click("=")
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        text = event.text()
        
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._handle_button_click("=")
            event.accept()
        elif key == Qt.Key.Key_Backspace:
            self._handle_button_click("⌫")
            event.accept()
        elif key == Qt.Key.Key_Escape:
            self._handle_button_click("AC")
            event.accept()
        elif text in "0123456789.+-^%(),[] abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ→":
            self._insert_text_at_cursor(text)
            event.accept()
        elif text == "*":
            self._insert_text_at_cursor("×")
            event.accept()
        elif text == "/":
            self._insert_text_at_cursor("÷")
            event.accept()
        else:
            super().keyPressEvent(event)

    def _insert_text_at_cursor(self, text: str) -> None:
        cursor = self.display_area.textCursor()
        cursor.insertText(text)
        self.display_area.setFocus()

    def _toggle_sidebar_navigation(self, checked: bool) -> None:
        self.sidebar_frame.setVisible(checked)

    def _trigger_voice_typing(self) -> None:
        self.voice_type_btn.setText("Recording...")
        self.voice_type_btn.setEnabled(False)
        
        self.voice_thread = VoiceWorker()
        self.voice_thread.status_signal.connect(lambda msg: self.formula_preview.setText(msg))
        self.voice_thread.finished_signal.connect(self._on_voice_finished)
        self.voice_thread.start()

    def _on_voice_finished(self, text: str) -> None:
        self.voice_type_btn.setText("🎙️ Voice Input")
        self.voice_type_btn.setEnabled(True)
        if text.startswith("ERROR:"):
            self.formula_preview.setText(text)
        else:
            self._insert_text_at_cursor(text)
            self.formula_preview.setText(f"Voice Registered: '{text}'")

    def _trigger_image_calculation(self) -> None:
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Image Math Input")
        msg_box.setText("Choose an image source:")
        msg_box.setStyleSheet(f"background-color: {self.theme_colors['SURFACE']}; color: {self.theme_colors['TEXT_MAIN']};")
        
        gallery_btn = msg_box.addButton("📁 Choose from Device", QMessageBox.ButtonRole.ActionRole)
        camera_btn = msg_box.addButton("📷 Take a Picture", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton(QMessageBox.StandardButton.Cancel)
        msg_box.exec()
        
        target_file_path = None
        if msg_box.clickedButton() == gallery_btn:
            target_file_path, _ = QFileDialog.getOpenFileName(self, "Open Math Image File", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        elif msg_box.clickedButton() == camera_btn:
            target_file_path = self._capture_from_camera()
            
        if target_file_path:
            self._process_ocr_calculation(target_file_path)

    def _capture_from_camera(self) -> str:
        self.formula_preview.setText("📷 Launching Viewfinder Stream... Press SPACE or ENTER to snapshot.")
        self.centralWidget().repaint()
        
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("No working camera hardware detected.")
        except Exception as e:
            QMessageBox.critical(self, "Hardware Error", f"Could not access webcam device:\n{str(e)}")
            self.formula_preview.setText("Camera Error: Check connection.")
            return None
            
        captured_path = "camera_snapshot.png"
        while True:
            ret, frame = cap.read()
            if not ret: break
            h, w, _ = frame.shape
            cv2.rectangle(frame, (int(w*0.1), int(h*0.3)), (int(w*0.9), int(h*0.7)), (37, 99, 235), 2)
            cv2.putText(frame, "Align Math Equation Here - Press SPACE to capture", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("NovaCalc Viewfinder View - Press Space/Enter to Capture", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key in (32, 13):
                _, raw_frame = cap.read()
                cv2.imwrite(captured_path, raw_frame)
                break
            elif key == 27:
                captured_path = None
                break
        cap.release()
        cv2.destroyAllWindows()
        return captured_path

    def _process_ocr_calculation(self, file_path: str) -> None:
        self.formula_preview.setText("🌐 Querying Cloud OCR API Frame...")
        self.centralWidget().repaint()
        try:
            url = "https://api.ocr.space/parse/image"
            with open(file_path, 'rb') as f:
                payload = {'apikey': 'helloworld', 'language': 'eng', 'isOverlayRequired': False, 'scale': True, 'OCREngine': '2'}
                files = {'file': f}
                response = requests.post(url, data=payload, files=files, timeout=7).json()
                
            if "camera_snapshot.png" in file_path and os.path.exists(file_path):
                os.remove(file_path)
                
            if response and "ParsedResults" in response and len(response["ParsedResults"]) > 0:
                parsed_string = response["ParsedResults"][0]["ParsedText"].strip()
                cleaned_math = parsed_string.replace("|", "").replace("\r", "").replace("\n", " ").replace("x", "×").replace("/", "÷")
                cleaned_math = "".join(cleaned_math.split())  
                if cleaned_math:
                    self.display_area.setText(cleaned_math)
                    self._handle_button_click("=")
                else:
                    self.formula_preview.setText("OCR Error: Text matching yield returned empty.")
            else:
                self.formula_preview.setText("OCR Error: Remote service failed to process.")
        except Exception as e:
            self.formula_preview.setText(f"Network Failure: Check connection. ({str(e)})")

    def _update_graph_visualization(self, expression: str) -> bool:
        if 'x' not in expression.lower():
            return False
        expr = expression.lower().replace('×', '*').replace('÷', '/').replace('^', '**').replace('²', '**2').replace('³', '**3')
        allowed_words = {'x': 0, 'sin': np.sin, 'cos': np.cos, 'tan': np.tan, 'log': np.log10, 'ln': np.log, 'sqrt': np.sqrt, 'pi': np.pi, 'e': np.e}
        try:
            x_vals = np.linspace(-10, 10, 400)
            y_vals = []
            for x in x_vals:
                allowed_words['x'] = x
                y_val = eval(expr, {"__builtins__": None}, allowed_words)
                y_vals.append(y_val)
                
            self.canvas.axes.clear()
            self.canvas.axes.plot(x_vals, y_vals, color='#2563EB', linewidth=2.5, label=f"y = {expression}")
            self.canvas.axes.axhline(0, color='#475569', linewidth=1)
            self.canvas.axes.axvline(0, color='#475569', linewidth=1)
            self.canvas.axes.grid(True, color='#334155', linestyle='--', linewidth=0.5)
            self.canvas.axes.legend(facecolor='#1E293B', edgecolor='#475569', labelcolor='#FFFFFF')
            self.canvas.draw()
            self.plot_frame.setVisible(True)
            return True
        except:
            return False

    def _export_full_session(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Workspace Log", "", "Markdown Document (*.md);;Plain Text (*.txt)")
        if not file_path:
            return
            
        try:
            records = self.history_manager.get_all_records()
            notes = self.notepad_edit.toPlainText()
            
            document_payload = [
                "# NovaCalc Professional Engineering Session Log\n",
                "## 📜 Verified Calculation Thread History",
                "" if records else "* No expressions logged this session.",
            ]
            for item in records:
                document_payload.append(f"- `{item}`")
                
            document_payload.extend([
                "\n---",
                "## 📝 Workspace Scratchpad Notes",
                notes if notes.strip() else "* Scratchpad left unwritten."
            ])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(document_payload))
                
            QMessageBox.information(self, "Export Complete", "Your full engineering log has been saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Failure", f"Failed to save document record:\n{str(e)}")

    def _build_standard_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(8); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('AC', 0, 0, 'functional'), ('±', 0, 1, 'operator'), ('%', 0, 2, 'operator'), ('÷', 0, 3, 'operator'),
            ('7', 1, 0, 'num'),         ('8', 1, 1, 'num'),      ('9', 1, 2, 'num'),      ('×', 1, 3, 'operator'),
            ('4', 2, 0, 'num'),         ('5', 2, 1, 'num'),      ('6', 2, 2, 'num'),      ('-', 2, 3, 'operator'),
            ('1', 3, 0, 'num'),         ('2', 3, 1, 'num'),      ('3', 3, 2, 'num'),      ('+', 3, 3, 'operator'),
            ('⌫', 4, 0, 'functional'),  ('0', 4, 1, 'num'),      ('.', 4, 2, 'num'),      ('=', 4, 3, 'accent')
        ]
        for txt, r, c, t in blueprint:
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(55); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c)
        return w

    def _build_scientific_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(6); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('sin', 0, 0, 'sci'),   ('cos', 0, 1, 'sci'),   ('tan', 0, 2, 'sci'),   ('x', 0, 3, 'num'),       ('AC', 0, 4, 'functional'), ('⌫', 0, 5, 'functional'), ('÷', 0, 6, 'operator'),
            ('asin', 1, 0, 'sci'),  ('acos', 1, 1, 'sci'),  ('atan', 1, 2, 'sci'),  ('e', 1, 3, 'sci'),       ('7', 1, 4, 'num'),         ('8', 1, 5, 'num'),        ('9', 1, 6, 'num'),       ('×', 1, 7, 'operator'),
            ('log', 2, 0, 'sci'),   ('ln', 2, 1, 'sci'),    ('√', 2, 2, 'sci'),     (',', 2, 3, 'util'),      ('4', 2, 4, 'num'),         ('5', 2, 5, 'num'),        ('6', 2, 6, 'num'),       ('-', 2, 7, 'operator'),
            ('x²', 3, 0, 'sci'),    ('x³', 3, 1, 'sci'),    ('xʸ', 3, 2, 'sci'),    ('RAD', 3, 3, 'util'),    ('1', 3, 4, 'num'),         ('2', 3, 5, 'num'),        ('3', 3, 6, 'num'),       ('+', 3, 7, 'operator'),
            ('(', 4, 0, 'sci'),     (')', 4, 1, 'sci'),     ('Ans', 4, 2, 'sci'),   ('EXP', 4, 3, 'sci'),     ('.', 4, 4, 'num'),         ('0', 4, 5, 'num'),                                   ('=', 4, 6, 'accent', 1, 2)
        ]
        for item in blueprint:
            txt, r, c, t = item[0], item[1], item[2], item[3]
            rs, cs = (item[4], item[5]) if len(item) > 4 else (1, 1)
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(50); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c, rs, cs)
        return w

    def _build_programmer_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(8); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('HEX', 0, 0, 'util'),  ('DEC', 0, 1, 'util'),  ('OCT', 0, 2, 'util'),  ('BIN', 0, 3, 'util'),
            ('AND', 1, 0, 'sci'),   ('OR', 1, 1, 'sci'),    ('XOR', 1, 2, 'sci'),   ('NOT', 1, 3, 'operator'),
            ('<<', 2, 0, 'sci'),    ('>>', 2, 1, 'sci'),    ('A', 2, 2, 'num'),     ('B', 2, 3, 'num'),
            ('C', 3, 0, 'num'),     ('D', 3, 1, 'num'),     ('E', 3, 2, 'num'),     ('F', 3, 3, 'num'),
            ('AC', 4, 0, 'functional'), ('⌫', 4, 1, 'functional'), ('0', 4, 2, 'num'), ('=', 4, 3, 'accent')
        ]
        for txt, r, c, t in blueprint:
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(52); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c)
        return w

    def _build_matrix_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(8); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('New Matrix', 0, 0, 'util'),   ('Determinant', 0, 1, 'sci'), ('Transpose', 0, 2, 'sci'),
            ('[', 1, 0, 'num'),             (']', 1, 1, 'num'),           (',', 1, 2, 'util'),
            ('7', 2, 0, 'num'),             ('8', 2, 1, 'num'),           ('9', 2, 2, 'num'),
            ('4', 3, 0, 'num'),             ('5', 3, 1, 'num'),           ('6', 3, 2, 'num'),
            ('AC', 4, 0, 'functional'),     ('1', 4, 1, 'num'),           ('=', 4, 2, 'accent')
        ]
        for txt, r, c, t in blueprint:
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(52); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c)
        return w

    def _build_statistics_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(8); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('Mean', 0, 0, 'sci'),       ('Median', 0, 1, 'sci'),     ('Variance', 0, 2, 'sci'),
            ('Std Dev', 1, 0, 'sci'),    (',', 1, 1, 'util'),         ('(', 1, 2, 'num'),
            ('7', 2, 0, 'num'),          ('8', 2, 1, 'num'),          ('9', 2, 2, 'num'),
            ('4', 3, 0, 'num'),          ('5', 3, 1, 'num'),          ('6', 3, 2, 'num'),
            ('AC', 4, 0, 'functional'),  (')', 4, 1, 'num'),          ('=', 4, 2, 'accent')
        ]
        for txt, r, c, t in blueprint:
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(52); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c)
        return w

    def _build_converter_keypad(self) -> QWidget:
        w = QWidget(); g = QGridLayout(w); g.setSpacing(8); g.setContentsMargins(0,0,0,0)
        blueprint = [
            ('C to F', 0, 0, 'util'),      ('F to C', 0, 1, 'util'),      ('M to KM', 0, 2, 'util'),
            ('KM to M', 1, 0, 'util'),     (' ', 1, 1, 'num'),            ('→', 1, 2, 'operator'),
            ('7', 2, 0, 'num'),            ('8', 2, 1, 'num'),            ('9', 2, 2, 'num'),
            ('4', 3, 0, 'num'),            ('5', 3, 1, 'num'),            ('6', 3, 2, 'num'),
            ('AC', 4, 0, 'functional'),    ('0', 4, 1, 'num'),            ('=', 4, 2, 'accent')
        ]
        for txt, r, c, t in blueprint:
            btn = QPushButton(txt); btn.setProperty("type", t); btn.setMinimumHeight(52); btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, token=txt: self._handle_button_click(token))
            g.addWidget(btn, r, c)
        return w

    def _switch_calculator_mode(self, idx: int) -> None:
        for i, btn in enumerate(self.mode_buttons): 
            btn.setChecked(i == idx)
        self.keypad_stack.setCurrentIndex(idx)
        self._apply_theme_styles()

    def _toggle_workspace_drawer(self, checked):
        self.workspace_frame.setVisible(checked)

    def _on_notepad_content_changed(self):
        self.workspace_manager.save_notes(self.notepad_edit.toPlainText())

    def _clear_notebook_data(self):
        self.workspace_manager.clear_all()
        self.notepad_edit.clear()

    def _on_history_item_clicked(self, item):
        text = item.text()
        if " = " in text:
            self.display_area.setText(text.split(" = ")[0])

    def _refresh_history_ui(self) -> None:
        self.history_list_widget.clear()
        for record in self.history_manager.get_all_records():
            self.history_list_widget.addItem(record)

    def _open_settings_modal(self):
        def dynamic_theme_hook(new_theme):
            self.current_theme_mode = new_theme
            self.theme_colors = ThemeEngine.get_palette(new_theme)
            self._apply_theme_styles()
        modal = SettingsModal(self, self.current_theme_mode, dynamic_theme_hook)
        modal.exec()

    def _apply_theme_styles(self) -> None:
        colors = self.theme_colors
        self.setStyleSheet(f"QMainWindow {{ background-color: {colors['BACKGROUND']}; }} QWidget {{ color: {colors['TEXT_MAIN']}; font-family: 'Segoe UI'; }} QFrame {{ background-color: {colors['SURFACE']}; border: none; }}")
        
        self.sidebar_frame.setStyleSheet(f"background-color: {colors['SURFACE']}; border-right: 1px solid {colors['SURFACE_ALT']};")
        self.display_frame.setStyleSheet(f"background-color: {colors['SURFACE']}; border-radius: {CORNER_RADIUS}px; border: 1px solid {colors['SURFACE_ALT']};")
        self.formula_preview.setStyleSheet(f"color: {colors['TEXT_MUTED']}; font-family: 'Consolas'; font-size: 14px;")
        self.display_area.setStyleSheet(f"background-color: transparent; color: {colors['TEXT_MAIN']}; font-family: 'Consolas'; font-size: 32px; selection-background-color: {colors['PRIMARY']};")
        self.workspace_frame.setStyleSheet(f"background-color: {colors['SURFACE']}; border-left: 1px solid {colors['SURFACE_ALT']};")
        self.notepad_edit.setStyleSheet(f"background-color: {colors['BACKGROUND']}; border: 1px solid {colors['SURFACE_ALT']}; border-radius: 6px; font-family: 'Consolas'; font-size: 13px; color: {colors['TEXT_MAIN']}; padding: 8px;")
        self.history_list_widget.setStyleSheet(f"background-color: {colors['BACKGROUND']}; border: 1px solid {colors['SURFACE_ALT']}; border-radius: 6px; font-family: 'Consolas'; font-size: 11px; color: {colors['TEXT_MUTED']};")
        self.plot_frame.setStyleSheet(f"background-color: {colors['SURFACE']}; border: 1px solid {colors['SURFACE_ALT']}; border-radius: {CORNER_RADIUS}px;")
        self.export_session_btn.setStyleSheet(f"background-color: {colors['PRIMARY']}; color: white; border-radius: 4px; font-weight: bold;")

        self.menu_btn.setStyleSheet(f"QPushButton {{ background-color: {colors['PRIMARY'] if self.menu_btn.isChecked() else colors['SURFACE']}; color: white; border: 1px solid {colors['SURFACE_ALT']}; border-radius: 6px; font-size: 16px; font-weight: bold; }}")
        self.voice_type_btn.setStyleSheet(f"QPushButton {{ background-color: {colors['SURFACE']}; border: 1px solid {colors['SURFACE_ALT']}; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}")
        self.image_calc_btn.setStyleSheet(f"QPushButton {{ background-color: {colors['SURFACE']}; border: 1px solid {colors['SURFACE_ALT']}; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}")
        self.workspace_toggle.setStyleSheet(f"QPushButton {{ background-color: {colors['PRIMARY'] if self.workspace_toggle.isChecked() else colors['SURFACE']}; border: 1px solid {colors['SURFACE_ALT']}; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}")

        for i, btn in enumerate(self.mode_buttons):
            btn.setStyleSheet(f"QPushButton {{ background-color: {colors['PRIMARY'] if btn.isChecked() else 'transparent'}; color: {'#FFFFFF' if btn.isChecked() else colors['TEXT_MAIN']}; border: none; border-radius: 6px; padding-left: 12px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background-color: {colors['SURFACE_ALT'] if not btn.isChecked() else colors['PRIMARY']}; }}")
            
        for btn in self.findChildren(QPushButton):
            t = btn.property("type")
            if not t: continue
            bg, fg = colors['SURFACE'], colors['TEXT_MAIN']
            if t == 'accent': bg, fg = colors['PRIMARY'], "#FFFFFF"
            elif t == 'operator': bg, fg = colors['OPERATOR'], colors['ACCENT']
            elif t == 'functional': bg, fg = colors['FUNCTIONAL'], colors['ERROR']
            elif t == 'sci': bg, fg = colors['OPERATOR'], colors['PRIMARY']
            elif t == 'util': bg, fg = colors['SURFACE_ALT'], colors['TEXT_MUTED']
            btn.setStyleSheet(f"QPushButton {{ background-color: {bg}; color: {fg}; border-radius: 8px; font-size: 14px; font-weight: bold; }} QPushButton:hover {{ background-color: {colors['SURFACE_ALT']}; }}")

    def _handle_button_click(self, token: str) -> None:
        if not hasattr(self, 'display_area'): return
        
        if token == "AC":
            self.display_area.clear()
            self.formula_preview.clear()
            self.plot_frame.setVisible(False)
        elif token == "⌫":
            cursor = self.display_area.textCursor()
            cursor.deletePreviousChar()
        elif token in ("Mean", "Median", "Variance", "Std Dev"):
            self._insert_text_at_cursor(f"{token.lower().replace(' ', '')}(")
        elif token == "New Matrix":
            self._insert_text_at_cursor("[[1,2],[3,4]]")
        elif token in ("Determinant", "Transpose"):
            prefix = "det" if token == "Determinant" else "trans"
            txt = self.display_area.toPlainText()
            self.display_area.setText(f"{prefix}({txt})")
        elif token in ("C to F", "F to C", "M to KM", "KM to M"):
            unit_parts = token.lower().split(" to ")
            self.display_area.setText(f"10 {unit_parts[0]} to {unit_parts[1]}")
        elif token in ("HEX", "DEC", "OCT", "BIN"):
            try:
                val = int(self.display_area.toPlainText())
                if token == "HEX": self.display_area.setText(hex(val))
                elif token == "BIN": self.display_area.setText(bin(val))
                elif token == "OCT": self.display_area.setText(oct(val))
                else: self.display_area.setText(str(val))
            except:
                self.display_area.setText("Enter Integer First")
        elif token in ("sin", "cos", "tan", "log", "ln", "asin", "acos", "atan"):
            self._insert_text_at_cursor(f"{token}(")
        elif token in ("x²", "x³", "xʸ"):
            suffix = "²" if token == "x²" else "³" if token == "x³" else "^"
            self._insert_text_at_cursor(suffix)
        elif token == "√":
            self._insert_text_at_cursor("√(")
        elif token == "±":
            txt = self.display_area.toPlainText()
            self.display_area.setText(txt[1:] if txt.startswith("-") else "-" + txt)
        elif token == "=":
            current_text = self.display_area.toPlainText()
            is_graph = self._update_graph_visualization(current_text)
            
            if is_graph:
                self.formula_preview.setText(f"Graphed Expression: {current_text}")
            else:
                result = CalculatorLogic.evaluate_expression(current_text)
                self.formula_preview.setText(current_text)
                self.display_area.setText(result)
                self.history_manager.add_record(current_text, result)
                self._refresh_history_ui()
        else:
            self._insert_text_at_cursor(token)

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())