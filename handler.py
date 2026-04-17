from typing import TYPE_CHECKING
from PySide6.QtGui import QTextCursor
from api import textcomp_stream, abort

if TYPE_CHECKING:
    from window import Window


class Handler:
    def __init__(self, w: "Window") -> None:
        self.w = w
        self.no_think = True
        self.is_retry = False
        self.config = self.w.config

    def send(self):
        context = self.w.maintext.toPlainText()
        self.last_context = context
        inputmsg = self.w.inputtext.text()
        is_new_turn = True if inputmsg != "" else False
        if is_new_turn:
            context = context + "\n{{[INPUT]}}\n" + inputmsg + "\n{{[OUTPUT]}}\n"
            self.last_context = context
        d = self.config["chat_template"]
        prom = context
        if self.no_think:
            s1, s2, s3 = prom.rpartition("\n{{[OUTPUT]}}\n")
            prom = s1 + s2 + self.config["nothink_tag"] + s3
        for k in d:
            prom = prom.replace(k, d[k])
        self.w.inputtext.clear()
        self.w.maintext.setPlainText(context)
        self.w.maintext.moveCursor(QTextCursor.MoveOperation.End)
        self.current_stream = textcomp_stream(
            prom, self.config["api_stream"], self.config["params"]
        )
        self.w.tstream.start()

    def retry(self):
        global is_retry
        is_retry = True
        self.w.maintext.setPlainText(self.last_context)
        self.send()
        is_retry = False

    def stream_tick(self):
        chunk = next(self.current_stream, None)
        if chunk is not None:
            # "append" gives extra newline
            self.w.maintext.moveCursor(QTextCursor.MoveOperation.End)
            self.w.maintext.insertPlainText(chunk)
        else:
            self.w.tstream.stop()

    def abort(self):
        abort(self.config["api_abort"])
