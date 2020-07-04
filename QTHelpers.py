from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *



# https://stackoverflow.com/questions/45575626/make-qlabel-clickable-using-pyqt5
class QLabel_alterada(QLabel):
    clicked=pyqtSignal()
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        self.mouse_click = [0,0]
    def mousePressEvent(self, ev):
        self.mouse_click= [ev.x(),ev.y()]
        print(ev.x(),ev.y())
        self.clicked.emit()


# single Object with CallBack
class ButtonBlock(QtWidgets.QWidget):
    def __init__(self, name='tach',row=None,action=None):
        super(QtWidgets.QWidget, self).__init__()
        self.row = row
        self.action = action
        bt = QtWidgets.QPushButton()
        bt.setText(name)
        bl=QtWidgets.QHBoxLayout(self)
        bl.addWidget(bt)
        bl.setAlignment(Qt.AlignCenter);
        bl.setContentsMargins(0, 0, 0, 0);
        self.setLayout(bl)
        bt.clicked.connect(self.ButtonClicked)
        self.name=name
    def ButtonClicked(self):
        # print ("ButtonClicked",self.row)
        self.action(self.row)

