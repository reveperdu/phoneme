from PySide6.QtCore import QTimer,Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from utils import make_subsdict, tool_call_generic
from api import abort_api, completion_stream_lcpp
import json
import re
from dataclasses import dataclass
from typing import Iterator


@dataclass
class State:
    is_retry: bool = False
    current_stream: None | Iterator = None
    context: str = ""
    last_context: str = ""
    current_output: str = ""
    should_abort: bool = False
    is_networking: bool = False
    status_string: str= "ready"
    available_status:tuple=("ready","GUI working","networking","streaming")

class Window(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setup_ui()
        self.config_path = config_path
        self.load_config()
        self.tstream = QTimer()
        self.state = State()
        self.setup_events()
        self.maintext.setPlainText(self.config["default_prompt"])

    def setup_ui(self):
        self.maintext = QPlainTextEdit()
        self.inputtext = QLineEdit()
        self.statusdisplay=QLabel("ready")
        # the combo will be put inside a separate dialog, probably after using class for ui
        self.combo = QComboBox()
        layout_main = QVBoxLayout()
        self.bsubs = QPushButton("regex replace")
        self.bsend = QPushButton("send")
        self.bretry = QPushButton("retry")
        self.babort = QPushButton("abort")
        self.breload = QPushButton("reload")
        layout_buttons = QHBoxLayout()
        self.setLayout(layout_main)
        self.active_buttons = [self.breload, self.babort, self.bretry, self.bsend]
        for btn in self.active_buttons:
            layout_buttons.addWidget(btn)
        layout_main.addWidget(self.maintext)
        layout_main.addWidget(self.statusdisplay)
        self.statusdisplay.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_main.addLayout(layout_buttons)
        layout_main.addWidget(self.inputtext)

    def send(self):
        self.update_status_text("GUI working")
        context = self.maintext.toPlainText()
        self.state.last_context = context
        self.state.current_output = ""
        inputmsg = self.inputtext.text()
        is_new_turn = True if inputmsg != "" else False
        if is_new_turn:
            context = context + "\n{{[INPUT]}}\n" + inputmsg + "\n{{[OUTPUT]}}\n"
            self.state.last_context = context
        d = make_subsdict(self.config)
        prom = context
        if self.config["no_think"]:
            s1, s2, s3 = prom.rpartition("\n{{[OUTPUT]}}\n")
            prom = s1 + s2 + self.config["nothink_tag"] + s3
        for k in d:
            prom = prom.replace(k, d[k])
        self.state.current_stream = completion_stream_lcpp(
                prom, self.config["api_stream"], self.config["params"], self.state
            )
        # move cursor to end should put at the end because clear
        # and setting text may also move cursor
        self.inputtext.clear()
        self.maintext.setPlainText(context)
        self.maintext.moveCursor(QTextCursor.MoveOperation.End)
        self.update_status_text("networking")
        self.state.is_networking = True
        self.update_window_state()
        self.tstream.start()
    def update_status_text(self,status:str):
        if status in self.state.available_status:
            self.state.status_string=status
            self.statusdisplay.setText(status)
        else:
            print("warning, trying to set unavailable status ", status)
            return
        
    def retry(self):
        self.state.is_retry = True
        self.maintext.setPlainText(self.state.last_context)
        self.send()
        self.state.is_retry = False

    def abort(self):
        # lcpp server does not have a abort endpoint
        # aborting is done by closing connection
        if self.config["api_abort"] != "":
            abort_api(self.config["api_abort"])
        self.state.should_abort = True

    def stream_tick(self):
        assert self.state.current_stream is not None
        chunk = next(self.state.current_stream, None)
        self.update_status_text("streaming")
        if chunk is not None:
            # "append" gives extra newline
            self.maintext.moveCursor(QTextCursor.MoveOperation.End)
            self.maintext.insertPlainText(chunk)
            self.state.current_output += chunk
        else:
            self.tstream.stop()
            self.output_finalize()

    def load_config(self):
        with open(self.config_path) as f:
            config = json.load(f)
        self.config = config

    def setup_events(self):
        self.bsend.clicked.connect(self.send)
        self.bretry.clicked.connect(self.retry)
        self.babort.clicked.connect(self.abort)
        self.breload.clicked.connect(self.load_config)
        self.tstream.setInterval(50)
        self.tstream.timeout.connect(self.stream_tick)
        self.inputtext.returnPressed.connect(self.send)

    def output_finalize(self):
        t = self.config["chat_template"]
        pattern = t["tool_call_start"] + "(.*)" + t["tool_call_end"]
        is_tool_match = re.search(pattern, self.state.current_output)
        if is_tool_match:
            call = is_tool_match[1]
            result = tool_call_generic(call)
            # note two \n help suppress possible generation of tool response tag
            result = f"\n\n{t['tool_resp_start']}{result}{t['tool_resp_end']}\n"
            self.maintext.insertPlainText(result)
            # continue generation after tool returns
            self.send()
        self.state.is_networking = False
        self.update_status_text("ready")
        self.update_window_state()

    def update_window_state(self):
        if self.state.is_networking:
            for btn in self.active_buttons:
                if btn != self.babort:
                    btn.setEnabled(False)
        if not self.state.is_networking:
            for btn in self.active_buttons:
                if btn != self.babort:
                    btn.setEnabled(True)
