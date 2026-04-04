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
maintext=QPlainTextEdit()
inputtext=QPlainTextEdit()
combo=QComboBox()
layout=QGridLayout()
bsubs=QPushButton("regex replace")
bsend=QPushButton("send")
bretry=QPushButton("retry")
babort=QPushButton("abort")
window.setLayout(layout)
for w in [maintext,inputtext,combo,bsubs,bsend,bretry,babort]:
    layout.addWidget(w)
combo.addItems(list(subs_dict.keys()))
window.show()
tstream=QTimer()
'''stream update timer'''
# logic

def dict_replace(s:str,d:dict):
    for k in d:
        s=s.replace(k,d[k])
    return s
def text_cb():
    param=combo.currentText()
    newtext=maintext.toPlainText()
    d=subs_dict[param]
    for k in d:
        newtext=re.sub(k,d[k],newtext)
    maintext.setPlainText(newtext)
def send():
    global current_stream,last_context
    context=maintext.toPlainText()
    last_context=context
    inputmsg=inputtext.toPlainText()
    is_new_turn=True if inputmsg!="" else False
    if is_new_turn:
        context=context+"\n{{[INPUT]}}\n"+inputmsg+"\n{{[OUTPUT]}}\n"
        last_context=context
    d=config['chat_template']
    prom=context
    for k in d:
        prom=prom.replace(k,d[k])
    if is_new_turn:
        prom=prom+config['nothink_tag']
    inputtext.clear()
    maintext.setPlainText(context)
    maintext.moveCursor(QTextCursor.MoveOperation.End)
    current_stream=textcomp_stream(prom)
    tstream.start()
def retry():
    maintext.setPlainText(last_context)
    send()
def stream_tick():
    chunk=next(current_stream,None)
    if chunk is not None:
        #"append" gives extra newline
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
# exec
app.exec()
    
