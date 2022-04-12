# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 09:33:21 2021

@author: bob

J Nelson 4 Apr 2022
new directory structure for data: 
$DATA_DIR_PATH/ACCL_LxB_CM00/yyyy/mm/dd/filename

add cm # to filename with -F switch
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

        # save the date
        self.startd = datetime.now()

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
        self.ui.TimSpinBox.setValue(10)

        # fill combo boxes
        for cmid in self.CM_IDs:
          self.ui.CMComboBox.addItem(cmid)
        self.ui.CavComboBox.addItem('Cavities 1-4')
        self.ui.CavComboBox.addItem('Cavities 5-8')

        #start out with cavities 1-4 selected
        self.checkboxes=[self.ui.cb1, self.ui.cb2, self.ui.cb3, self.ui.cb4]
        for idx,cb in enumerate(self.checkboxes):
          cb.setText(str(idx+1))

        # check the first box so there's Something
        self.ui.cb1.setChecked(True)
        # call function if cavity select combo box changes
        self.ui.CavComboBox.activated.connect(self.ChangeCav)

    def ChangeCav(self):
#   This function responds to a user changing the cavity combo box
#    from cavs 1-4 to cavs 5-8
        cavs=self.ui.CavComboBox.currentIndex()
        if cavs==0:
            delta=1
        else:
            delta=5
        for idx,cb in enumerate(self.checkboxes):
            cb.setText(str(idx+delta))


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

        # cavNumA/B are '1 2 3 4' with spaces in between for 
        #  script call
        # cavNumStr is '1234' for filename
        cavNumList=[]
        cavNumStr=''

        # get CM id from comboBox
        cmid=self.ui.CMComboBox.currentText()

        # grab the LxB part
        liNac=cmid.split(':')[1]

        # grab the CM number
        cmNumStr=cmid.split(':')[2]

        # read which rack - 0=A, 1=B
        rack=self.ui.CavComboBox.currentIndex()
        if rack==0:
          delta=1
        else:
          delta=5

        # load up cavNumStr ('1234') and cavNumList (['1','2','3','4'])
        for idx,cb in enumerate(self.checkboxes):
          if cb.isChecked():
            cavNumStr += str(idx+delta)
            cavNumList += str(idx+delta)

        # Make the path name to be nice
#        LASTPATH=DATA_DIR_PATH+'ACCL_'+liNac+'_'+cmNumStr+cavNumStr[0]+'0'
        LASTPATH=path.join(DATA_DIR_PATH,'ACCL_'+liNac+'_'+cmNumStr+'00')

        # get today's date as 2- or 4-char strings
        year=str(self.startd.year)
        month='%02d' % self.startd.month
        day='%02d' % self.startd.day
        LASTPATH=path.join(LASTPATH,year,month,day)

        return liNac, cmNumStr, cavNumStr

# setGOVal is the response to the Get New Measurement button push
# it takes GUI settings and calls python script to fetch the data
#  then if Plotting is chosen, it calls getDataBack to make the plot

    def setGOVal(self,tPlot,bPlot):
        global LASTPATH
        return_code=2

        # reads GUI inputs, fills out LASTPATH, and returns LxB, CMxx, and cav num
        liNac, cmNumSt, cavNumStr = self.getUserVal()    

        # Get time for measurement from spinbox
        timMeas = self.ui.TimSpinBox.value()  

        self.ui.AcqProg.setText("Data acquisition started\n")
        self.ui.AcqProg.repaint()

        resScrptSrce = "/usr/local/lcls/package/lcls2_llrf/srf/software/res_ctl/res_data_acq.py"

        # made the channel access spec for script call
        rack=self.ui.CavComboBox.currentIndex()
        AB='AB'
        caCmd = "ca://ACCL:"+liNac+":"+str(cmNumSt)+"00:RES"+AB[rack]+":"

        # LASTPATH in this case ultimately looks like:
        #  /u1/lcls/physics/rf_lcls2/microphonics/ACCL_L0B_0110/ACCL_L0B_0110_20220329_151328
        # /u1/lcls/physics/rf_lcls2/microphonics/ACCL_L0B_0100/yyyy/mm/dd/
        # LASTPATH =  path.join(morPath, botPath)
        # get LASTPATH from getUserVal()
        makedirs(LASTPATH, exist_ok=True)

        # This kinda cheats... really just ceil of timMeas/8
        #numbWaveF= str(timMeas//8 +int(timMeas % 8 > 0))
        numbWaveF = str(math.ceil(timMeas/8))

        # LASTPATH is the directory to put the datafile compliments of getUserVal()
        # Need to make output file name
        # Sergio had res_cav#_c#_yyyymmdd_hhmmss
        # Go to res_cm##_cav####_c#_yyyymmdd_hhmmss
        
        s1 = datetime.now().strftime("%Y%m%d"+"_"+"%H%M%S")
        outFile = 'res_CM'+cmNumSt+'_cav'+cavNumStr+'_c'+str(numbWaveF)+'_'+s1
        # print(outFile)
        # print(cavNumStr)

        # cmdList= ['python',resScrptSrce,'-D',str(LASTPATH),'-a',caCmd,'-wsp','2','-acav',str(cavNums),'-ch','DF','-c',numbWaveF,'-F',outFile]
        cmdList= ['python',resScrptSrce,'-D',str(LASTPATH),'-a',caCmd,'-wsp','2','-acav']
        for cav in cavNumStr:
            cmdList+=cav
        cmdList+= ['-ch','DF','-c',numbWaveF,'-F',outFile]
        print(cmdList)

        try:
            self.ui.AcqProg.setText("Data acquisition started\n")
            self.ui.AcqProg.repaint()
            process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = process.communicate()
            return_code = process.poll()
            print('Return code {}'.format(return_code))
            out = out.decode(sys.stdin.encoding)
            err = err.decode(sys.stdin.encoding)
            print('Out: {}'.format(out))
            if len(err)>0:
                print('Err: {}'.format(err))
            self.ui.AcqProg.setText("{}".format(out))
            self.ui.AcqProg.repaint()
