# -*- coding: utf-8 -*-
"""
Created on Wed Aug  4 09:33:21 2021

@author: bob
"""

from pydm import Display
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import (QWidgetItem, QCheckBox, QPushButton, QLineEdit,
                             QGroupBox, QHBoxLayout, QMessageBox, QWidget,
                             QLabel, QFrame, QComboBox, QRadioButton)
from os import path, pardir, makedirs
from os import listdir
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
        self.xfDisp = Display(ui_filename=getPath("MicPlot.ui"))  
        self.ui.AcqProg.setText("Select 1 CM and 1 cavity at a time for commissioning. \nLimit plotted waveforms to 30 sec.")         
        TopPlot = MplCanvas(self, width = 20, height =40, dpi=100)
        BotPlot = MplCanvas(self, width = 20, height =40, dpi=100)
        self.xfDisp.ui.PlotTop.addWidget(TopPlot)
        self.xfDisp.ui.PlotBot.addWidget(BotPlot)
        
        # call function setGOVal when strtBut is pressed
        self.ui.StrtBut.clicked.connect(partial(self.setGOVal,TopPlot,BotPlot))  

        # call function getOldData when OldDatBut is pressed
        self.ui.OldDatBut.clicked.connect(partial(self.getOldData,TopPlot,BotPlot))  

# get CM IDs from FFt_math
        self.CM_IDs=FFt_math.CM_IDs()

# fill combo boxes
        for cmid in self.CM_IDs:
          self.ui.CMComboBox.addItem(cmid)
        for cavnum in range(8):
          self.ui.CavComboBox.addItem(str(cavnum+1))

    def FFTPlot(self, ac,cavUno):   
        N = len(cavUno)
        T = 1.0/1000 
