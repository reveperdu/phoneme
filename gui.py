import re
import PySide6.QtWidgets as qt
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QTimer
import api
subs_dict={"full-width quotes to half-width":{r'“|”':r'"'},
           "half-width quotes to full-width":{r'\"(.*?)\"',r'“\1”'}}
#ui layout
qt_app=qt.QApplication()
qt_window=qt.QWidget()
qt_text_main=qt.QPlainTextEdit()
qt_combo=qt.QComboBox()
qt_layout=qt.QGridLayout()
qt_button_subs=qt.QPushButton("Do It")
qt_button_send=qt.QPushButton("Send")
qt_window.setLayout(qt_layout)
for w in [qt_text_main,qt_combo,qt_button_subs,qt_button_send]:
    qt_layout.addWidget(w)
qt_combo.addItems(list(subs_dict.keys()))
qt_window.show()
qt_tstream=QTimer()
'''stream update timer'''
# logic
def text_subs(text,param):
    subs=subs_dict[param]
    for s in subs:
        text=re.sub(s,subs[s],text)
    return text

def text_cb():
    param=qt_combo.currentText()
    newtext=text_subs(qt_text_main.toPlainText(),param)
    qt_text_main.setPlainText(newtext)
def send():
    global current_stream
    context=qt_text_main.toPlainText()
    current_stream=api.textcomp_stream(context)
    qt_tstream.start()
def stream_tick():
    chunk=next(current_stream,None)
    if chunk is not None:
        #"append" gives extra newline
        qt_text_main.moveCursor(QTextCursor.MoveOperation.End)
        qt_text_main.insertPlainText(chunk)
    else:
        qt_tstream.stop()
# ui events
qt_button_subs.clicked.connect(text_cb)
qt_button_send.clicked.connect(send)
qt_tstream.setInterval(100)
qt_tstream.timeout.connect(stream_tick)
# exec
qt_app.exec()
    
