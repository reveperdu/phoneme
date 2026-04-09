import re

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from api import abort, config, textcomp_stream

subs_dict = {
    "full-width quotes to half-width": {r"“|”": r'"'},
    "half-width quotes to full-width": {r"\"(.*?)\"", r"“\1”"},
}
# ui layout
app = QApplication()
window = QWidget()
maintext = QPlainTextEdit()
inputtext = QLineEdit()
# the combo will be put inside a separate dialog, probably after using class for ui
combo = QComboBox()
layout_main = QVBoxLayout()
bsubs = QPushButton("regex replace")
bsend = QPushButton("send")
bretry = QPushButton("retry")
babort = QPushButton("abort")
layout_buttons = QHBoxLayout()
window.setLayout(layout_main)
for btn in [babort, bretry, bsend]:
    layout_buttons.addWidget(btn)
layout_main.addWidget(maintext)
layout_main.addLayout(layout_buttons)
layout_main.addWidget(inputtext)
combo.addItems(list(subs_dict.keys()))
window.show()
# stream timer
tstream = QTimer()

# logic
no_think = True
is_retry = False


def dict_replace(s: str, d: dict):
    for k in d:
        s = s.replace(k, d[k])
    return s


def text_cb():
    param = combo.currentText()
    newtext = maintext.toPlainText()
    d = subs_dict[param]
    for k in d:
        newtext = re.sub(k, d[k], newtext)
    maintext.setPlainText(newtext)


def send():
    global current_stream, last_context
    context = maintext.toPlainText()
    last_context = context
    inputmsg = inputtext.text()
    is_new_turn = True if inputmsg != "" else False
    if is_new_turn:
        context = context + "\n{{[INPUT]}}\n" + inputmsg + "\n{{[OUTPUT]}}\n"
        last_context = context
    d = config["chat_template"]
    prom = context
    if no_think:
        s1, s2, s3 = prom.rpartition("\n{{[OUTPUT]}}\n")
        prom = s1 + s2 + config["nothink_tag"] + s3
    for k in d:
        prom = prom.replace(k, d[k])
    inputtext.clear()
    maintext.setPlainText(context)
    maintext.moveCursor(QTextCursor.MoveOperation.End)
    current_stream = textcomp_stream(prom)
    tstream.start()


def retry():
    global is_retry
    is_retry = True
    maintext.setPlainText(last_context)
    send()
    is_retry = False


def stream_tick():
    chunk = next(current_stream, None)
    if chunk is not None:
        # "append" gives extra newline
        maintext.moveCursor(QTextCursor.MoveOperation.End)
        maintext.insertPlainText(chunk)
    else:
        tstream.stop()


# ui events
bsubs.clicked.connect(text_cb)
bsend.clicked.connect(send)
bretry.clicked.connect(retry)
babort.clicked.connect(abort)
tstream.setInterval(100)
tstream.timeout.connect(stream_tick)
inputtext.returnPressed.connect(send)
# exec
maintext.setPlainText(config["default_prompt"])
app.exec()
