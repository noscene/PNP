from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json

import cv2
import numpy as np
import pandas as pd

from VideoThread import *
from PNPHelpers import *
from PNPWorker import *

mouse_click = []

# https://stackoverflow.com/questions/45575626/make-qlabel-clickable-using-pyqt5
class QLabel_alterada(QLabel):
    clicked=pyqtSignal()
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        global mouse_click
        mouse_click= [ev.x(),ev.y()]
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




class PNPGui():
    def __init__(self,ui,gcode):
        self.ui=ui
        self.gcode=gcode
        self.df_parts=None
        self.df_footprints=None
        self.df_feeders=None


        # simple Validation on numeric fields
        self.ui.gc_mpos_x.setValidator( QDoubleValidator(0, 230.0 ,8) )
        self.ui.gc_mpos_y.setValidator( QDoubleValidator(0, 280.0 ,8) )
      
        
        self.ui.pannel_update_bt.clicked.connect(self.loadFiducialList)

        self.ui.tabs.currentChanged.connect(self.onTabChange)


        # configure Video Thread
        self.th = VideoThread()
        self.th2 = VideoThread()
        self.changeSlider4Vision()

        if(sys.platform == 'linux'):    self.th.cam="/dev/video0"
        else:                           self.th.cam=1

        self.th.myVideoFrame = self.ui.videoframe
        self.th.changePixmap.connect(self.th.setImageToGUI)
        self.th.mode=0
        self.th.start()
    

        # configure Video Thread
        if(sys.platform == 'linux'):    self.th2.cam="/dev/video1"
        else:                           self.th2.cam=0
        self.th2.myVideoFrame = self.ui.videoframe_2
        self.th2.changePixmap.connect(self.th2.setImageToGUI)
        self.th2.mode=0
        self.th2.start()

        self.worker = PNPWorker()
        self.worker.gcode = self.gcode
        self.worker.event.connect(self.on_worker_event)

        self.ui.check_step.clicked.connect(self.onCheckStep)


        self.ui.videoframe.clicked.connect(self.onVideoMouseEvent) 


        self.ui.slider_h_min.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_h_max.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_s_min.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_s_max.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_v_min.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_v_max.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_a_min.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_a_max.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_expose.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_a_fac.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_kernel.valueChanged.connect(self.changeSlider4Vision)
        
        
    
    
    #
    # Handling worker Jobs allow Steps if need interacting
    #
    def on_worker_event(self,n):
        print("on_worker_event",n)      
        self.ui.lcdNumber.display(n)    
        workerItem = self.worker.states[n]  # get current Worker Item
        if workerItem['auto']:
            self.ui.check_step.setCheckState(2)
            self.worker.next_step_enable=True
        else:
            self.ui.check_step.setCheckState(False)

    def onCheckStep(self):
        if(self.ui.check_step.checkState()):
            self.worker.next_step_enable=True
            print("checked")
        else:
            print("non checked")    
    
    
    
    
    #
    # Helper Functions for Sliders
    def changeSlider4Vision(self):
        self.th.parms['h_min'] = self.ui.slider_h_min.value()
        self.th.parms['h_max'] = self.ui.slider_h_max.value()
        self.th.parms['s_min'] = self.ui.slider_s_min.value()
        self.th.parms['s_max'] = self.ui.slider_s_max.value()
        self.th.parms['v_min'] = self.ui.slider_v_min.value()
        self.th.parms['v_max'] = self.ui.slider_v_max.value()
        self.th.parms['a_min'] = self.ui.slider_a_min.value()
        self.th.parms['a_max'] = self.ui.slider_a_max.value()
        self.th.parms['expose'] = self.ui.slider_expose.value()
        self.th.parms['a_fac'] = self.ui.slider_a_fac.value()
        self.th.parms['kernel'] = self.ui.slider_kernel.value()
        self.th.parms['canny_thrs1'] = 85
        self.th.parms['canny_thrs2'] = 255
        self.th.parms['dilate_count'] = 8
        self.th.parms['erode_count'] = 6
        self.th.parms['gauss_v1'] = 3
        self.th.parms['gauss_v2'] = 3


        #self.th.parms['a_fac'] = self.ui.slider_a_fac.value()
        self.th2.parms = self.th.parms # For first Tests just use same Settings on both cams
        print("changeSlider4Vision", self.th.parms)




    def onVideoMouseEvent(self):
        global mouse_click
        print("onVideoMouseEvent",mouse_click)
        # 1024x768 => 1024 = 52mm
        mm_faktor = 52.0 / 1024.0
        x = (512 - mouse_click[0]) * -1
        y = 384 - mouse_click[1]
        print("onVideoMouseEvent2",x * mm_faktor ,y * mm_faktor)
        self.gcode.update_position_relative( x * mm_faktor , y * mm_faktor )  



    def onTabChange(self,i):
        print("onTabChange TODO refresh Data on this event: ",i)
        self.th.mode=i
        self.th2.mode=i
        if(i==3): self.setFeederTable()

    #
    #
    #
    def setFootprintTable(self):
          # QTableWidget
        grid = self.ui.footprint_table
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        df = self.df_footprints
        self.footprint_list_headers = ['Feeder','Footprint','X', 'Y', 'Z','Nozzle','GoFeeder']
        grid.setColumnCount(7)
        grid.setHorizontalHeaderLabels(self.footprint_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.setRowCount(len(df.index))
        for index, row in df.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['Feeder']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Footprint']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setItem(index,4,QtWidgets.QTableWidgetItem(str(row['Z']))) 
            grid.setItem(index,5,QtWidgets.QTableWidgetItem(str(row['Nozzle']))) 
            grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonFootprint))
        grid.itemChanged.connect(self.changeFootprintItemn)

    def changeFootprintItemn(self,item):
        row = item.row()
        col = item.column()
        col_name = self.footprint_list_headers[col]
        # print ("changePartItemn",row,col,col_name,item.text())
        try:
            self.df_footprints.at[row, col_name] = item.text()
        except:
            print ("changeFootprintItemn ERROR invalid value",row,col,col_name,item.text())
    def onGoButtonFootprint(self,item):
        print("onGoButtonFootprint",item)

    #
    #
    #
    #
    def setFeederTable(self):
          # QTableWidget
        grid = self.ui.feeder_table
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        df = self.df_feeders
        self.feeder_list_headers = ["Tray","Vision","NR","X","Y","W","H","Z","Footprint","Value"]
        grid.setColumnCount(11)
        grid.setHorizontalHeaderLabels(self.feeder_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.setRowCount(len(df.index))
        for index, row in df.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['Tray']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Vision']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['NR']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,4,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setItem(index,5,QtWidgets.QTableWidgetItem(str(row['W']))) 
            grid.setItem(index,6,QtWidgets.QTableWidgetItem(str(row['H']))) 
            grid.setItem(index,7,QtWidgets.QTableWidgetItem(str(row['Z']))) 
            grid.setItem(index,8,QtWidgets.QTableWidgetItem(str(row['Footprint']))) 
            grid.setItem(index,9,QtWidgets.QTableWidgetItem(str(row['Value']))) 
            grid.setCellWidget(index, 10, ButtonBlock("go",row, self.onGoButtonFeeder))
        grid.itemChanged.connect(self.changeFeederItemn)

    def changeFeederItemn(self,item):
        row = item.row()
        col = item.column()
        col_name = self.feeder_list_headers[col]
        # print ("changePartItemn",row,col,col_name,item.text())
        try:
            self.df_feeders.at[row, col_name] = item.text()
        except:
            print ("changeFootprintItemn ERROR invalid value",row,col,col_name,item.text())
        self.df_feeders.to_csv('feeder.csv', sep=";", header=True,index=False, columns=["Tray","NR","X","Y","W","H","Z","Footprint","Value","Vision"])

    def onGoButtonFeeder(self,item):
        print("onGoButtonFeeder",item.X + item.W / 2.0 , item.Y + item.H / 2.0)
        self.gcode.driveto(( item.X + item.W / 2.0  , item.Y + item.H / 2.0 )) 
    #
    #
    #
    #
    def showPartList(self):
        print("showPartList",self.df_parts)
        grid = self.ui.parts_table 
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        df = self.df_parts
        self.part_list_headers = ['PART','Footprint','Value','X', 'Y', 'R','Go']
        grid.setColumnCount(8)
        grid.setHorizontalHeaderLabels(self.part_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.setRowCount(len(df.index))
        for index, row in df.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['PART']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Footprint']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['Value']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,4,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setItem(index,5,QtWidgets.QTableWidgetItem(str(row['R']))) 

            # query for existing Footprint, need trim strings on import!
            query = 'Footprint == "'+str(row['Footprint'])+'" and X > 0 '
            if self.df_footprints.query( query )['Footprint'].count() == 0:
                grid.item(index, 1).setBackground(Qt.yellow)

            query = 'Footprint == "'+str(row['Footprint'])+'" and Value =="'+str(row['Value'])+'" '
            if self.df_feeders.query( query )['Value'].count() == 0:
                grid.item(index, 2).setBackground(Qt.yellow)                

            grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonPartlist))
            grid.setCellWidget(index, 7, ButtonBlock("Sim",row, self.onSimButtonPartlist))

        grid.itemChanged.connect(self.changePartItemn)
        self.ui.lcdNumber.display(len(df.index))

    def changePartItemn(self,item):
        row = item.row()
        col = item.column()
        col_name = self.part_list_headers[col]
        # print ("changePartItemn",row,col,col_name,item.text())
        try:
            self.df_parts.at[row, col_name] = item.text()
        except:
            print ("changePartItemn ERROR invalid value",row,col,col_name,item.text())
            self.showPartList()   # restore list

    def onSimButtonPartlist(self,row):
        print("onSimButtonPartlist", row)
        self.worker.footprint = self.df_footprints.query( 'Footprint == "'+str(row['Footprint'])+'" and X > 0 ' ).iloc[0]
        self.worker.feeder    = self.df_feeders.query( 'Footprint == "'+str(row['Footprint'])+'" and Value =="'+str(row['Value'])+'" ').iloc[0]
        print("onSimButtonPartlist::Footprint",self.worker.footprint)
        print("onSimButtonPartlist::feeder",self.worker.feeder)
        self.worker.position_part_on_pcb = self.getMotorPositionForPart(row)
        self.worker.videoThreadTop = self.th
        self.worker.videoThreadBottom = self.th2
        self.worker.state_idx=0
        self.worker.start()


    def getMotorPositionForPart(self,row):      # TODO: extend for other PCBs on Pannel
        print("onGoButtonPartlist",row['X'],row['Y'])
        # Query nativ positions
        fd0_x = float(self.fiducials.query('Fiducial == "FD0" and PCB == 0 ').iloc[0]['X'])
        fd0_y = float(self.fiducials.query('Fiducial == "FD0" and PCB == 0 ').iloc[0]['Y'])
        fd1_x = float(self.fiducials.query('Fiducial == "FD1" and PCB == 0 ').iloc[0]['X'])
        fd1_y = float(self.fiducials.query('Fiducial == "FD1" and PCB == 0 ').iloc[0]['Y'])
        if ( fd0_x==0 or fd0_y==0 or fd1_x==0 or fd1_y==0 ):
            print("LERN first fiducials",fd0_x,fd0_y,fd1_x,fd1_y)
            return
        
        bom_fd0_x = self.df_parts.query('PART == "FD1" ').iloc[0]['X']
        bom_fd0_y = self.df_parts.query('PART == "FD1" ').iloc[0]['Y']
        bom_fd1_x = self.df_parts.query('PART == "FD2" ').iloc[0]['X']
        bom_fd1_y = self.df_parts.query('PART == "FD2" ').iloc[0]['Y']
        print("bom fiducials ",bom_fd0_x,bom_fd0_y,bom_fd1_x,bom_fd1_y)

        F1=Point(bom_fd0_x, bom_fd0_y)
        F2=Point(bom_fd1_x, bom_fd1_y)
        D=Point(  row['X'],row['Y'])
        print(F1)
        rect = convertRect(F1,F2,D,fd0_x,fd0_y,fd1_x,fd1_y) #
        return rect



    def onGoButtonPartlist(self,row):
        pos_to_move = self.getMotorPositionForPart(row)
        print("pos_to_move",pos_to_move[0],pos_to_move[1])
        print("angle",pos_to_move[2])
        self.gcode.driveto(( pos_to_move[0] , pos_to_move[1] ))                          

    #
    #
    #
    #
    def loadFiducialList(self):
        pannel_x = int(self.ui.pannel_x.text())
        pannel_y = int(self.ui.pannel_y.text())
        d = []
        pcb=0
        for p in range(pannel_x * pannel_y):
            # TODO: dont overwrite existing Fiducial Cords!
            d.append((pcb ,'FD0', 68.44 , 53.99))
            d.append((pcb ,'FD1', 31.75,  86.09))
            pcb+=1
        # print(d)
        self.fiducials  = pd.DataFrame(d, columns=('PCB','Fiducial','X','Y'))
        self.showPannelFiducialList()

    def showPannelFiducialList(self):
        grid = self.ui.fiducial_table 
        self.fiducials_list_headers = ['PCB','Fiducial','X','Y', 'Set','Go']
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        grid.setColumnCount(6)
        grid.setHorizontalHeaderLabels(self.fiducials_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # print(self.fiducials)

        grid.setRowCount(len(self.fiducials.index)) # x*y*2 fiducials
        for index, row in self.fiducials.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['PCB']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Fiducial']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setCellWidget(index, 4, ButtonBlock("Set",(index,row), self.onSetButtonFiducial))
            grid.setCellWidget(index, 5, ButtonBlock("Go",(index,row), self.onGoButtonFiducial))
        grid.itemChanged.connect(self.changeFiducialItem)
        self.showPreviewPannel()
    
    def changeFiducialItem(self,item):
        row = item.row()
        col = item.column()
        col_name = self.part_list_headers[col]
        # print ("changePartItemn",row,col,col_name,item.text())
        try:
            self.fiducials.at[row, col_name] = item.text()
        except:
            print ("changeFiducialItem ERROR invalid value",row,col,col_name,item.text())
            self.showPartList()   
    def onGoButtonFiducial(self,callbackData):
        index = callbackData[0]
        row = callbackData[1]
        print("onGoButtonFiducial",row['X'],row['Y'])
        self.gcode.driveto(( float(row['X']) , float(row['Y']) ))                          

    def onSetButtonFiducial(self,callbackData):
        index = callbackData[0]
        row = callbackData[1]
        self.fiducials.at[index, 'X'] = self.ui.gc_mpos_x.text()
        self.fiducials.at[index, 'Y'] = self.ui.gc_mpos_y.text()
        # print("onSetButtonFiducial",self.fiducials)
        self.showPannelFiducialList()




    #
    #
    #
    #
    def showPreviewPannel(self):
       
        # config Feeder Trays
        fachnr=0
        fachsize = 50.0
        tray_offset_x = 5
        tray_offset_y = 250
        trayParts = []
        for (i) in range(2):
            for (j) in range(4):
                trayParts.append(PNPFeeder('Tray',j * fachsize, i * fachsize, fachsize, fachsize))
                print('Tray1;',fachnr,';',j * fachsize + tray_offset_x ,';',i * fachsize + tray_offset_y,';',fachsize,';',fachsize)
                fachnr+=1



        trayParts[2].setConfig('C0603',  '10uF' ) # foorprint,value
        trayParts[3].setConfig('R0603',  '330K' ) # foorprint,value
        trayParts[5].setConfig('C0402K', '100nF' ) # foorprint,value
        traySet = PNPFeederSet('Tray1', 120.0 , 130.0,trayParts)

        trayParts2 = []
        for (i) in range(10):
            trayParts2.append(PNPFeeder('Tray2',8.0, i * 8.0, 70.0, 8.0))
        traySet2 = PNPFeederSet('Tray2', 20.0 , 120.0,trayParts2)

        parts = []
        for index, row in self.df_parts.iterrows():
            parts.append(PNPPart(row['PART'], row['X'],row['Y'],row['R'],row['Footprint'],row['Value']))
        
        
        pcb_h = float(self.ui.pcb_h.text())
        pcb_w = float(self.ui.pcb_w.text())
        pcb = PNPSinglePcb(parts,pcb_w,pcb_h,'FD1','FD2') # real pcb h,w on pannel

        pannel_x = int(self.ui.pannel_x.text())
        pannel_y = int(self.ui.pannel_y.text())
        pannel = PNPPcbPannel(pcb,5,20,(pannel_x,pannel_y)) # pcb Offset , layout

        pannel.scale=5.0
        
        #traySet.drawTrays(imageBlank)
        #traySet2.drawTrays(imageBlank)

        # ['PART','Footprint','Value','X', 'Y', 'R','Go']
        footprints={}
        for index, row in self.df_footprints.iterrows():
            footprints[row['Footprint']] = PNPFootprint({ 'x': row['X'], 'y': row['Y'], 'z': row['Z'] })
        #print(footprints)

        # create Image
        imageBlank = np.zeros((720, 800, 3), np.uint8)
        pannel.drawPcbs(imageBlank,footprints)
        h, w, ch = imageBlank.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(imageBlank.data, w, h, bytesPerLine, QImage.Format_RGB888)
        p = convertToQtFormat.scaled(1024, 768, Qt.KeepAspectRatio)
        self.ui.pannelpreview.setPixmap(QPixmap.fromImage(p))