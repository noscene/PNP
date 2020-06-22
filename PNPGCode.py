# pip3 install PySerial 
import serial
import time
import sys
import threading

class PNPGCode():
    def __init__(self, device='/dev/ttyUSB0'):
        self.x=0
        self.y=0
        self.z=3
        self.device = device
        self.alpha=0 
        self.stepSpeed=8000
        self.stepWidth=10
        self.bottom_cam_x =   5.39        # machine parm
        self.bottom_cam_y =  34.73        # machine parm

        self.headoffset_x =  18.89        # machine parm
        self.headoffset_y = -42.96        # machine parm
        self.headoffset_active = False

        self.is_connected=False
        self.readthread=None
        self.get_wait=False

    def handle_data(self,data):
        line = data.splitlines()[0] # without "\r\n"
        if line == 'wait' and not self.get_wait:
            self.get_wait = True
            print("saw wait")
        elif line != 'wait': print('handle_data->',line,'<--')

    def read_from_port(self,ser):
        while True:
            #print("test")
            reading = self.ser.readline().decode()
            self.handle_data(reading)


    def sendGCode(self,gcode,dly=0):
        print(gcode)
        if(sys.platform == 'darwin'): return    # avoid crashes on my mac
        if not self.is_connected:
            self.ser = serial.Serial(self.device, 115200)
            self.readthread = threading.Thread(target=self.read_from_port, args=(self.ser,))
            self.readthread.start()
            self.is_connected = True
        time.sleep(0.01)
        self.ser.write(gcode.encode('raw_unicode_escape'))
        self.get_wait=False
        #self.ser.write(b"M114\r\n")

            

    def driveto(self,pos):
        #global stepSpeed,z
        new_x = pos[0]
        new_y = pos[1]
        
        if(new_x<0): 
            print("Bad x:",new_x)
            return
        if(new_x>250):
            print("Bad x:",new_x)
            return
        if(new_y<0):
            print("Bad y:",new_y)
            return
        if(new_y>390):
            print("Bad y:",new_y)
            return        

        self.x = new_x
        self.y = new_y

        if self.z > 4 :
            self.driveZ(4) # UP Nozzle!!!!! before Drive!!!!!
        
        self.ui.gc_mpos_x.setText(str(round(self.x,2 )))
        self.ui.gc_mpos_y.setText(str(round(self.y,2 )))

        gcode="G1 X"+ str(round(self.x,3)) + " Y"+ str(round(self.y,3)) +" F" + str(int(self.stepSpeed)) + "\r\n"
        self.sendGCode(gcode,0)

    def toogle_head_cam_center(self):
        if not self.headoffset_active:
            self.headoffset_active = True
            self.update_position_relative( self.headoffset_x, self.headoffset_y )
        else:
            self.headoffset_active = False
            self.update_position_relative( (-1.0 * self.headoffset_x) , (-1.0 * self.headoffset_y))

    def driveZ(self,z):
        time.sleep(0.1)
        self.z = int(z)
        if(self.z<2):
            print("Bad z:",self.z)
            return
        if(self.z>20):
            print("Bad z:",self.z)
            return
        gcode="G1 Z-"+ str(self.z) +" F7000\r\n"
        self.sendGCode(gcode,0)
    def rotateGrad(self,alpha):
        self.alpha = int(alpha)
        gcode="G1 E"+ str(self.alpha) +" F1500 \r\n"
        self.sendGCode(gcode,0)
        time.sleep(1)
    def motoroff(self):     self.sendGCode("M84\r\n",0)
    def goHome(self):  
        self.sendGCode("G28\r\n",0)
        self.driveto((0,0))    
    def driveTest1(self):
        for x in range(3):
            self.driveto((120,220))
            self.sleep(2000)
            self.driveto((200,220))
            self.sleep(1000)
    def driveTest2(self):
        self.vacuum1_On()
        self.vacuum2_On()
        self.sleep(1000)  
        for x in range(1):
            self.driveto((60,240))
            self.driveZ(16)
            self.selenoid_on()
            self.sleep(300)
            self.driveZ(4)
            self.driveto((200,220))
            self.update_rotation_relative(90)
            self.sleep(300)
            self.driveZ(15)
            time.sleep(1)
            self.selenoid_off()
            self.sleep(1000)
            self.driveZ(4)
            self.driveto((100,100))
        self.vacuum1_Off()
        self.vacuum2_Off()
    def sleep(self,ms):        self.sendGCode("G4 P" + str(ms) + "\r\n",     1)
    def ledHead_On(self):      self.sendGCode("M42 P31 S255\r\n",     0)  
    def ledHead_Off(self):     self.sendGCode("M42 P31 S0\r\n",       0)
    def ledBottom_On(self):    self.sendGCode("M42 P33 S255\r\n",     0) 
    def ledBottom_Off(self):   self.sendGCode("M42 P33 S0\r\n",       0)
    def vacuum1_On(self):      self.sendGCode("M42 P25 S255\r\n",  1000)
    def vacuum2_On(self):      self.sendGCode("M42 P27 S255\r\n",  1000)
    def vacuum1_Off(self):     self.sendGCode("M42 P25 S0\r\n",    1000)
    def vacuum2_Off(self):     self.sendGCode("M42 P27 S0\r\n",    1000)
    def selenoid_on(self):     self.sendGCode("M42 P29 S255\r\n",   500)
    def selenoid_off(self):    self.sendGCode("M42 P29 S0\r\n",    1000)




    def update_rotation_relative(self,na):
        self.rotateGrad(self.alpha+na)
    def update_position_relative(self,nx,ny):   
        self.driveto((self.x + nx ,self.y + ny))
        #self.ui.gc_mpos_x.setText(str(self.x ))
        #self.ui.gc_mpos_y.setText(str(self.y ))

    def update_z_position_relative(self,nz):      self.driveZ(self.z+nz)

    # Setup UI Stuff    
    def gc_up1(self):       self.update_position_relative(0,0.3)
    def gc_up10(self):      self.update_position_relative(0, 6)
    def gc_up100(self):     self.update_position_relative(0,60)

    def gc_down1(self):     self.update_position_relative(0,-0.3)
    def gc_down10(self):    self.update_position_relative(0,-6)
    def gc_down100(self):   self.update_position_relative(0,-60)

    def gc_left1(self):     self.update_position_relative(-0.3,0)
    def gc_left10(self):    self.update_position_relative(-6,0)
    def gc_left100(self):   self.update_position_relative(-60,0)

    def gc_right1(self):    self.update_position_relative(0.3,0)
    def gc_right10(self):   self.update_position_relative(6,0)
    def gc_right100(self):  self.update_position_relative(60,0)

    def gc_rot1(self):    self.update_rotation_relative(1)
    def gc_rot_1(self):   self.update_rotation_relative(-1)
    def gc_rot_90(self):  self.update_rotation_relative(-90)
    def gc_rot45(self):   self.update_rotation_relative(45)


    def gc_z_up(self):     self.update_z_position_relative(-1)
    def gc_z_down(self):   self.update_z_position_relative(1)


    def gc_go_absolute(self):
        print(self.ui.gc_mpos_x.text(),self.ui.gc_mpos_y.text())
        self.driveto((float(self.ui.gc_mpos_x.text()) , float(self.ui.gc_mpos_y.text())))
        #self.ui.gc_mpos_x.setText(str(self.x ))
        #self.ui.gc_mpos_y.setText(str(self.y ))        

    def gc_led_head(self):
        if self.ui.gc_led_head.checkState()==0:     self.ledHead_Off()
        else:                                       self.ledHead_On()

    def gc_led_bottom(self):
        if self.ui.gc_led_bottom.checkState()==0:   self.ledBottom_Off()
        else:                                       self.ledBottom_On()

    def gc_vacuum1(self):
        if self.ui.gc_vacuum1.checkState()==0:      self.vacuum1_Off()
        else:                                       self.vacuum1_On()

    def gc_vacuum2(self):
        if self.ui.gc_vacuum2.checkState()==0:      self.vacuum2_Off()
        else:                                       self.vacuum2_On()



    def setupGui(self, ui):
        self.ui = ui # backup for later
  
        self.ui.gc_mpos_x.setText("0")
        self.ui.gc_mpos_y.setText("0")

        self.ui.gc_home.clicked.connect(       self.goHome)
        self.ui.gc_motor_off.clicked.connect(  self.motoroff)
        self.ui.gc_sel_off.clicked.connect(    self.selenoid_off)
        self.ui.gc_sel_on.clicked.connect(     self.selenoid_on)


        self.ui.gc_up1.clicked.connect(   self.gc_up1)
        self.ui.gc_up10.clicked.connect(  self.gc_up10)
        self.ui.gc_up100.clicked.connect( self.gc_up100)

        self.ui.gc_down1.clicked.connect(   self.gc_down1)
        self.ui.gc_down10.clicked.connect(  self.gc_down10)
        self.ui.gc_down100.clicked.connect( self.gc_down100)

        self.ui.gc_left1.clicked.connect(   self.gc_left1)
        self.ui.gc_left10.clicked.connect(  self.gc_left10)
        self.ui.gc_left100.clicked.connect( self.gc_left100)

        self.ui.gc_right1.clicked.connect(   self.gc_right1)
        self.ui.gc_right10.clicked.connect(  self.gc_right10)
        self.ui.gc_right100.clicked.connect( self.gc_right100)

        self.ui.gc_go_absolute.clicked.connect( self.gc_go_absolute)

        self.ui.gc_head_pick.clicked.connect(self.toogle_head_cam_center)
  
        self.ui.gc_led_head.clicked.connect( self.gc_led_head)
        self.ui.gc_led_bottom.clicked.connect( self.gc_led_bottom)
        self.ui.gc_vacuum1.clicked.connect( self.gc_vacuum1)
        self.ui.gc_vacuum2.clicked.connect( self.gc_vacuum2)

        self.ui.gc_rot1.clicked.connect( self.gc_rot1)
        self.ui.gc_rot45.clicked.connect( self.gc_rot45)
        self.ui.gc_rot_1.clicked.connect( self.gc_rot_1)
        self.ui.gc_rot_90.clicked.connect( self.gc_rot_90)

        self.ui.gc_z_up.clicked.connect( self.gc_z_up)
        self.ui.gc_z_down.clicked.connect( self.gc_z_down)


