from handler import Handler
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Window(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.maintext = QPlainTextEdit()
        self.inputtext = QLineEdit()
        # the combo will be put inside a separate dialog, probably after using class for ui
        self.combo = QComboBox()
        layout_main = QVBoxLayout()
        self.subs = QPushButton("regex replace")
        self.send = QPushButton("send")
        self.retry = QPushButton("retry")
        self.abort = QPushButton("abort")
        layout_buttons = QHBoxLayout()
        self.setLayout(layout_main)
        for btn in [self.abort, self.retry, self.send]:
            layout_buttons.addWidget(btn)
        layout_main.addWidget(self.maintext)
        layout_main.addLayout(layout_buttons)
        layout_main.addWidget(self.inputtext)
        self.tstream = QTimer()
        self.setup_handler()

    def setup_handler(self):
        self.handler = Handler(self)
        self.send.clicked.connect(self.handler.send)
        self.retry.clicked.connect(self.handler.retry)
        self.abort.clicked.connect(self.handler.abort)
        self.tstream.setInterval(50)
        self.tstream.timeout.connect(self.handler.stream_tick)
        self.inputtext.returnPressed.connect(self.handler.send)
