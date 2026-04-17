import json
from PySide6.QtWidgets import QApplication
from window import Window

subs_dict = {
    "full-width quotes to half-width": {r"“|”": r'"'},
    "half-width quotes to full-width": {r"\"(.*?)\"", r"“\1”"},
}
# ui layout
app = QApplication()
# stream timer

with open("config.json") as f:
    config = json.load(f)

# ui events

# setup ui & app
win = Window(config=config)
win.maintext.setPlainText(config["default_prompt"])
win.show()
# set dark mode
stylestr = "*{background:#303030;color:white;font-size:16pt}"
app.setStyleSheet(stylestr)
app.exec()
