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
        self.next_step_enable = False
        self.state_idx=0
        self.states = [ {'name': self.GO_PCBPART,        'wait': 1.0},
                        {'name': self.MAKE_PCB_FOTO,     'wait': 1.0},
                        {'name': self.GO_FEEDER,         'wait': 1.0},
                        {'name': self.CENTER_TO_CLOSE,   'wait': 1.0},
                        {'name': self.GO_NOZZLE_OFFSET,  'wait': 1.0},
                        {'name': self.NOZZLE_DOWN,       'wait': 1.0},
                        {'name': self.SELENOID_ON,       'wait': 1.0},
                        {'name': self.NOZZLE_UP,         'wait': 1.0},
                        {'name': self.GO_BOTTOMCAM,      'wait': 1.0},
                        {'name': self.SET_ROTATION,      'wait': 1.0},
                        {'name': self.GO_PCB_PLACE,      'wait': 1.0},
                        {'name': self.NOZZLE_DOWN2,      'wait': 1.0},
                        {'name': self.SELENOID_OFF,      'wait': 1.0},
                        {'name': self.FINISHED,          'wait': 10.0} ]

    def run(self):

        while True:
            current_state = self.states[self.state_idx]
            #print ( current_state['name']     ) 
            time.sleep(current_state['wait'])
            current_state['name']()
            if( self.state_idx < len(self.states)-1 ):
                self.state_idx+=1
                self.event.emit(self.state_idx)
                self.next_step_enable = False
            else:
                print ( 'Job Finished'   ) 
                time.sleep(5)

    def GO_PCBPART(self):           print("GO_PCBPART")
    def MAKE_PCB_FOTO(self):        print("MAKE_PCB_FOTO")
    def GO_FEEDER(self):            print("GO_FEEDER")

    def CENTER_TO_CLOSE(self):            print("CENTER_TO_CLOSE")
    def GO_NOZZLE_OFFSET(self):            print("GO_NOZZLE_OFFSET")
    def NOZZLE_DOWN(self):            print("NOZZLE_DOWN")    
    def SELENOID_ON(self):            print("SELENOID_ON")
    def NOZZLE_UP(self):            print("NOZZLE_UP")
    def GO_BOTTOMCAM(self):            print("GO_BOTTOMCAM")    

    def SET_ROTATION(self):            print("SET_ROTATION")    
    def GO_PCB_PLACE(self):            print("GO_PCB_PLACE")    
    def NOZZLE_DOWN2(self):            print("NOZZLE_DOWN2")    
    def SELENOID_OFF(self):            print("SELENOID_OFF")    
    def FINISHED(self):            print("FINISHED")    
