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

        self.states = [ {'name': self.GO_PCBPART,        'wait': 1.0, 'auto': True},
                        {'name': self.MAKE_PCB_FOTO,     'wait': 1.0, 'auto': True},
                        {'name': self.GO_FEEDER,         'wait': 1.0, 'auto': False},
                        {'name': self.CENTER_TO_CLOSE,   'wait': 1.0, 'auto': False},
                        {'name': self.GO_NOZZLE_OFFSET,  'wait': 1.0, 'auto': False},
                        {'name': self.NOZZLE_DOWN,       'wait': 1.0, 'auto': False},
                        {'name': self.SELENOID_ON,       'wait': 1.0, 'auto': True},
                        {'name': self.NOZZLE_UP,         'wait': 1.0, 'auto': True},
                        {'name': self.GO_BOTTOMCAM,      'wait': 1.0, 'auto': True},
                        {'name': self.SET_ROTATION,      'wait': 1.0, 'auto': False},
                        {'name': self.FIX_CENTER,        'wait': 1.0, 'auto': True},
                        {'name': self.GO_PCB_PLACE,      'wait': 1.0, 'auto': False},
                        {'name': self.NOZZLE_DOWN2,      'wait': 1.0, 'auto': True},
                        {'name': self.SELENOID_OFF,      'wait': 1.0, 'auto': True},
                        {'name': self.FINISHED,          'wait': 1.0, 'auto': True} ]
        self.gcode = None

        # Runtime Parms
        self.next_step_enable = False
        self.state_idx=0
        self.feeder = None
        self.footprint = None
        self.position_part_on_pcb = None    # [0]:x  [1]:y  [2]:angle 
        self.videoThreadTop = None
        self.videoThreadBottom = None
        self.angel_from_pickup = 0


    def run(self):

        while True:
            current_state = self.states[self.state_idx]     # loopup state
            self.event.emit(self.state_idx)                 # call UI
            while not self.next_step_enable:                # Wait for enable Step
                pass

            time_to_wait = current_state['wait']
            time.sleep(time_to_wait)                        # wait
            print(self.state_idx,"UI Finished")
            current_state['name']()                         # call function
            if( self.state_idx < len(self.states)-1 ):
                self.state_idx+=1
                self.next_step_enable = False
            else:
                return                                      # Stop and Return

    def GO_PCBPART(self):           
        print(self.state_idx,"GO_PCBPART")
        self.gcode.ledHead_On()
        self.angel_from_pickup=0    # reset Value
        self.gcode.driveto((self.position_part_on_pcb[0], self.position_part_on_pcb[1]))
    def MAKE_PCB_FOTO(self):        
        print(self.state_idx,"MAKE_PCB_FOTO")
    def GO_FEEDER(self):            
        print(self.state_idx,"GO_FEEDER")
        self.gcode.driveto((self.feeder.X + self.feeder.W/2 ,self.feeder.Y + self.feeder.H/2))
    def CENTER_TO_CLOSE(self):      
        print(self.state_idx,"CENTER_TO_CLOSE")
        self.gcode.vacuum1_On()
        self.gcode.vacuum2_On()


        mm_faktor = 52.0 / 1024.0   # mm per 1024 pixel depend on cam position
        x = (self.videoThreadTop.real_w / 2 - self.videoThreadTop.min_obj_x) * -1
        y = self.videoThreadTop.real_h / 2 - self.videoThreadTop.min_obj_y

        x_relativ_mm =  x * mm_faktor
        y_relativ_mm =  y * mm_faktor


        print("CENTER_TO_CLOSE",x_relativ_mm ,y_relativ_mm, self.videoThreadTop.real_w,self.videoThreadTop.real_h)
        if(abs(x_relativ_mm) < 25 and abs(y_relativ_mm) < 25):
            self.angel_from_pickup =  self.videoThreadTop.min_obj_angel
            self.gcode.update_position_relative( x_relativ_mm , y_relativ_mm )  



    def GO_NOZZLE_OFFSET(self):     
        print(self.state_idx,"GO_NOZZLE_OFFSET")
        self.gcode.driveto((self.gcode.x + self.gcode.headoffset_x ,
                            self.gcode.y + self.gcode.headoffset_y   ))

    def NOZZLE_DOWN(self):          
        print(self.state_idx,"NOZZLE_DOWN", self.feeder.Z - self.footprint.Z)
        self.gcode.driveZ(self.feeder.Z - self.footprint.Z)
    def SELENOID_ON(self):          
        print(self.state_idx,"SELENOID_ON")
        self.gcode.selenoid_on()
    def NOZZLE_UP(self):            
        print(self.state_idx,"NOZZLE_UP")
        self.gcode.driveZ(4)
    def GO_BOTTOMCAM(self):         
        print(self.state_idx,"GO_BOTTOMCAM")    
        self.gcode.driveto((self.gcode.bottom_cam_x,self.gcode.bottom_cam_y)) 
    def SET_ROTATION(self):         
        print(self.state_idx,"SET_ROTATION")   
        self.gcode.update_rotation_relative(self.angel_from_pickup ) 
    def FIX_CENTER(self):           
        print(self.state_idx,"FIX_CENTER")   
        #self.gcode.driveto((100,100))
    def GO_PCB_PLACE(self):         
        print(self.state_idx,"GO_PCB_PLACE")   
        #
        # TODO: add the currentOffset from self.gcode.x - self.gcode.bottom_cam_x
        #
        delta_x = self.gcode.x - self.gcode.bottom_cam_x 
        delta_y = self.gcode.y - self.gcode.bottom_cam_y  

        self.gcode.driveto((self.position_part_on_pcb[0]  + self.gcode.headoffset_x + delta_x , 
                            self.position_part_on_pcb[1]  + self.gcode.headoffset_y + delta_y )) 
    def NOZZLE_DOWN2(self):         
        print(self.state_idx,"NOZZLE_DOWN2")   
        self.gcode.driveZ(11.5 - self.footprint.Z)  # TODO: Add PCB Z Param
    def SELENOID_OFF(self):         
        print(self.state_idx,"SELENOID_OFF")    
        self.gcode.selenoid_off()
    def FINISHED(self):             
        self.gcode.driveZ(4.0) 
        self.gcode.vacuum1_Off() 
        self.gcode.vacuum2_Off() 

        print(self.state_idx,"FINISHED")    
