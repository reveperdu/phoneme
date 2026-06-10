from PySide6.QtWidgets import QApplication
from window import Window
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config")
args = parser.parse_args()
config_path = "config.json"
if args.config is not None:
    config_path = args.config

app = QApplication()


# setup ui & app
win = Window(config_path=config_path)
win.show()
# set dark mode
stylestr = win.config["style"]
app.setStyleSheet(stylestr)
app.exec()
