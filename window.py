from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QMenu,
    QFileDialog,
)
from utils import tool_call_generic
from rendermath import render_math
from api import abort_api, completion_stream_lcpp
import json
import re
import base64
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class State:
    is_retry: bool = False
    current_stream: None | Iterator = None
    context: str = ""
    last_context: str = ""
    current_input: str = ""
    current_output: str = ""
    should_abort: bool = False
    is_networking: bool = False
    status_string: str = "ready"
    available_status: tuple = ("ready", "GUI working", "networking", "streaming")
    images: list[str] = field(default_factory=list)


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
        self.statusdisplay = QLabel("ready")
        layout_main = QVBoxLayout()
        # unused
        # self.bsubs = QPushButton("regex replace")
        self.bsend = QPushButton("send")
        self.bretry = QPushButton("retry")
        self.babort = QPushButton("abort")
        self.bextra = QPushButton("extra")
        layout_buttons = QHBoxLayout()
        self.setLayout(layout_main)
        self.buttons = [
            self.bextra,
            self.babort,
            self.bretry,
            self.bsend,
        ]
        for btn in self.buttons:
            layout_buttons.addWidget(btn)
        layout_main.addWidget(self.maintext)
        layout_main.addWidget(self.statusdisplay)
        self.statusdisplay.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout_main.addLayout(layout_buttons)
        layout_main.addWidget(self.inputtext)
        self.extra_menu = QMenu()
        self.bextra.setMenu(self.extra_menu)
        extra_action1 = self.extra_menu.addAction("render math")
        extra_action1.triggered.connect(lambda: render_math(self.state.current_output))
        extra_action2 = self.extra_menu.addAction("reload")
        extra_action2.triggered.connect(self.load_config)
        extra_action3 = self.extra_menu.addAction("load image")
        extra_action3.triggered.connect(self.load_image)

    def send(self):
        # refactor tip: use state.context instead of context, and pass only state to api,
        # skipping "prom" and "mmdata"?
        if self.state.is_networking:
            print("ignored attempt to send request, a request is already active.")
            return
        self.update_status_text("GUI working")
        context = self.maintext.toPlainText()
        self.state.last_context = context
        self.state.current_output = ""
        inputmsg = self.inputtext.text()
        if inputmsg != "":
            is_new_turn = True
        else:
            is_new_turn = False
            self.state.current_input = "(None)"
        if is_new_turn:
            context = context + "\n{{[INPUT]}}\n" + inputmsg + "\n{{[OUTPUT]}}\n"
            self.state.last_context = context
            self.state.current_input = inputmsg
        d = self.config["chat_template"]
        prom = context
        if self.config["no_think"]:
            s1, s2, s3 = prom.rpartition("\n{{[OUTPUT]}}\n")
            prom = s1 + s2 + self.config["nothink_tag"] + s3
        for k in d:
            prom = prom.replace(k, d[k])
            if len(self.state.images) > 0:
                self.state.current_stream = completion_stream_lcpp(
                    prom,
                    self.config["api_stream"],
                    self.config["params"],
                    self.state,
                    self.state.images,
                )
            else:
                self.state.current_stream = completion_stream_lcpp(
                    prom,
                    self.config["api_stream"],
                    self.config["params"],
                    self.state,
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

    def update_status_text(self, status: str):
        if status in self.state.available_status:
            self.state.status_string = status
            self.statusdisplay.setText(status)
        else:
            print("warning, trying to set unavailable status ", status)
            return

    def retry(self):
        if self.state.is_networking:
            print("ignored attempt to send request, a request is already active.")
            return
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
        self.tstream.setInterval(50)
        self.tstream.timeout.connect(self.stream_tick)
        self.inputtext.returnPressed.connect(self.send)

    def output_finalize(self):
        self.handle_toolcall()
        self.output_log()
        self.state.is_networking = False
        self.update_status_text("ready")
        self.update_window_state()

    def load_image(self):
        fpath = QFileDialog.getOpenFileName()[0]
        with open(fpath, "rb") as f:
            base64_str = base64.b64encode(f.read()).decode("utf-8")
        self.state.images.append(base64_str)

    def handle_toolcall(self):
        # stale. standard agentic workflow possibly out of scope.
        t = self.config["chat_template"]
        if ("tool_call_start" not in t) or ("tool_call_end" not in t):
            return
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

    def output_log(self):
        print(">", self.state.current_input)
        print(self.state.current_output)
        print()

    def update_window_state(self):
        pass
