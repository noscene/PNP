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

    gui.df_parts = pd.read_csv('test_m104.mnt', sep="\s+", names=["PART","X","Y","R","Value","Footprint"] )

    gui.setFootprintTable()
    gui.setFeederTable()
    gui.showPartList()
    gui.loadFiducialList()
    gui.showPreviewPannel()


    # show App and start
    ui.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()
