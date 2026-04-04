import re
from PySide6.QtWidgets import (QApplication,QWidget,QPlainTextEdit,QComboBox,
                               QGridLayout,QPushButton)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import QTimer
from api import *
subs_dict={"full-width quotes to half-width":{r'“|”':r'"'},
           "half-width quotes to full-width":{r'\"(.*?)\"',r'“\1”'}}
#ui layout
app=QApplication()
window=QWidget()
tmain=QPlainTextEdit()
combo=QComboBox()
layout=QGridLayout()
bsubs=QPushButton("Do It")
bsend=QPushButton("Send")
window.setLayout(layout)
for w in [tmain,combo,bsubs,bsend]:
    layout.addWidget(w)
combo.addItems(list(subs_dict.keys()))
window.show()
tstream=QTimer()
'''stream update timer'''
# logic
def text_subs(text,param):
    subs=subs_dict[param]
    for s in subs:
        text=re.sub(s,subs[s],text)
    return text

def text_cb():
    param=combo.currentText()
    newtext=text_subs(tmain.toPlainText(),param)
    tmain.setPlainText(newtext)
def send():
    global current_stream
    context=tmain.toPlainText()
    current_stream=textcomp_stream(context)
    tstream.start()
def stream_tick():
    chunk=next(current_stream,None)
    if chunk is not None:
        #"append" gives extra newline
        tmain.moveCursor(QTextCursor.MoveOperation.End)
        tmain.insertPlainText(chunk)
    else:
        tstream.stop()
# ui events
bsubs.clicked.connect(text_cb)
bsend.clicked.connect(send)
tstream.setInterval(100)
tstream.timeout.connect(stream_tick)
# exec
app.exec()
    
