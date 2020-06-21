# PNPWorker
import sys
import time

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class PNPWorker(QThread):

    event = pyqtSignal(int)

    def __init__(self):
        super(QThread, self).__init__()

    def run(self):
        count = 0
        while True:
            time.sleep(5)
            count += 1
            print("PNPWorker")
            self.event.emit(count)
