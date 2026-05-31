from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from api import abort, completion_stream
from utils import make_subsdict,tool_call_generic
import json
import re
from dataclasses import dataclass
from typing import Iterator

@dataclass
class state:
    is_retry: bool = False
    current_stream: None | Iterator = None
    context: str = ""
    last_context: str = ""


class Window(QWidget):
    def __init__(self, config_path):
        super().__init__()
        self.setup_ui()
        self.config_path = config_path
        self.load_config()
        self.tstream = QTimer()
        self.state = state()
        self.setup_events()
        self.maintext.setPlainText(self.config["default_prompt"])

    def setup_ui(self):
        self.maintext = QPlainTextEdit()
        self.inputtext = QLineEdit()
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
        for btn in [self.breload, self.babort, self.bretry, self.bsend]:
            layout_buttons.addWidget(btn)
        layout_main.addWidget(self.maintext)
        layout_main.addLayout(layout_buttons)
        layout_main.addWidget(self.inputtext)

    def send(self):
        context = self.maintext.toPlainText()
        self.state.last_context = context
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
            self.state.current_stream = completion_stream(
                prom, self.config["api_stream"], self.config["params"]
            )
        self.maintext.moveCursor(QTextCursor.MoveOperation.End)
        self.inputtext.clear()
        self.maintext.setPlainText(context)
        self.tstream.start()

    def retry(self):
        self.state.is_retry = True
        self.maintext.setPlainText(self.state.last_context)
        self.send()
        self.state.is_retry = False

    def abort(self):
        abort(self.config["api_abort"])

    def stream_tick(self):
        assert self.state.current_stream is not None
        chunk = next(self.state.current_stream, None)
        if chunk is not None:
            # "append" gives extra newline
            self.maintext.moveCursor(QTextCursor.MoveOperation.End)
            self.maintext.insertPlainText(chunk)
            self.current_output+=chunk
        else:
            self.tstream.stop()
            self.output_postprocess()
    def load_config(self):
        with open(self.config_path) as f:
            config = json.load(f)
        self.config = config

    def setup_events(self):
        self.bsend.clicked.connect(self.send)
        self.bretry.clicked.connect(self.retry)
        self.babort.clicked.connect(self.abort)
        self.breload.clicked.connect(self.retry)
        self.tstream.setInterval(50)
        self.tstream.timeout.connect(self.stream_tick)
        self.inputtext.returnPressed.connect(self.send)
    def output_postprocess(self):
        t=self.config["chat_template"]
        pattern=t["tool_call_start"]+"(.*)"+t["tool_call_end"]
        tool_match=re.search(pattern,self.current_output)
        if tool_match:
            call=tool_match[1]
            result=tool_call_generic(call)
            #note two \n help suppress possible generation of tool response tag
            result=f"\n\n{t["tool_resp_start"]}{result}{t["tool_resp_end"]}\n"
            self.maintext.insertPlainText(result)
            #continue generation after tool returns
            self.send()