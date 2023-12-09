import os, sys
import cv2
from datetime import date
import datetime
import glob
#from Tkinter import Frame, Tk, Label, Button, Scale, HORIZONTAL, Checkbutton, IntVar
from tkinter import *
#from tkFileDialog import *
from tkinter import filedialog
from tkinter.filedialog import askopenfilename, askdirectory

from PIL import Image, ImageStat, ImageDraw, ImageFont, TiffImagePlugin, ImageTk

import tkinter as tk
from scipy import ndimage

import scipy
#import pylab
from scipy import polyval, polyfit, ndimage
from pylab import polyfit, polyval
import time
import numpy as np
import threading


def load_calib():
	try:
		with open(os.path.join(sys.path[0], "calib.csv")) as csvfile:
			#next(csvfile) # ignore header
			a = [row.strip().split(',') for row in csvfile]
		######linear regression for min G
		x = [float(i[0]) for i in a]
		y = [float(i[3]) for i in a]
		(m,b) =polyfit(x,y,1)
		####################
		print (sum((polyval(polyfit(x,y,1),x)-y)**2)/(len(x)))
		####################
		mg=m
		bg=b
		######linear regression for G/R
		x = [float(i[1]) for i in a]
		y = [float(i[4]) for i in a]
		(m,b) =polyfit(x,y,1)
		mgr=m
		bgr=b

		######linear regression for G/B
		x = [float(i[2]) for i in a]
		y = [float(i[5]) for i in a]
		(m,b) =polyfit(x,y,1)
		mgb=m
		bgb=b
		############
		############
		x = [float(i[6]) for i in a]
		y = [float(i[8]) for i in a]
		(m,b) =polyfit(x,y,1)
		mmr=m
		bmr=b

		x = [float(i[7]) for i in a]
		y = [float(i[9]) for i in a]
		(m,b) =polyfit(x,y,1)
		mmg=m
		bmg=b


		print ("loaded calib")
	except:
		mg= 1.223
		bg=-111
		mgr=0.360
		bgr=0.589
		mgb=0.334
		bgb=0.534
		mmr=1.412
		bmr=-140.6
		mmg=0.134
		bmg=0.782

		print ("calib file not found")
		print ("Set to default arabidopsis values")

	return mg,bg,mgr,bgr,mgb,bgb, mmr, bmr, mmg, bmg

mgset, bgset, mgrset, bgrset, mgbset, bgbset, mmrset, bmrset, mmrgset, bmrgset = load_calib()

def takePic():
    global capture
    global capturedImage
    capture = True
    img = cap.read()[1]
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(img))
    # L1['image'] =  img
    global capturedImage
    capturedImage = img
    #root.update()


def retake():
    global capture
    capture = False

def secondStep():
    frame2.pack()
    frame1.pack_forget()

def backToFirst():
    frame2.pack_forget()
    frame1.pack()
    global capture
    capture = False
	

def auto_Settings(WhatData):
	pic = Image.open(curFile)
	speedP=8
	xsize, ysize = pic.size
	xsize=xsize/speedP
	ysize=ysize/speedP
	pic=pic.resize((int(xsize),int(ysize)))
	xsize, ysize = pic.size
	print (xsize,"x", ysize)
	ratG=2
	ratGb=1.8
	minG = 75
	cnt =0
	lpcntb = 0
	lpcnt =-1
	pixMinGreen = xsize*ysize*0.0025
	pic = pic.convert("RGB")
	pixels = pic.load() # create the pixel map
	while cnt <pixMinGreen:
		leafpix = []
		for i in range(pic.size[0]):    # for every pixel:
			for j in range(pic.size[1]):
				r, g, b = pixels[i,j]
				if r*ratG < g and b*(ratGb)<g  and g> minG:
					leafpix.append((r,g,b))
		lpcnt=lpcnt+1
		cnt=len(leafpix)
		if lpcnt <12:
			ratG = 0.94*ratG
			ratGb = 0.94*ratGb
		if lpcnt >11:
			minG = 0.9*minG
		if lpcnt >15:
			cnt =(pixMinGreen+10)
			print ("OOPS NOT ENOUGH LEAF PIXELS")

	print (minG, ratG, ratGb, "to select >",pixMinGreen," leaf pixels after", lpcnt, "loops")
	gavg=0
	gravg=0
	bravg=0
	if cnt==0: cnt=1
	for i in leafpix:
		r, g, b = i
		if r<1: r=g
		if g<1: g=0.1
		if b<1: b=g
		gavg=gavg+g
		gravg= gravg+(float(g)/float(r))
		bravg= bravg+(float(g)/float(b))

	gavg=float(gavg)/float(cnt)
	gravg=float(gravg)/float(cnt)
	bravg=float(bravg)/float(cnt)
	global ConsData
	#ConsData = [gavg, gravg, bravg]
	#print ConsData, "Values can be added to calib file"
	gavg= mgset*gavg+bgset
	if gavg <10: gavg=10
	minGscale.set(gavg)
	ratGscale.set(mgrset*gravg+bgrset)
	ratGbscale.set(mgbset*bravg+bgbset)

	ratR=2
	minR = 150
	cnt =0
	lpcntb = 0
	lpcnt =0
