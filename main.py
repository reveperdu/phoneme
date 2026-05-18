from PySide6.QtWidgets import QApplication
from window import Window

subs_dict = {
    "full-width quotes to half-width": {r"“|”": r'"'},
    "half-width quotes to full-width": {r"\"(.*?)\"", r"“\1”"},
}
app = QApplication()

config_path = "config.json"
# setup ui & app
win = Window(config_path=config_path)
win.show()
# set dark mode
stylestr = win.config["style"]
app.setStyleSheet(stylestr)
app.exec()