# success!
#                print('about to if-else with return_code {}'.format(return_code))
            if return_code==0:
                self.ui.AcqProg.setText("File saved at \n"+LASTPATH)
                self.ui.AcqProg.repaint()

                # user requesting that plots be made
                if self.ui.PlotComboBox.currentIndex()==0:
                    try:
                        fname=path.join(LASTPATH,outFile)
                        if path.exists(fname):
                            self.getDataBack(fname,tPlot,bPlot)
                        else:
                            print('file doesnt exist {}'.format(fname))
                    except:
                        print('No data file found in {} to make plots from'.format(LASTPATH))

# unsuccess - if return_code != 0
            else: 
                print('return code is not0')
                e = subprocess.CalledProcessError(return_code, cmdList, output=out)
                e.stdout, e.stderr = out, err
                self.ui.AcqProg.setText("Call to microphonics script failed \nreturn code: {}\nstderr: {}".format(return_code,str(e.stderr)))
                self.ui.AcqProg.repaint()
                print('stdout {0} stderr {1} return_code {2}'.format(e.stdout,e.stderr,return_code))
        except:
            print('You are exceptional')
            self.ui.AcqProg.setText("Call to microphonics script failed \n")  
            self.ui.AcqProg.repaint()
              
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
        liNac, cmNumSt, cavNumStr = self.getUserVal()    

        # fileDial is fun to say
        fileDial=QFileDialog()
        fname_tuple=fileDial.getOpenFileName(None,'Open File?',LASTPATH,'')
        if fname_tuple[0]!='':
          self.getDataBack(fname_tuple[0],tPlot,bPlot)

        return ()
    

# This function eats the data from filename fname and plots
#  a waterfall plot to axis tPlot and an FFT to axis bPlot

    def getDataBack(self,fname,tPlot,bPlot):

        cavDataList=[]

        if path.exists(fname):
            dFDat, throwAway = FFt_math.readCavDat(fname)

            # this returns a list of lists of data values
            cavDataList = FFt_math.parseCavDat(dFDat)

            # figure out cavities from filename for legend
            fnameParts=fname.split('_')
            # find the fnamePart that starts with cav
            for part in fnameParts:
                if part.startswith('cav'):
                    cavnums=str(part[3:])

            tPlot.axes.cla()
            bPlot.axes.cla()
            leGend=[]
            leGend2=[]

            for idx,cavData in enumerate(cavDataList):
                if len(cavData)>0:
                    leGend.append('Cav'+cavnums[idx])
                    tPlot.axes.hist(cavData, bins=140,  
                               histtype='step', log='True')
               
                    leGend2.append('Cav'+cavnums[idx])
                    self.FFTPlot(bPlot,cavData)
                     
            # put file name on the plot
            parts=fname.split('/')
            tPlot.axes.set_title(parts[-1],loc='left',fontsize='small')
            #tPlot.axes.set_xlim(-200, 200)
            tPlot.axes.set_ylim(bottom=1)
            tPlot.axes.set_xlabel('Detune (Hz)')
            tPlot.axes.set_ylabel('Counts')
            tPlot.axes.grid(True)
            tPlot.axes.legend(leGend)
            tPlot.draw_idle()  

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