# Conservative pixel selection of 200+ pixels at 1/8th resolution:
	while cnt <pixMinGreen:
		scalepix=[]
		for i in range(pic.size[0]):    # for every pixel:
			for j in range(pic.size[1]):
				r, g, b = pixels[i,j]
				if g*ratR < r and b*(ratR)< r  and r> minR:
					scalepix.append((r,g,b))

		cnt=len(scalepix)
		lpcnt=lpcnt+1
		if lpcnt <8:
			ratR = 0.94*ratR
		if lpcnt >7:
			ratR = 2
			minR = 0.99*minR
		if lpcnt >10:
			cnt =(pixMinGreen+10)
	print (minR, ratR, "to select >",pixMinGreen," scale pixels after", lpcnt, "loops")
	ravg=0
	rgavg=0
	rbavg=0
	cnt=len(scalepix)
	if cnt>0:
		for i in scalepix:
			r, g, b = i
			if g<1: g=r
			if b<1: b=r
			ravg=ravg+r
			rgavg= rgavg+(float(r)/float(g))
			rbavg= rbavg+(float(r)/float(b))

		ravg=float(ravg)/float(cnt)
		rgavg=float(rgavg)/float(cnt)
		rbavg=float(rbavg)/float(cnt)
		rgavg=(rgavg+rbavg)/2
		rrat=mmrgset*rgavg+bmrgset
		if rrat <1.011: rrat=1.01
		minRscale.set(mmrset*ravg+bmrset)
		ratRscale.set(rrat)
	else:
		minRscale.set(255)
		ratRscale.set(2)
		print ("No Scale detected")
	ConsData = [gavg, gravg, bravg, ravg, rgavg]
	#print ConsData, "Values can be added to calib file"
	print (ravg, mmrset, bmrset, (mmrset*ravg+bmrset))
	#ratGbscale.set(0.334*bravg+0.534)
	return ConsData


