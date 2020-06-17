import pandas as pd
import sys
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.uic import loadUi

from PNPGCode import *
from PNPGui import *

def main():
    global myVideoFrame
    application = QtWidgets.QApplication(sys.argv)

    ui = loadUi('pnp.ui')
    # connect the G-Code Driver Class 
    gcode = PNPGCode('/dev/ttyUSB0')
    gcode.setupGui(ui)          # Setup Button Callback for gcode commands
    gui = PNPGui(ui,gcode)      # create UI

    df = pd.read_csv('test_m104.mnt', sep="\s+", names=["PART","X","Y","R","Value","Footprint"] )
    gui.showPartList(df)


    # known footprints
    footprints={ "C0603K":                              PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}), 
                "C0603":                                PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
                "R0603":                                PNPFootprint({'x':  1.6,  'y':  0.8,   'h': 0.5}),
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
                "ESP-WROOM32":                          PNPFootprint({'x': 18.0,  'y': 20.0,   'h': 3.1}) } 

    # Print CSV Data
    for fp in footprints:   print(fp,',',footprints[fp].parms['x'] ,',',footprints[fp].parms['y'] ,',',footprints[fp].parms['h']         )

    df_footprints = pd.read_csv('footprints.csv', sep=",", names=["Footprint","X","Y","H"] )
    print(df_footprints)

    # just define 2 heads for simulation -> same position = single head
    # Todo Add Nozzle Type e.g. 502
    head = PNPHead(PNPVision(), [   PNPNozzle(-45.0,36.0,['C0603','R0603']),
                                    PNPNozzle(-45.0,36.0,['R0402','C0402K']) ])

    parts = []
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
    traySet2 = PNPFeederSet('Tray2', 20.0 , 130.0,trayParts2)

    for index, row in df.iterrows():
        parts.append(PNPPart(row['PART'], row['X'],row['Y'],row['R'],row['Footprint'],row['Value']))
    pcb = PNPSinglePcb(parts,53.1,56,'FD1','FD2') # real pcb h,w on pannel
    pannel = PNPPcbPannel(pcb,10,10,(3,2)) # pcb Offset , layout

    imageBlank = np.zeros((720, 800, 3), np.uint8)
    traySet.drawTrays(imageBlank)
    traySet2.drawTrays(imageBlank)
    pannel.drawPcbs(imageBlank,footprints)
    h, w, ch = imageBlank.shape
    bytesPerLine = ch * w
    convertToQtFormat = QImage(imageBlank.data, w, h, bytesPerLine, QImage.Format_RGB888)
    p = convertToQtFormat.scaled(1024, 768, Qt.KeepAspectRatio)
    ui.pannelpreview.setPixmap(QPixmap.fromImage(p))

    #plt.figure(figsize = (15,14)) # bigger screen
    #plt.imshow(imageBlank)
    #plt.show()


    # show App and start
    ui.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()
