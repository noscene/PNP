from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import cv2
import numpy as np

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
        self.setFootprintTable()
        
        # configure Video Thread
        self.th = VideoThread()
        self.th.myVideoFrame = self.ui.videoframe
        self.th.changePixmap.connect(self.th.setImageToGUI)
        self.th.start()
    


    #
    #
    #
    #
    def setFootprintTable(self):
          # QTableWidget
        grid = self.ui.footprint_table
        grid.setColumnCount(6)
        grid.setHorizontalHeaderLabels(['macAddr','Name', 'RSSI', 'TX Power','xx','cc'])
        grid.setRowCount(10)
        #ui.footprint_table.resizeColumnsToContents()
        grid.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.setCellWidget(6, 4, ButtonBlock("1"))
        grid.setCellWidget(7, 4, ButtonBlock("2"))
        grid.setCellWidget(8, 4, ButtonBlock("3"))
        grid.itemChanged.connect(self.changeFootprintItemn)
    
    def changeFootprintItemn(self,item):
        row = item.row()
        col = item.column()
        print ("changeItemn",row,col,item.text())

    #
    #
    #
    #
    def showPartList(self,df):
        print("showPartList",df)
        self.df_parts = df
        grid = self.ui.parts_table 
        headers = ['PART','Footprint','Value','X', 'Y', 'R','Go']
        grid.setColumnCount(7)
        grid.setHorizontalHeaderLabels(headers)
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
        print ("changeItemn",row,col,item.text())
        # TODO: write Back to dataframe ?!?!?!

    def onGoButtonPartlist(self,row):
        print("onGoButtonPartlist",row)