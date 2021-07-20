# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 17:08:16 2021

@author: bob
"""
#import scipy.fft
#from scipy.fft import fft, fftfreq
from scipy.fftpack import fft, fftfreq
import matplotlib.pyplot as plt
from os import devnull, path, makedirs
import numpy as np


read_data=[]

def readCavDat(fileName):
    header_Data=[]
    with open(fileName) as f:
        for lin in range(28):
            header_Data.append(f.readline())
        read_data = f.readlines()
       
    f.close()
    return(read_data, header_Data)
# Number of sample points

def parseCavDat(read_data):
    cavDat1 = [] 
    cavDat2 = [] 
    cavDat3 = []
    cavDat4 = []
    for red in read_data:

        cavDat1.append(float(red[0:8]))
        if red[10:18] != '':
            cavDat2.append(float(red[10:18]))
        if red[20:28] != '':
            cavDat3.append(float(red[20:28]))
        if red[30:38] != '':
            cavDat4.append(float(red[30:38]))
#print(cavDat3)
    return(cavDat1,cavDat2,cavDat3,cavDat4)

def dummyFileCreator(pathToDatafile):
#    print(pathToDatafile)
    data, Header = readCavDat("1234_20210617_1227")
    brkFile='0/'
    indxFilName = pathToDatafile.find(brkFile,0)
    NewFileName=pathToDatafile[indxFilName+2:]+"_microphonics.dat"
    f = open(pathToDatafile+"/"+NewFileName, "w")
    for i in range(len(Header)):
        f.write(str(Header[i]))
    cavDat1, cavDat2,cavDat3, cavDat4 = parseCavDat(data)
    for i in range(len(cavDat2)):
        f.write(str(cavDat2[i])+"\n")
    f.close()    
    return 

def compatibleMkdirs(filename):
    makedirs(path.dirname(filename), exist_ok=True)
    return (filename)