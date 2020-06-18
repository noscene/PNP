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

        # simple Validation on numeric fields
        self.ui.gc_mpos_x.setValidator( QDoubleValidator(0, 230.0 ,8) )
        self.ui.gc_mpos_y.setValidator( QDoubleValidator(0, 280.0 ,8) )
      
        
        self.ui.pannel_update_bt.clicked.connect(self.loadFiducialList)



        # configure Video Thread
        self.th = VideoThread()
        self.th.myVideoFrame = self.ui.videoframe
        self.th.changePixmap.connect(self.th.setImageToGUI)
        self.th.start()
    
        self.ui.slider_h_min.valueChanged.connect(self.changeSlider_h_min)
        self.ui.slider_s_min.valueChanged.connect(self.changeSlider_s_min)
        self.ui.slider_v_min.valueChanged.connect(self.changeSlider_v_min)
        self.ui.slider_h_max.valueChanged.connect(self.changeSlider_h_max)
        self.ui.slider_s_max.valueChanged.connect(self.changeSlider_s_max)
        self.ui.slider_v_max.valueChanged.connect(self.changeSlider_v_max)

        self.visionParms={      'h_min' : 0,    's_min' : 0 ,   'v_min'  : 102 ,
                                'h_max' : 179,  's_max' : 255,  'v_max'  : 255 ,
                                'a_fac' : 8,    'a_lim' : 66,
                                'canny_thrs1' : 150,  'canny_thrs2' : 255,
                                'dilate_count' : 8,   'erode_count' : 6,
                                'gauss_v1' : 3,       'gauss_v2' : 3 }
    #
    # Helper Functions for Sliders
    def changeSlider_h_min(self):      self.th.parms['h_min'] = self.ui.slider_h_min.value()
    def changeSlider_s_min(self):      self.th.parms['s_min'] = self.ui.slider_s_min.value()
    def changeSlider_v_min(self):      self.th.parms['v_min'] = self.ui.slider_v_min.value()
    def changeSlider_h_max(self):      self.th.parms['h_max'] = self.ui.slider_h_max.value()
    def changeSlider_s_max(self):      self.th.parms['s_max'] = self.ui.slider_s_max.value()
    def changeSlider_v_max(self):      self.th.parms['v_max'] = self.ui.slider_v_max.value()
    def changeSlider_a_fac(self):      self.th.parms['a_fac'] = self.ui.slider_a_fac.value()

    #
    #
    def setFootprintTable(self):
          # QTableWidget
        grid = self.ui.footprint_table
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        df = self.df_footprints
        self.footprint_list_headers = ['Footprint','X', 'Y', 'H','Feeder','Nozzle','GoFeeder']
        grid.setColumnCount(7)
        grid.setHorizontalHeaderLabels(self.footprint_list_headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.setRowCount(len(df.index))
        for index, row in df.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['Feeder']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Footprint']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setItem(index,4,QtWidgets.QTableWidgetItem(str(row['H']))) 
            grid.setItem(index,5,QtWidgets.QTableWidgetItem(str(row['Nozzle']))) 
            grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonPartlist))
        grid.itemChanged.connect(self.changeFootprintItemn)

    def changeFootprintItemn(self,item):
        row = item.row()
        col = item.column()
        print ("changeItemn",row,col,item.text())

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
        grid.setColumnCount(7)
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
            grid.setCellWidget(index, 6, ButtonBlock("go",row, self.onGoButtonPartlist))
        grid.itemChanged.connect(self.changePartItemn)
    
    def changePartItemn(self,item):
        row = item.row()
        col = item.column()
        col_name = self.part_list_headers[col]
        # print ("changePartItemn",row,col,col_name,item.text())
        try:
            self.df_parts.at[row, col_name] = item.text()
        except:
            print ("changePartItemn ERROR invalid value",row,col,col_name,item.text())
            self.showPartList()   


    def onGoButtonPartlist(self,row):
        print("onGoButtonPartlist",row)





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
            d.append((pcb ,'FD0', 0.0, 0.0))
            d.append((pcb ,'FD1', 0.0, 0.0))
            pcb+=1
        # print(d)
        self.fiducials  = pd.DataFrame(d, columns=('PCB','Fiducial','X','Y'))
        self.showPannelFiducialList()

    def showPannelFiducialList(self):
        grid = self.ui.fiducial_table 
        headers = ['PCB','Fiducial','X','Y', 'Set']
        try: grid.itemChanged.disconnect() # avoid any msg when redraw
        except Exception: pass
        grid.setColumnCount(5)
        grid.setHorizontalHeaderLabels(headers)
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # print(self.fiducials)

        grid.setRowCount(len(self.fiducials.index)) # x*y*2 fiducials
        for index, row in self.fiducials.iterrows():
            grid.setItem(index,0,QtWidgets.QTableWidgetItem(str(row['PCB']))) 
            grid.setItem(index,1,QtWidgets.QTableWidgetItem(str(row['Fiducial']))) 
            grid.setItem(index,2,QtWidgets.QTableWidgetItem(str(row['X']))) 
            grid.setItem(index,3,QtWidgets.QTableWidgetItem(str(row['Y']))) 
            grid.setCellWidget(index, 4, ButtonBlock("Set",(index,row), self.onSetButtonFiducial))
        grid.itemChanged.connect(self.changePartItemn)
        self.showPreviewPannel()
    
    def changePartItemn(self,item):
        row = item.row()
        col = item.column()
        print ("changePannelItemn",row,col,item.text())
        # TODO: write Back to dataframe ?!?!?!

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
        trayParts = []
        for (i) in range(4):
            for (j) in range(5):
                trayParts.append(PNPFeeder('Tray',j * 15.0, i * 15.0, 15.0, 15.0))
                
        trayParts[18].setConfig('C0603',  '10uF' ) # foorprint,value
        trayParts[13].setConfig('R0603',  '330K' ) # foorprint,value
        trayParts[ 8].setConfig('C0402K', '100nF' ) # foorprint,value
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
        pannel = PNPPcbPannel(pcb,10,36,(pannel_x,pannel_y)) # pcb Offset , layout

        imageBlank = np.zeros((720, 800, 3), np.uint8)
        traySet.drawTrays(imageBlank)
        traySet2.drawTrays(imageBlank)

        footprints={    "C0603K":                               PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}), 
                        "C0603":                                PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
                        "R0603":                                PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
                        "0603":                                 PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
                        "0603-ARC":                             PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
                        "C0402K":                               PNPFootprint({'x':  1.0,  'y':  0.5,   'h': 0.5}),
                        "R0402":                                PNPFootprint({'x':  1.0,  'y':  0.5,   'h': 0.5}),
                        "EIA7343":                              PNPFootprint({'x':  7.3,  'y':  4.3,   'h': 2.8}), # TantalCaps
                        "PSON127P500X600X82-9N":                PNPFootprint({'x':  6.0,  'y':  5.0,   'h': 0.5}), # eSim QFN
                        "SEEED-SWITCH_SW4-SMD-4.2X3.2X2.5MM":   PNPFootprint({'x':  4.2,  'y':  3.2,   'h': 2.5}), # Button
                        "SOT89":                                PNPFootprint({'x':  4.6,  'y':  4.2,   'h': 1.8}), # LDO
                        "U.FL":                                 PNPFootprint({'x':  3.0,  'y':  2.8,   'h': 1.8}), # LDO
                        "SOT363":                               PNPFootprint({'x':  2.2,  'y':  2.2,   'h': 1.0}), # 0.5 innendurchmesser
                        "Qwiic":                                PNPFootprint({'x':  3.0,  'y':  5.0,   'h': 2.8}), # 0.5 innendurchmesser
                        "SIM800C":                              PNPFootprint({'x': 15.7,  'y': 17.6,   'h': 2.8}), # 0.5 innendurchmesser
                        "QFN50P700X700X100-49N":                PNPFootprint({'x': 10.0,  'y': 10.0,   'h': 2.8}), # 0.5 innendurchmesser
                        "QFN50P900X900X100-65N":                PNPFootprint({'x': 12.0,  'y': 12.0,   'h': 2.8}), # 0.5 innendurchmesser
                        "LQFP64L":                              PNPFootprint({'x': 12.0,  'y': 12.0,   'h': 2.8}), # 0.5 innendurchmesser
                        "WE-CON_SDMO-CN-9":                     PNPFootprint({'x': 12.0,  'y': 12.0,   'h': 2.8}), # 0.5 innendurchmesser
                        "ESP-WROOM32":                          PNPFootprint({'x': 18.0,  'y': 20.0,   'h': 3.1}) } 
        # Print CSV Data
        for fp in footprints:   print(fp,';',footprints[fp].parms['x'] ,';',footprints[fp].parms['y'] ,';',footprints[fp].parms['h']         )


        pannel.drawPcbs(imageBlank,footprints)
        h, w, ch = imageBlank.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(imageBlank.data, w, h, bytesPerLine, QImage.Format_RGB888)
        p = convertToQtFormat.scaled(1024, 768, Qt.KeepAspectRatio)
        self.ui.pannelpreview.setPixmap(QPixmap.fromImage(p))