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

lastPath=''

class MplCanvas(FigureCanvasQTAgg):
# MPLCanvas is the class for the 'canvas' that plots are drawn on and then mapped to the ui
# They are Figure format described in matplotlib 2.2 documentation

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout="true")
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MicDisp(Display):

    def __init__(self, parent=None, args=None, ui_filename="FFT_test.ui"):
        super(MicDisp, self).__init__(parent=parent, args=args, ui_filename=ui_filename)
        self.pathHere = path.dirname(sys.modules[self.__module__].__file__)
        def getPath(fileName):
            return path.join(self.pathHere, fileName)
        self.xfDisp = Display(ui_filename=getPath("MicPlot.ui"))  
        XfelPlot = MplCanvas(self, width = 20, height =40, dpi=100)
        self.ui.AcqProg.setText("Select 1 CM and 1 cavity at a time for commissioning. \nLimit plotted waveforms to 30 sec.")         
        self.xfDisp.ui.Plot3.addWidget(XfelPlot)
        
        self.ui.StrtBut.clicked.connect(partial(self.setGOVal,XfelPlot))  # call function setGOVal when strtBut is pressed

#  Timer would NOT interrupt subprocess call.      self.timer= QTimer()                            # start timer to track data acq     
#        self.timer.timeout.connect(partial(self.showTime,XfelPlot))
                   

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
        cavNumA=''
        cavNumB=''               
        cmNum = self.ui.spinBox_2.value()  # Get Cryomodule number from spinBox_2
        if cmNum==1:
            liNac="L0B" 
        elif cmNum > 1 and cmNum < 4:
            liNac = "L1B" 
        elif cmNum > 3 and cmNum < 16:
            liNac = "L2B"
        else:
            liNac = "L3B"
     
        if cmNum<10:                
            cmNumSt='0'+str(cmNum)
        else:
            cmNumSt=str(cmNum)           
                                                                 
        if self.ui.Cav1.isChecked():
            cavNumA=cavNumA+'1 '
        if self.ui.Cav2.isChecked():
            cavNumA=cavNumA+'2 '
        if self.ui.Cav3.isChecked():
            cavNumA=cavNumA+'3 '
        if self.ui.Cav4.isChecked():
            cavNumA=cavNumA+'4 '
        if self.ui.Cav5.isChecked():
            cavNumB=cavNumB+'5 '
        if self.ui.Cav6.isChecked():
            cavNumB=cavNumB+'6 ' 
        if self.ui.Cav7.isChecked():
            cavNumB=cavNumB+'7 ' 
        if self.ui.Cav8.isChecked():
            cavNumB=cavNumB+'8 '           

        return liNac, cmNumSt, cavNumA, cavNumB

    def setGOVal(self,ac):
        global lastPath
        global count
        return_code=2
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    # This gets the User inputs from the spinBox and checkboxes
#                                                               # cmNumSt is a string of the cm number. cavNumA & B are strings of cavities chec$

        cavity=str(cavNumA + cavNumB)
        if lastPath[48:50]==cmNumSt and lastPath[50:51] == cavity[0:1]:
            self.getDataBack(ac)

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
                   cavNums=cavNumA

                lastPath =  path.join(morPath, botPath)
                makedirs(lastPath, exist_ok=True)

                numbWaveF= str(int(timMeas//8)+(timMeas % 8 > 0))
                cmdList= ['python',resScrptSrce,'-D',str(lastPath),'-a',caCmd,'-wsp','2','-acav',str(cavNums),'-ch','DF','-c',numbWaveF]
#            print(cmdList)

#            FFt_math.dummyFileCreator(lastPath)
#                cmd=["ls","/usr/local/lcls/package/lcls2_llrf/srf/software/res_ctl"]

                try:
                    self.ui.AcqProg.setText("Data acquisition started\n")
                    process = subprocess.Popen(cmdList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = process.communicate()
                    return_code = process.poll()
                    out = out.decode(sys.stdin.encoding)
                    err = err.decode(sys.stdin.encoding)
                    print(out)

                    if return_code==0:
                        self.ui.AcqProg.setText("File saved at \n"+lastPath)
                        self.getDataBack(ac)

                    if return_code !=0:
                        e = subprocess.CalledProcessError(return_code, cmdList, output=out)
                        e.stdout, e.stderr = out, err
                        self.ui.AcqProg.setText("Call to microphonics script failed \n"+str(e.stderr))
                    
                except:
                    self.ui.AcqProg.setText("Call to microphonics script failed \n")  
              
            elif (len(cavNumA) + len(cavNumB)) > 2:  
                self.ui.AcqProg.setText("Only one cavity can be selected. \nTry again")

            else:
                self.ui.AcqProg.setText("No Cavity selected. try again")
        return ()
    
    def getDataBack(self,ac):
        cavDat1=[]
        cavNumA=''
        cavNumB=''          
        global lastPath
        liNac, cmNumSt, cavNumA, cavNumB = self.getUserVal()    
# =============================================================================
# This is where I need to add the code to go find the correct files to be read back in
# and I still need to parse the files to  read the data from the cavities selected
# =============================================================================
# #             
        dirs = listdir(lastPath)
#        print("dirs = ",dirs)
        if dirs != []:
            for entry in dirs:

                FilePlusPath = lastPath+"/"+entry
                dFDat, throwAway = FFt_math.readCavDat(FilePlusPath)
                cavDat1,cavDat2,cavDat3,cavDat4 = FFt_math.parseCavDat(dFDat)

            indexPlot = self.ui.comboBox.currentIndex()        

            if indexPlot ==1:
                leGend=[]
                ac.axes.cla()
                ac.axes.hist(cavDat1, bins=140,  histtype='step', log='True', edgecolor='b')
                if '1' in cavNumA:
                    leGend.append('Cav1')
                if '2' in cavNumA:
                    leGend.append('Cav2')
                if '3' in cavNumA:
                    leGend.append('Cav3')
                if '4' in cavNumA:
                    leGend.append('Cav4')
                if '5' in cavNumB:
                    leGend.append('Cav5')
                if '6' in cavNumB:
                    leGend.append('Cav6')
                if '7' in cavNumB:
                    leGend.append('Cav7')
                if '8' in cavNumB:                 
                    leGend.append('Cav8')
                ac.axes.set_xlim(-20, 20)
                ac.axes.set_ylim(bottom=1)
                ac.axes.set_xlabel('Detune in Hz')
                ac.axes.set_ylabel('Cnts')
                ac.axes.grid(True)
                ac.axes.legend(leGend)
                ac.draw_idle()  
               
            if indexPlot == 2:
                leGend=[]
                ac.axes.cla()
                self.FFTPlot(ac,cavDat1)
                if '1' in cavNumA:
                    leGend.append('Cav1')
                if '2' in cavNumA:
                    leGend.append('Cav2')
                if '3' in cavNumA:
                    leGend.append('Cav3')
                if '4' in cavNumA:
                    leGend.append('Cav4')
                if '5' in cavNumB:
                    leGend.append('Cav5')
                if '6' in cavNumB:
                    leGend.append('Cav6')
                if '7' in cavNumB:
                    leGend.append('Cav7')
                if '8' in cavNumB:                
                    leGend.append('Cav8')
                ac.axes.set_xlim(0, 150)
                ac.axes.set_xlabel('Freq, Hz')
                ac.axes.set_ylabel('Rel Amplitude')
                ac.axes.grid(True)
                ac.axes.legend(leGend)
                ac.draw_idle()  
                     
            self.showDisplay(self.xfDisp)   
       
            if indexPlot==0:
                self.xfDisp.close()
                self.ui.AcqProg.setText("Microphonics data saved to file")
        else:
            self.ui.AcqProg.setText("No file created. No data saved.")                 
        return
   
    def showDisplay(self, display):
        # type: (QWidget) -> None
        display.show()
        # brings the display to the front
        display.raise_()
        # gives the display focus
        display.activateWindow()
