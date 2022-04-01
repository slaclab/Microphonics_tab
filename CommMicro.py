# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 09:33:21 2021

@author: bob
"""

import sys
from pydm import Display
from PyQt5.QtGui import QStandardItem, QPixmap, QScreen
from PyQt5.QtWidgets import (QWidgetItem, QCheckBox, QPushButton, QLineEdit,
                             QGroupBox, QHBoxLayout, QMessageBox, QWidget,
          QApplication,QLabel, QFrame, QComboBox, QRadioButton,QFileDialog)
from os import path, pardir, makedirs, system, listdir
import subprocess
#from qtpy.QtCore import Slot, QTimer
from functools import partial, reduce
from datetime import datetime, timedelta
import sys
import numpy as np
from scipy.fftpack import fft, fftfreq
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# for ceil
import math

# FFt_math has utility functions
import FFt_math

LASTPATH=''
DEBUG=1
DATA_DIR_PATH = "/u1/lcls/physics/rf_lcls2/microphonics/"

class MplCanvas(FigureCanvasQTAgg):
# MPLCanvas is the class for the 'canvas' that plots are drawn on and then mapped to the ui
# They are Figure format described in matplotlib 2.2 documentation

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout="true")
# one axes per layout
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MicDisp(Display):

    def __init__(self, parent=None, args=None, ui_filename="FFT_test.ui"):
        super(MicDisp, self).__init__(parent=parent, args=args, ui_filename=ui_filename)
        self.pathHere = path.dirname(sys.modules[self.__module__].__file__)
        def getPath(fileName):
            return path.join(self.pathHere, fileName)

        # link up to the secondary display
        self.xfDisp = Display(ui_filename=getPath("MicPlot.ui"))

        # Show message on gui
        self.ui.AcqProg.setText("Select 1 CM and 1 cavity at a time for commissioning. \nLimit plotted waveforms to 30 sec.")         

        # create plot canvases and link to GUI elements
        TopPlot = MplCanvas(self, width = 20, height =40, dpi=100)
        BotPlot = MplCanvas(self, width = 20, height =40, dpi=100)
        self.xfDisp.ui.PlotTop.addWidget(TopPlot)
        self.xfDisp.ui.PlotBot.addWidget(BotPlot)
        
        # call function setGOVal when strtBut is pressed
        self.ui.StrtBut.clicked.connect(partial(self.setGOVal,TopPlot,BotPlot))  

        # call function getOldData when OldDatBut is pressed
        self.ui.OldDatBut.clicked.connect(partial(self.getOldData,TopPlot,BotPlot))  

        # This doesn't work yet.
        # call function plotWindow when printPlot is pressed
#        self.xfDisp.ui.printPlot.clicked.connect(self.plotWindow)

        # get CM IDs from FFt_math
        self.CM_IDs=FFt_math.CM_IDs()

        # set spinbox to 10 to start
        self.ui.spinBox.setValue(10)

        # fill combo boxes
        for cmid in self.CM_IDs:
          self.ui.CMComboBox.addItem(cmid)
        for cavnum in range(8):
          self.ui.CavComboBox.addItem(str(cavnum+1))


# This doesn't work yet
# Function to print the window
#    def plotWindow(self):
#        fname='plot.png'
#        app = QtWidgets.QApplication(sys.argv)
#        screen = QtWidgets.QApplication.primaryScreen()
#        screenshot = screen.grabWindow()
#        QScreen.grabWindow(app.primaryScreen(),
#          QApplication.desktop().winId()).save(fname,'png')
#        if path.exists(fname) and path.getsize(fname):
#            try:
#                system('lpr -Pphysics-lcls2log '+fname)
#            except:
#                print('Unable to print {} with apologies'.format(fname))
#        else:
#            print('creation of {} failed'.format(fname))

# This function takes given data (cavUno) and axis handle (tPlot) and calculates FFT and plots
    def FFTPlot(self, bPlot,cavUno):   

        N = len(cavUno)
        T = 1.0/1000 
        yf1 = fft(cavUno)
        xf = fftfreq(N, T)[:N//2]
        bPlot.axes.plot(xf, 2.0/N * np.abs(yf1[0:N//2]))

# This function gets info from the GUI, fills out LASTPATH, 
#  and returns liNac, cmNumStr, cavNumA, cavNumB

    def getUserVal(self):
        # I don't get why I need the global declaration
        global LASTPATH

        cavNumA=''
        cavNumB=''

        # get CM id from comboBox
        cmid=self.ui.CMComboBox.currentText()

        # grab the LxB part
        liNac=cmid.split(':')[1]

        # grab the CM number
        cmNumStr=cmid.split(':')[2]

        # only 1 cavity at a time for now, space at end for Bob
        cavNumStr=self.ui.CavComboBox.currentText()+' '

        # A & B refer to the racks, used in the data acq command
        if int(cavNumStr) <5:
          cavNumA=cavNumStr
          cavNumB=''
        else:
          cavNumA=''
          cavNumB=cavNumStr

        # Make the path name to be nice
        LASTPATH=DATA_DIR_PATH+'ACCL_'+liNac+'_'+cmNumStr+cavNumStr[0]+'0'

        return liNac, cmNumStr, cavNumA, cavNumB

# setGOVal is the response to the Get New Measurement button push
# it takes GUI settings and calls python script to fetch the data
#  then if Plotting is chosen, it calls getDataBack to make the plot

    def setGOVal(self,tPlot,bPlot):
        global LASTPATH
#        global count
        return_code=2

        # reads GUI inputs, fills out LASTPATH, and returns LxB, CMxx, and cav num
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    

        cavity=str(cavNumA + cavNumB)

        indexPlot=self.ui.comboBox.currentIndex()
#        print('indexPlot {}'.format(indexPlot))

        # This was a check to make sure only one cavity was chosen and I'm too lazy to 
        #  unindent the entire block that follows

        if (len(cavNumA)+len(cavNumB))==2:                      # If sum of len of cavity num strings is 2, one of the strings has a cavity numb$

            # Get time for measurement from spinbox
            timMeas = self.ui.spinBox.value()  
            count=timMeas+30

            self.ui.AcqProg.setText("Data acquisition started\n")

            resScrptSrce = "/usr/local/lcls/package/lcls2_llrf/srf/software/res_ctl/res_data_acq.py"
            morPath = "/u1/lcls/physics/rf_lcls2/microphonics/"
            s1 = datetime.now().strftime("%Y%m%d"+"_"+"%H%M%S")
            botPath = "ACCL_"+liNac+"_"+cmNumSt

            if cavNumA != '':
                botPath = botPath+cavNumA[0]+"0/"+botPath+cavNumA[0]+"0_"+s1
                caCmd = "ca://ACCL:"+liNac+":"+str(cmNumSt)+"00:RESA:"
                cavNums=cavNumA

            if cavNumB != '':
               botPath = botPath+cavNumB[0]+"0/"+botPath+cavNumB[0]+"0_"+s1
               caCmd = str("ca://ACCL:"+liNac+":"+str(cmNumSt)+"00:RESB:")
               cavNums=cavNumB

            # LASTPATH in this case ultimately looks like:
            #  /u1/lcls/physics/rf_lcls2/microphonics/ACCL_L0B_0110/ACCL_L0B_0110_20220329_151328
            #
            LASTPATH =  path.join(morPath, botPath)
            makedirs(LASTPATH, exist_ok=True)

            # This kinda cheats... really just ceil of timMeas/8
            #numbWaveF= str(timMeas//8 +int(timMeas % 8 > 0))
            numbWaveF = str(math.ceil(timMeas/8))
            cmdList= ['python',resScrptSrce,'-D',str(LASTPATH),'-a',caCmd,'-wsp','2','-acav',str(cavNums),'-ch','DF','-c',numbWaveF]
            print(cmdList)

            try:
                self.ui.AcqProg.setText("Data acquisition started\n")
                process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
                return_code = process.poll()
                out = out.decode(sys.stdin.encoding)
                err = err.decode(sys.stdin.encoding)
                print('Out: {}'.format(out))
                self.ui.AcqProg.setText("{}".format(out))

# success!
#                print('about to if-else with return_code {}'.format(return_code))
                if return_code==0:
                    self.ui.AcqProg.setText("File saved at \n"+LASTPATH)
                    if indexPlot==1:
                      try:
                        dirs=listdir(LASTPATH)
                        if dirs != []:
                          fname=path.join(LASTPATH,dirs[0])
                          self.getDataBack(fname,tPlot,bPlot)
                      except:
                        print('No data file found in {} to make plots from'.format(LASTPATH))

# unsuccess - if return_code != 0
                else: 
                    e = subprocess.CalledProcessError(return_code, cmdList, output=out)
                    e.stdout, e.stderr = out, err
                    self.ui.AcqProg.setText("Call to microphonics script failed \nreturn code: {}\nstderr: {}".format(return_code,str(e.stderr)))
                    print('stdout {0} stderr {1} return_code {2}'.format(e.stdout,e.stderr,return_code))
            except:
                self.ui.AcqProg.setText("Call to microphonics script failed \n")  
              
        return ()

# This function prompts the user for a file with data to plot
#  then calls getDataBack to plot it to axes tPlot and bPlot
#  The inputs of tPlot and bPlot are passed through to getDataBack

    def getOldData(self,tPlot,bPlot):
        global LASTPATH

        # clear message box in case there's anything still there
        self.ui.AcqProg.setText("Choose previous data file.")
        self.ui.AcqProg.adjustSize()

        # getUserVal sets LASTPATH from user input on the GUI
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    

        # fileDial is fun to say
        fileDial=QFileDialog()
        fname_tuple=fileDial.getOpenFileName(None,'Open File?',LASTPATH,'')
        if fname_tuple[0]!='':
          self.getDataBack(fname_tuple[0],tPlot,bPlot)

        return ()
    

# This function eats the data from filename fname and plots
#  a waterfall plot to axis tPlot and an FFT to axis bPlot

    def getDataBack(self,fname,tPlot,bPlot):

        cavDat1=[]

        if path.exists(fname):
            dFDat, throwAway = FFt_math.readCavDat(fname)
            cavDat1,cavDat2,cavDat3,cavDat4 = FFt_math.parseCavDat(dFDat)

            # figure out cavity from filename for legend
            idx=fname.find('res_cav')
            cavnum=fname[idx+7]
            
            leGend=[]
            leGend.append('Cav'+cavnum)
            tPlot.axes.cla()
            tPlot.axes.hist(cavDat1, bins=140,  histtype='step', log='True', edgecolor='b')
            # put file name on the plot
            parts=fname.split('/')
            tPlot.axes.set_title(parts[-2][5:],loc='left',fontsize='small')
            #tPlot.axes.set_xlim(-200, 200)
            tPlot.axes.set_ylim(bottom=1)
            tPlot.axes.set_xlabel('Detune (Hz)')
            tPlot.axes.set_ylabel('Counts')
            tPlot.axes.grid(True)
            tPlot.axes.legend(leGend)
            tPlot.draw_idle()  
               
            leGend2=[]
            leGend2.append('Cav'+cavnum)
            bPlot.axes.cla()
            self.FFTPlot(bPlot,cavDat1)
            bPlot.axes.set_xlim(0, 150)
            bPlot.axes.set_xlabel('Frequency (Hz)')
            bPlot.axes.set_ylabel('Relative Amplitude')
            bPlot.axes.grid(True)
            bPlot.axes.legend(leGend2)
            bPlot.draw_idle()  
                     
            self.showDisplay(self.xfDisp)   
       
        else:
            print("Couldn't find file {}".format(fname))
        return
   
    def showDisplay(self, display):
        # type: (QWidget) -> None
        display.show()
        # brings the display to the front
        display.raise_()
        # gives the display focus
        display.activateWindow()