#        x = np.linspace(0.0, N*T, N, endpoint=False)
#        y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x)
        yf1 = fft(cavUno)
        xf = fftfreq(N, T)[:N//2]
        ac.axes.plot(xf, 2.0/N * np.abs(yf1[0:N//2]))

        
#    def showTime(self,ac):
#        global count
#        count = count +30
#        self.ui.AcqProg.setText("Data Acquisition started. "+str(count)+" sec left.")	# decrementing the counter
#        count -= 1
#        if count<0:
#            self.timer.stop()
#        return      

    def getUserVal(self):
# I don't get why I need the global declaration
        global LASTPATH

        cavNumA=''
        cavNumB=''
#        cmNum = self.ui.spinBox_2.value()  # Get Cryomodule number from spinBox_2
        cmid=self.ui.CMComboBox.currentText()

# grab the LxB part
        liNac=cmid.split(':')[1]

# grab the CM number
        cmNumStr=cmid.split(':')[2]
                                                                 
# only 1 cavity at a time for now, space at end for Bob
        cavNumStr=self.ui.CavComboBox.currentText()+' '
        if int(cavNumStr) <5:
          cavNumA=cavNumStr
          cavNumB=''
        else:
          cavNumA=''
          cavNumB=cavNumStr

# Make the path name to be nice
        LASTPATH=DATA_DIR_PATH+'ACCL_'+liNac+'_'+cmNumStr+cavNumStr[0]+'0'

        return liNac, cmNumStr, cavNumA, cavNumB

# too scared to change ac = axis C? to top plot, ac2 is bottom plot
    def setGOVal(self,ac,ac2):
#        global lastPath
        global LASTPATH
        global count
        return_code=2
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    # This gets the User inputs from the spinBox and checkboxes
#                                                               # cmNumSt is a string of the cm number. cavNumA & B are strings of cavities chec$

        cavity=str(cavNumA + cavNumB)

# instead of if lastPath, use if DEBUG while debugging
#        if lastPath[48:50]==cmNumSt and lastPath[50:51] == cavity[0:1]:
#        if LASTPATH[48:50]==cmNumSt and LASTPATH[50:51] == cavity[0:1]:
        if DEBUG:
# don't need the outputs, need the function to fill in LASTPATH
            a,b,c,d=self.getUserVal()
            self.getDataBack(ac,ac2)

        else: 
            if (len(cavNumA)+len(cavNumB))==2:                      # If sum of len of cavity num strings is 2, one of the strings has a cavity numb$

                timMeas = self.ui.spinBox.value()  # Get time for measurement from spinBox
                count=timMeas+30

                self.ui.AcqProg.setText("Data acquisition started\n")

                resScrptSrce = "/usr/local/lcls/package/lcls2_llrf/srf/software/res_ctl/res_data_acq.py"
#            resScrptSrce = "$PACKAGE_TOP/lcls2_llrf/srf/software/res_ctl/res_data_acq.py"
#            morPath = "$PHYSICS_DATA/rf_lcls2/microphonics/"
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

                LASTPATH =  path.join(morPath, botPath)
                makedirs(LASTPATH, exist_ok=True)

                numbWaveF= str(int(timMeas//8)+(timMeas % 8 > 0))
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

                    if return_code==0:
                        self.ui.AcqProg.setText("File saved at \n"+LASTPATH)
                        if indexPlot==1:
                          try:
                            dirs=listdir(LASTPATH)
                            if dirs != []:
                              fname=path.join(LASTPATH,dirs[0])
                              self.getDataBack(fname,ac,ac2)
                          except:
                            print('No data file found in {} to make plots from'.format(LASTPATH))

                    else: #if return_code !=0:
                        e = subprocess.CalledProcessError(return_code, cmdList, output=out)
                        e.stdout, e.stderr = out, err
                        self.ui.AcqProg.setText("Call to microphonics script failed \n"+str(e.stderr))
                        print('stdout {0} stderr {1} return_code {2}'.format(e.stdout,e.stderr,return_code))
                except:
                    self.ui.AcqProg.setText("Call to microphonics script failed \n")  
              
        return ()

    def getOldData(self,ac,ac2):
        global LASTPATH
        global count
        return_code=2
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    # This gets the User inputs from the spinBox and checkboxes
#                                                               # cmNumSt is a string of the cm number. cavNumA & B are strings of cavities chec$
        self.getDataBack(ac,ac2)

        return ()
    
    def getDataBack(self,fname,ac,ac2):
# assume we only call this if we want to plot something.
        cavDat1=[]
        cavNumA=''
        cavNumB=''          

        if path.exists(fname):
            dFDat, throwAway = FFt_math.readCavDat(FilePlusPath)
            cavDat1,cavDat2,cavDat3,cavDat4 = FFt_math.parseCavDat(dFDat)

# figure out cavity from filename
            idx=fname.find('res_cav')
            cavnum=fname[idx+7]
            
            leGend=[]
            leGend.append('Cav'+cavnum)
            ac.axes.cla()
            ac.axes.hist(cavDat1, bins=140,  histtype='step', log='True', edgecolor='b')
            ac.axes.set_xlim(-20, 20)
            ac.axes.set_ylim(bottom=1)
            ac.axes.set_xlabel('Detune in Hz')
            ac.axes.set_ylabel('Cnts')
            ac.axes.grid(True)
            ac.axes.legend(leGend)
            ac.draw_idle()  
               
            leGend2=[]
            leGend2.append('Cav'+cavnum)
            ac2.axes.cla()
            self.FFTPlot(ac2,cavDat1)
            ac.axes.set_xlim(0, 150)
            ac.axes.set_xlabel('Freq, Hz')
            ac.axes.set_ylabel('Rel Amplitude')
            ac.axes.grid(True)
            ac.axes.legend(leGend2)
            ac.draw_idle()  
                     
            self.showDisplay(self.xfDisp)   
       
        else:
            print('Couldn't find file {}'.format(fname))                 
        return
   
    def showDisplay(self, display):
        # type: (QWidget) -> None
        display.show()
        # brings the display to the front
        display.raise_()
        # gives the display focus
        display.activateWindow()
