import re
import PySide6.QtWidgets as qt

subs_dict={"full-width quotes to half-width":{r'“|”':r'"'},
           "half-width quotes to full-width":{r'\"(.*?)\"',r'“\1”'}}
#ui layout
qt_app=qt.QApplication()
qt_window=qt.QWidget()
qt_text=qt.QPlainTextEdit()
qt_combo=qt.QComboBox()
qt_layout=qt.QGridLayout()
qt_button=qt.QPushButton("Do It")
qt_window.setLayout(qt_layout)
for w in [qt_text,qt_combo,qt_button]:
    qt_layout.addWidget(w)
qt_combo.addItems(list(subs_dict.keys()))
qt_window.show()

# logic
def text_op(text,param):
    subs=subs_dict[param]
    for s in subs:
        text=re.sub(s,subs[s],text)
    return text

def text_cb():
    param=qt_combo.currentText()
    newtext=text_op(qt_text.toPlainText(),param)
    qt_text.setPlainText(newtext)

# ui events
qt_button.clicked.connect(text_cb)

# exec
qt_app.exec()
    
