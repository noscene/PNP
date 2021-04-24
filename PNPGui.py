from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json
import sys
import subprocess
import cv2
import numpy as np
import pandas as pd

from VideoThread import *
from PNPHelpers import *
from PNPWorker import *
from QTHelpers import *


class PNPGui():
    def __init__(self,ui,gcode):
        self.ui=ui
        self.gcode=gcode
        self.df_parts=None
        self.df_footprints=None
        self.df_feeders=None

        self.mm_faktor_x = 55.2 / 1280.0  # 1024x768 => 1024 = 52mm TODO: add to setting dataframe
        self.mm_faktor_y = 40.0 / 960.0

        self.currentTab=0

        # simple Validation on numeric fields
        self.ui.gc_mpos_x.setValidator( QDoubleValidator(0, 230.0 ,8) )
        self.ui.gc_mpos_y.setValidator( QDoubleValidator(0, 280.0 ,8) )
        self.ui.pcb_preview_scale.setValidator( QDoubleValidator(0, 12.0 ,8) )
        self.ui.status_label.setText("-")
        self.ui.status_label.setStyleSheet('color: red')
        self.ui.pannel_update_bt.clicked.connect(self.loadFiducialList)
        self.ui.tabs.currentChanged.connect(self.onTabChange)

        if(sys.platform == 'linux'):
            command = "v4l2-ctl -d /dev/video0 -c exposure_auto=1"
            output = subprocess.call(command, shell=True)
            command = "v4l2-ctl -d /dev/video1 -c exposure_auto=1"
            output = subprocess.call(command, shell=True)


        self.visionData={}
        self.ui.save_vision_as.clicked.connect(self.save_vision_as)

        # init default Vision Settings
        self.videoParms1 = self.getVisionSliderValues()
        self.videoParms2 = self.getVisionSliderValues()
        #self.videoParms2['expose'] = 16
        #self.videoParms1['expose'] = 70

        # configure Video Thread
        self.th = VideoThread()
        self.th.parms = self.getVisionSliderValues() # read defaultParms from Sliders
        if(sys.platform == 'linux'):    self.th.cam="/dev/video0"
        else:                           self.th.cam=1
        self.th.changePixmap.connect(self.setImageToGUICamTop)
        self.th.mode=0
        self.th.crosshair_color = (0,0,255)
        #self.th.w = 1600
        #self.th.h = 1200
        self.ui.videoframe.clicked.connect(self.onVideoMouseEvent) 
        self.th.openVideo()
    

        # configure Video Thread
        self.th2 = VideoThread()
        self.th2.parms = self.getVisionSliderValues() # read defaultParms from Sliders
        # self.th2.parms['expose'] = 70
        if(sys.platform == 'linux'):    self.th2.cam="/dev/video1"
        else:                           self.th2.cam=0
        self.th2.changePixmap.connect(self.setImageToGUICamBottom)
        self.th2.mode=0
        self.th2.w = 800
        self.th2.h = 600
        self.th2.crosshair_color = (255,0,0)
        self.th2.flip=True
        self.ui.videoframe_2.clicked.connect(self.onVideoMouseEvent2) 
        self.th2.openVideo()
        #self.th2.start()


        self.th.start()


        # add Worker 
        self.worker = PNPWorker()
        self.worker.mm_faktor_x = self.mm_faktor_x
        self.worker.mm_faktor_y = self.mm_faktor_y
        self.worker.gcode = self.gcode
        self.worker.event.connect(self.on_worker_event)
        self.ui.check_step.clicked.connect(self.onCheckStep)

        # callback for Vision slider parms
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
        self.ui.slider_canny_thrs1.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_canny_thrs2.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_dilate.valueChanged.connect(self.changeSlider4Vision)
        self.ui.slider_erode.valueChanged.connect(self.changeSlider4Vision)
        self.ui.check_toogle_cam.clicked.connect(self.on_check_toogle_cam)
        
    #@pyqtSlot(np.ndarray) ->
    def setImageToGUICamTop(self, image):
        qt_img = self.ui.videoframe.convert_cv_qt(image)
        self.ui.videoframe.setPixmap(qt_img) # TODO: check for Thread bug
        self.th2.parms = self.videoParms2
        self.th2.mode=self.currentTab
        self.th2.start()
    #@pyqtSlot(QImage)
    #@pyqtSlot(np.ndarray) -> TypeError: connect() failed between VideoThread.changePixmap[numpy.ndarray] and setImageToGUICamTop()
    def setImageToGUICamBottom(self, image):
        qt_img = self.ui.videoframe_2.convert_cv_qt(image)
        self.ui.videoframe_2.setPixmap(qt_img) # TODO: check for Thread bug   
        self.th.parms = self.videoParms1
        self.th.mode  = self.currentTab
        self.worker.videoThreadTop = obj({  'min_obj_x'     : self.th.min_obj_x,
                                            'min_obj_y'     : self.th.min_obj_y,
                                            'min_obj_angel' : self.th.min_obj_angel,
                                            'real_w'        : self.th.real_w,
                                            'real_h'        : self.th.real_h})
        self.th.start()

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
    
    
    
    def setVisionSliderLabelValues(self,p):
        self.ui.label_h_min.setText("h_min: " + str(p['h_min']))
        self.ui.label_s_min.setText("s_min: " + str(p['s_min']))
        self.ui.label_v_min.setText("v_min: " + str(p['v_min']))
        self.ui.label_h_max.setText("h_max: " + str(p['h_max']))
        self.ui.label_s_max.setText("s_max: " + str(p['s_max']))
        self.ui.label_v_max.setText("v_max: " + str(p['v_max']))
        self.ui.label_a_min.setText("a_min: " + str(p['a_min']))
        self.ui.label_a_max.setText("a_max: " + str(p['a_max']))
        self.ui.label_expose.setText("expose: " + str(p['expose']))
        self.ui.label_a_fac.setText("a_fac: " + str(p['a_fac']))
        self.ui.label_kernel.setText("kernel: " + str(p['kernel']))
        self.ui.label_dilate.setText("dilate_count: " + str(p['dilate_count']))
        self.ui.label_erode.setText("erode_count: " + str(p['erode_count']))
        self.ui.label_canny_thrs1.setText("canny_thrs1: " + str(p['canny_thrs1']))
        self.ui.label_canny_thrs2.setText("canny_thrs2: " + str(p['canny_thrs2']))
    #
    # Helper Functions for Sliders
    def setVisionSliderValues(self,p):
        self.ui.slider_h_min.setValue(p['h_min'])
        self.ui.slider_h_max.setValue(p['h_max'])
        self.ui.slider_s_min.setValue(p['s_min'])
        self.ui.slider_s_max.setValue(p['s_max'])
        self.ui.slider_v_min.setValue(p['v_min'])
        self.ui.slider_v_max.setValue(p['v_max'])
        self.ui.slider_a_min.setValue(p['a_min'])
        self.ui.slider_a_max.setValue(p['a_max'])
        self.ui.slider_expose.setValue(p['expose'])
        self.ui.slider_a_fac.setValue(p['a_fac'])
        self.ui.slider_kernel.setValue(p['kernel'])
        self.ui.slider_canny_thrs1.setValue(p['canny_thrs1']) 
        self.ui.slider_canny_thrs2.setValue(p['canny_thrs2']) 
        self.ui.slider_dilate.setValue(p['dilate_count']) 
        self.ui.slider_erode.setValue(p['erode_count']) 
        #p['gauss_v1'] = 3
        #p['gauss_v2'] = 3


    def getVisionSliderValues(self):
        p= {}
        p['h_min'] = self.ui.slider_h_min.value()
        p['h_max'] = self.ui.slider_h_max.value()
        p['s_min'] = self.ui.slider_s_min.value()
        p['s_max'] = self.ui.slider_s_max.value()
        p['v_min'] = self.ui.slider_v_min.value()
        p['v_max'] = self.ui.slider_v_max.value()
        p['a_min'] = self.ui.slider_a_min.value()
        p['a_max'] = self.ui.slider_a_max.value()
        p['expose'] = self.ui.slider_expose.value()
        p['a_fac'] = self.ui.slider_a_fac.value()
        p['kernel'] = self.ui.slider_kernel.value()
        p['canny_thrs1'] = self.ui.slider_canny_thrs1.value() 
        p['canny_thrs2'] = self.ui.slider_canny_thrs2.value() 
        p['dilate_count'] = self.ui.slider_dilate.value() 
        p['erode_count'] = self.ui.slider_erode.value() 
        p['gauss_v1'] = 3
        p['gauss_v2'] = 3
        self.setVisionSliderLabelValues(p)
        return p





    def changeSlider4Vision(self):
        parms = self.getVisionSliderValues()
        print("changeSlider4Vision", parms)
        if(self.ui.check_toogle_cam.checkState()):
            self.videoParms1 = parms
        else:
            self.videoParms2 = parms

    def on_check_toogle_cam(self):
        print("on_check_toogle_cam")
        if(self.ui.check_toogle_cam.checkState()):
            self.setVisionSliderValues(self.videoParms1.copy())
        else:
            self.setVisionSliderValues(self.videoParms2.copy())


    def onVideoMouseEvent2(self):
        mouse_click = self.ui.videoframe_2.mouse_click
        xm = (1280/2 - mouse_click[0]) 
        ym = 480/2 - mouse_click[1]
        if(xm==0): xm=1 # avoid div/0
        if(ym==0): ym=1 # avoid div/0
        xmabs=abs(xm)
        alpha = math.atan(ym/xmabs) - (np.pi * 0.5)
        alpha*= 180/np.pi
        if(xm<0):
            alpha*=-1
        print("onVideoMouseEvent2",xm,ym,alpha) # TODO: change angle by mouse click ?
        self.gcode.update_rotation_relative(alpha)

    def onVideoMouseEvent(self):
        mouse_click = self.ui.videoframe.mouse_click
        print("onVideoMouseEvent",mouse_click)

        # 40 / 960
        x = (1280/2 - mouse_click[0]) * -1
        y = 960/2   - mouse_click[1]
        print("onVideoMouseEvent2",x * self.mm_faktor_x ,y * self.mm_faktor_y)
        self.gcode.update_position_relative( x * self.mm_faktor_x , y * self.mm_faktor_y )  


    def onTabChange(self,i):
        print("onTabChange TODO refresh Data on this event: ",i)
        self.currentTab = i
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
        grid.setColumnCount(6)
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
            #grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonFootprint))
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
    #def onGoButtonFootprint(self,item):
    #    print("onGoButtonFootprint",item)

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
        print("onGoButtonFeeder",item.Vision,item.X + item.W / 2.0 , item.Y + item.H / 2.0)
        self.ui.save_vision_name.setText(item.Vision)   
        if item.Vision in self.visionData:
            self.videoParms1 = self.visionData[str(item.Vision)]['T']
            self.videoParms2 = self.visionData[str(item.Vision)]['B']    
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



            error_row_count=0
            # query for existing Footprint, need trim strings on import!
            query = 'Footprint == "'+str(row['Footprint'])+'" and X > 0 '
            if self.df_footprints.query( query )['Footprint'].count() == 0:
                grid.item(index, 1).setBackground(Qt.yellow)
                error_row_count+=1

            query = 'Footprint == "'+str(row['Footprint'])+'" and Value =="'+str(row['Value'])+'" '
            if self.df_feeders.query( query )['Value'].count() == 0:
                grid.item(index, 2).setBackground(Qt.yellow)                
                error_row_count+=1

            grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonPartlist))
            if(error_row_count==0):
                grid.setCellWidget(index, 7, ButtonBlock("Sim",(index,row), self.onSimButtonPartlist))

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

    def onSimButtonPartlist(self,obj):
        row = obj[1]
        index = obj[0]
        print("onSimButtonPartlist", index, row)
        self.ui.parts_table.item(index, 0).setBackground(Qt.green)  

        self.worker.footprint = self.df_footprints.query( 'Footprint == "'+str(row['Footprint'])+'" and X > 0 ' ).iloc[0]
        self.worker.feeder    = self.df_feeders.query( 'Footprint == "'+str(row['Footprint'])+'" and Value =="'+str(row['Value'])+'" ').iloc[0]
        print("onSimButtonPartlist::Footprint",self.worker.footprint)
        print("onSimButtonPartlist::feeder",self.worker.feeder)
        self.worker.position_part_on_pcb = self.getMotorPositionForPart(row)

        # Load Vision
        visionSetting = self.worker.feeder['Vision']
        print("onSimButtonPartlist::Vision",visionSetting)
        self.ui.save_vision_name.setText(visionSetting)   
        if visionSetting in self.visionData:
            self.videoParms1 = self.visionData[str(visionSetting)]['T']
            self.videoParms2 = self.visionData[str(visionSetting)]['B']   


        self.ui.status_label.setText("PLACE " + row.PART + " " + row.Value + " " + row.Footprint + " Vision: " + visionSetting)

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
        self.ui.status_label.setText("GO " + row.PART + " " + row.Value + " " + row.Footprint)
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
            d.append((pcb ,'FD0', 92.50 , 50.37))
            d.append((pcb ,'FD1', 55.43,  82.67))
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
    def loadVisionList(self):
        try:
            with open('vision_'+sys.platform+'.json') as f:
                self.visionData = json.load(f)
        except Exception: pass
        print(self.visionData)
        grid = self.ui.visionTable 
        self.vision_list_headers = ['Name','JSON','Go']
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        grid.setColumnCount(3)
        grid.setHorizontalHeaderLabels(self.vision_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # print(self.fiducials)
        i=0
        grid.setRowCount(len(self.visionData)) # x*y*2 fiducials
        for key  in self.visionData:
            grid.setItem(i,0,QtWidgets.QTableWidgetItem(str(key))) 
            grid.setItem(i,1,QtWidgets.QTableWidgetItem(str(self.visionData[key]))) 
            grid.setCellWidget(i, 2, ButtonBlock("Load",(key,self.visionData[key],i), self.onLoadVision))
            i+=1
        #grid.itemChanged.connect(self.changeFiducialItem)

    def save_vision_as(self):
        name = self.ui.save_vision_name.text()
        self.visionData[name] = {'T':self.videoParms1,'B':self.videoParms2}
        with open('vision_'+sys.platform+'.json', 'w') as json_file:
            json.dump(self.visionData, json_file,  indent = 4, sort_keys=True)

        self.loadVisionList()

    def onLoadVision(self,callbackData):
        key = callbackData[0]
        row = callbackData[1]        
        index = callbackData[2]     
        self.ui.save_vision_name.setText(key)   
        print("onLoadVision",key,index,row)
        self.videoParms1 = row['T']
        self.videoParms2 = row['B']
        self.on_check_toogle_cam()

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

        pannel.scale=float(self.ui.pcb_preview_scale.text())
        
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

