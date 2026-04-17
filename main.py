import json
from PySide6.QtWidgets import QApplication
from window import Window

TEST = 0
subs_dict = {
    "full-width quotes to half-width": {r"“|”": r'"'},
    "half-width quotes to full-width": {r"\"(.*?)\"", r"“\1”"},
}
app = QApplication()

with open("config.json") as f:
    config = json.load(f)

# setup ui & app
win = Window(config=config)
win.maintext.setPlainText(config["default_prompt"])
win.show()
# set dark mode
stylestr = "*{background:#303030;color:white}"
app.setStyleSheet(stylestr)
if TEST:
    testmsg = "你好呀"
    win.inputtext.insert(testmsg)
    win.send.click()
app.exec()
