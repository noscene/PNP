import pandas as pd
import sys
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.uic import loadUi

from PNPGCode import *
from PNPGui import *

def main():
    #faulthandler.enable()
    # python3 -q -X faulthandler PNPApp.py

    application = QtWidgets.QApplication(sys.argv)

    ui = loadUi('pnp2.ui')
    # connect the G-Code Driver Class 
    gcode = PNPGCode('/dev/ttyUSB0')
    gcode.setupGui(ui)          # Setup Button Callback for gcode commands
    gui = PNPGui(ui,gcode)      # create UI

    # names=["Tray","NR","X","Y","W","H","Z","Footprint","Value","Vision"]
    df_feeders = pd.read_csv('feeder.csv', sep=";", header=0  )
    gui.df_feeders = df_feeders.applymap(lambda x: x.strip() if isinstance(x, str) else x) # Trim Strings for query


    df_footprints = pd.read_csv('footprints.csv', sep=";", names=["Footprint","X","Y","Z"] )
    gui.df_footprints = df_footprints.applymap(lambda x: x.strip() if isinstance(x, str) else x) # Trim Strings for query

    # 0201 -> 501
    # 0402 -> 502
    # 0603 / 0805 -> 0503
    # 1206 -> 504
    # http://www.firepick.org/assets/pdf/juki-nozzle-catalogue-rev-c3.pdf
 
    gui.df_footprints['Feeder']='1'
    gui.df_footprints['Nozzle']='1'

    df_parts = pd.read_csv('test_m104.mnt', sep="\s+", names=["PART","X","Y","R","Value","Footprint"] )
    df_parts['Placed']='0'
    df_parts.to_csv('test_m104.csv', sep=";", header=True,index=False, columns=["PART","X","Y","R","Value","Footprint","Placed"])

    #df_parts = df_parts[df_parts['PART'].str.contains("7") | df_parts['Footprint'].str.contains('7')]     

    gui.df_parts = df_parts.sort_values(by=['Value','PART']).reset_index(drop=True)

    gui.setFootprintTable()
    gui.setFeederTable()
    gui.showPartList()
    gui.loadFiducialList()
    gui.showPreviewPannel()


    gui.loadVisionList()




    # show App and start
    ui.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()
