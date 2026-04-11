import sys
import threading

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject, QPoint

from kurAI2 import (
    get_response,
    search_wikipedia,
    format_response,
    humanize,
    is_factual_question,
    load_data,
    save_data
)

data = load_data()

# ------------------ SIGNALS ------------------

class SignalBus(QObject):
    message_signal = Signal(str, bool)

signals = SignalBus()

# ------------------ APP ------------------

app = QApplication(sys.argv)

class KurAI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("KurAI")
        self.resize(850, 900)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #0B0B10;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # ------------------ TITLE BAR ------------------

        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(50)
        self.title_bar.setStyleSheet("""
            background-color: #12121A;
            border-bottom: 1px solid #1C1C2A;
        """)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        self.title = QLabel("KurAI")
        self.title.setStyleSheet("color: #A8A8E6; font-size: 16px; font-weight: bold;")

        self.btn_min = QPushButton("—")
        self.btn_close = QPushButton("✕")

        for b in [self.btn_min, self.btn_close]:
            b.setFixedSize(32, 28)
            b.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: white;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #2A2A3D;
                }
            """)

        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #FF4D4D;
            }
        """)

        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)

        title_layout.addWidget(self.title)
        title_layout.addStretch()
        title_layout.addWidget(self.btn_min)
        title_layout.addWidget(self.btn_close)

        self.layout.addWidget(self.title_bar)

        # ------------------ CHAT ------------------

        self.chat_area = QVBoxLayout()
        self.chat_area.addStretch()

        container = QWidget()
        container.setLayout(self.chat_area)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(container)
        self.scroll.setStyleSheet("border: none;")

        self.layout.addWidget(self.scroll)

        # ------------------ INPUT ------------------

        bottom = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Écris ton message...")
        self.input.returnPressed.connect(self.send_message)
        self.input.setStyleSheet("""
            QLineEdit {
                background-color: #151522;
                border: 1px solid #A8A8E6;
                padding: 10px;
                border-radius: 10px;
                color: white;
            }
        """)

        send_btn = QPushButton("Envoyer")
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #A8A8E6;
                padding: 10px;
                border-radius: 10px;
                color: black;
                font-weight: bold;
            }
        """)

        bottom.addWidget(self.input)
        bottom.addWidget(send_btn)

        self.layout.addLayout(bottom)

        # ------------------ SIGNAL ------------------
        signals.message_signal.connect(self.add_message)

        # ------------------ DRAG FIX (IMPORTANT) ------------------
        self.title_bar.mousePressEvent = self.start_drag

    # ------------------ DRAG (PRO METHOD) ------------------

    def start_drag(self, event):
        if self.windowHandle():
            self.windowHandle().startSystemMove()

    # ------------------ CHAT UI ------------------

    def add_message(self, text, user=False):
        label = QLabel(text)
        label.setWordWrap(True)

        label.setStyleSheet(f"""
            background-color: {'#1F1C3A' if user else '#151522'};
            padding: 12px;
            border-radius: 12px;
            margin: 5px;
            color: white;
        """)

        wrapper = QFrame()
        layout = QHBoxLayout(wrapper)

        if user:
            layout.addStretch()
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch()

        self.chat_area.insertWidget(self.chat_area.count() - 1, wrapper)

        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    # ------------------ SEND ------------------

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return

        self.input.clear()

        signals.message_signal.emit(text, True)

        threading.Thread(target=self.process_ai, args=(text,), daemon=True).start()

    def process_ai(self, text):
        response = get_response(text.lower(), data)

        if not response:
            wiki = search_wikipedia(text)
            if wiki:
                response_text = humanize(format_response(wiki))
            else:
                response_text = (
                    "Je ne sais pas encore 🤔"
                    if is_factual_question(text)
                    else "Pas sûr 😅"
                )
        else:
            response_text = response

        signals.message_signal.emit(response_text, False)


# ------------------ RUN ------------------

window = KurAI()
window.show()

sys.exit(app.exec())