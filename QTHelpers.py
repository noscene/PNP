from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2 


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
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        #rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(cv_img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


# single Object with CallBack
class ButtonBlock(QtWidgets.QWidget):
    def __init__(self, name='noname',row=None,action=None):
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