def processELA():

		global timeT
		global today
		global dirF
		global dirS
		global curFile
		global takePic
		while True:
			if (today != date.today()):
				today = date.today()
				try:
					os.mkdir("images/"+str(today))
					
				except:
					print("Folder already exists")
			dirS = os.path.abspath("dump")
			dirF = "images/"+str(today)
			dirFz = "dump/"

			if not os.path.exists(dirF+f"/leafarea-{today}.csv"):
				try:
					with open(dirF+f"/leafarea-{today}.csv", "a") as f:
						f.write("filename,total green pixels,red pixels (4 cm^2),leaf area cm^2, Component green pixels:")
						f.write("\n")
				except:
					open (dirF+f"/leafarea-{today}.csv", "w")
					with open(dirF+'/leafarea.csv', "a") as f:
						f.write("filename,total green pixels,red pixels (4 cm^2),leaf area cm^2, Component green pixels:")
						f.write("\n")
			

				
				

			frame = cap.read()[1]
			frame11 = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
			frame = ImageTk.PhotoImage(Image.fromarray(frame11))
			
			image = Image.fromarray(frame11)
			
			timeT = str(datetime.datetime.now().today()).replace(":"," ") + ".jpg"
			image.save("dump/"+timeT)
			#L1 = tk.Label(image=frame, height =600, width = 800)
			#L1.image= frame
			#L1.grid(row =5, rowspan=50, column =2)
			#print('.')
			#main.update()
			curFile = os.path.join(dirS, timeT)
			curFile = os.path.join(dirS, timeT)
			pic = Image.open(curFile)
			file = os.path.basename(curFile)
			xsize, ysize = pic.size

			if (autocheck.get()):
				global ConsData
				ConsData = [0,0,0,0,0]
				auto_Settings(ConsData)
			(gCnt, rCnt, pic, pixdata) = Pixel_check(curFile, dirFz, file)
			if rCnt < 1:
				rCnt+=1
			leafarea = float(gCnt)/float(rCnt)*4.0
			if rCnt <2:
				rCnt = 0

			filelabel= Label (main, height =1, width=60)
			speedP=speedPscale.get()
			xsize=xsize/speedP
			ysize=ysize/speedP
			filelabel.configure (text = file+" "+str(xsize)+ "x"+str(ysize))
			filelabel.grid (row =1, column =2)
			Pixlabel = Label(main, height = 1, width = 60)
			Pixlabel.configure (text = "Leaf pixels: "+ str(gCnt)+ "   Scale pixels: "+ str(rCnt)+ "    Leaf area: "+ '%.2f' % leafarea+ "cm^2")
			Pixlabel.grid(row =2, column =2)
			
			highlightfile = dirF+f"/leafarea-{today}.csv"
			os.remove("dump/"+timeT)
			if takePic:
				save_Output(highlightfile, file, pixdata, pic, dirF)
				takePic = False
			print ("Finished processing images")
		#time.sleep(0.1)




capture = False

root = Tk()


cap = cv2.VideoCapture(0)


f1 = LabelFrame(root)
f1.pack()
picFrame = LabelFrame(f1)
picFrame.pack()
L1 = Label(picFrame)
L1.grid(column=0,row=0)
L2 = LabelFrame()

frame1 = LabelFrame(f1)
frame1.pack()


retakeButton = Button(frame1,text="Retake",height=2,width=15,command=retake)
retakeButton.grid(row=0,column=0,sticky=W,padx=100) 

captureButton = Button(frame1,text="Capture",height=2,width=15,command=takePic)
captureButton.grid(row=0,column=1,padx=100) 

nextButton = Button(frame1,text="Next",height=2,width=15,command=secondStep)
nextButton.grid(row=0,column=2,sticky=E,padx=100)

frame2 = LabelFrame(f1)

backButton = Button(frame2,text="Back",height=2,width=15,command=backToFirst)
backButton.grid(row=0,column=0,sticky=W,padx=30) 

calibrateButton = Button(frame2,text="Calibrate",height=2,width=15,command=takePic)
calibrateButton.grid(row=0,column=1,padx=30) 

processButton = Button(frame2,text="Process",height=2,width=15,command=secondStep)
processButton.grid(row=0,column=2,sticky=E,padx=30)

next2Button = Button(frame2,text="Next",height=2,width=15,command=secondStep)
next2Button.grid(row=0,column=3,sticky=E,padx=30)

frame3 = LabelFrame(picFrame)
frame3.grid(column=1,row=0)
autocheck = IntVar()
C4 = Checkbutton(frame3, text = "Use auto settings", variable = autocheck)
C4.pack()
minG =100
minGscale = Scale(frame3, from_=0, to=255, label="Leaf minimum Green RGB value:", orient=HORIZONTAL, tickinterval = 50, length = 250, variable = minG )
minGscale.set(25)
minGscale.pack()


autocheck.get()

















#threading.Thread(target=liveImage).start()
while True:
    if capture == False:
        img = cap.read()[1]
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(img))
        L1['image'] = img
       
    root.update() 

#cap.release()