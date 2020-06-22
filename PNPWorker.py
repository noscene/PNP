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
                        {'name': self.CENTER_TO_CLOSE,   'wait': 1.0},
                        {'name': self.NOZZLE_DOWN,       'wait': 1.0},
                        {'name': self.SELENOID_ON,       'wait': 1.0},
                        {'name': self.NOZZLE_UP,         'wait': 1.0},
                        {'name': self.GO_BOTTOMCAM,      'wait': 1.0},
                        {'name': self.SET_ROTATION,      'wait': 1.0},
                        {'name': self.FIX_CENTER,        'wait': 1.0},
                        {'name': self.GO_PCB_PLACE,      'wait': 1.0},
                        {'name': self.NOZZLE_DOWN2,      'wait': 1.0},
                        {'name': self.SELENOID_OFF,      'wait': 1.0},
                        {'name': self.FINISHED,          'wait': 1.0} ]
        self.gcode = None
        self.part = None
        self.footprint = None
        self.parms = None


    def run(self):

        while True:
            current_state = self.states[self.state_idx]     # loopup state
            self.event.emit(self.state_idx)                 # call UI
            time_to_wait = current_state['wait']
            time.sleep(time_to_wait)                        # wait

            print(self.state_idx,"UI Finished")
            current_state['name']()                         # call function
            if( self.state_idx < len(self.states)-1 ):
                self.state_idx+=1
                self.next_step_enable = False
            else:
                return                                      # Stop and Return

    def GO_PCBPART(self):           print(self.state_idx,"GO_PCBPART")
    def MAKE_PCB_FOTO(self):        print(self.state_idx,"MAKE_PCB_FOTO")
    def GO_FEEDER(self):            
        print(self.state_idx,"GO_FEEDER")
        self.gcode.driveto((10,10))
    def CENTER_TO_CLOSE(self):      print(self.state_idx,"CENTER_TO_CLOSE")
    def GO_NOZZLE_OFFSET(self):     print(self.state_idx,"GO_NOZZLE_OFFSET")
    def NOZZLE_DOWN(self):          print(self.state_idx,"NOZZLE_DOWN")    
    def SELENOID_ON(self):          
        print(self.state_idx,"SELENOID_ON")
        self.gcode.driveto((100,10))
    def NOZZLE_UP(self):            print(self.state_idx,"NOZZLE_UP")
    def GO_BOTTOMCAM(self):         print(self.state_idx,"GO_BOTTOMCAM")    
    def SET_ROTATION(self):         print(self.state_idx,"SET_ROTATION")    
    def FIX_CENTER(self):           
        print(self.state_idx,"FIX_CENTER")   
        self.gcode.driveto((100,100))
    def GO_PCB_PLACE(self):         print(self.state_idx,"GO_PCB_PLACE")    
    def NOZZLE_DOWN2(self):         print(self.state_idx,"NOZZLE_DOWN2")    
    def SELENOID_OFF(self):         print(self.state_idx,"SELENOID_OFF")    
    def FINISHED(self):             print(self.state_idx,"FINISHED")    
