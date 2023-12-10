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
	if capture:
		frame2.pack()
		frame1.pack_forget()

def backToSecond():
	global calibrate
	frame5.pack_forget()
	frame2.pack()
	calibrate = False
	try:
		L0.grid_forget()
		frame3.grid_forget()
	except:
		pass


def backToFirst():
	global calibrate
	global capture
	global processELAdone
	global imtkexists
	imtkexists = False
	processELAdone = False
	calibrate = False
	capture = False
	frame1.pack()
	try:
		L0.grid_forget()
		frame3.grid_forget()
	except:
		pass

	frame5.pack_forget()
	frame2.pack_forget()

	try:
		frame4.grid_forget()
	except:
		pass
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


def Show_pic(pic):
	global L1
	global imtk
	
	im = pic.copy()
	im = im.resize((400,400), Image.LANCZOS)
	im.thumbnail((800,800), Image.LANCZOS)
	imtk=ImageTk.PhotoImage(im)
	L1['image'] = imtk


def Pixel_check(curFile, dirF, file):
	pic = Image.open(curFile)
	pic2= Image.open(curFile)
	picr= Image.open(curFile)
	if (rotPic.get()):
		print ("Rotating picture 180")
		pic = pic.rotate(180)
	if (flipPic.get()):
		print ("Flipping picture")
		pic = pic.transpose(Image.FLIP_LEFT_RIGHT)
	imgdata = pic.load()
	print (file, " loaded")

	speedP=speedPscale.get()
	xsize, ysize = pic.size
	xsize=xsize/speedP
	ysize=ysize/speedP
	pic=pic.resize((int(xsize),int(ysize)))
	pic2=pic2.resize((int(xsize),int(ysize)))
	picr=picr.resize((int(xsize),int(ysize)))
	xsize, ysize = pic.size
	print (xsize,"x", ysize)
	minG=minGscale.get()
	minR=minRscale.get()
	ratG=ratGscale.get()
	ratGb=ratGbscale.get()
	ratR=ratRscale.get()
	##################################
	global mingGactual, ratGactual, ratGbactual
	mingGactual = minG
	ratGactual = ratG
	ratGbactual = ratGb
	#################################
	#print minG, minR, ratG, ratR
	pic = pic.convert("RGB")
	pixels = pic.load() # create the pixel map
	leafpix = []
	scalepix = []
	backpix = []
	leafonly = pic2.load()
	scaleonly = picr.load()
	for i in range(pic.size[0]):    # for every pixel:
		for j in range(pic.size[1]):
			#print pixels[i,j]
			r, g, b = pixels[i,j]
			if r*ratG < g and b*ratGb<g  and g> minG:
				leafpix.append((i,j))
				leafonly[i,j] = (0,255,0)
				scaleonly[i,j] = (0,0,0)
			else:
				leafonly[i,j] = (0,0,0)
				if r>minR and g*ratR<r and b*ratR<r :
					scalepix.append((i,j))
					#pixels[i,j] = (0,0,255)
					scaleonly[i,j] = (255,0,0)
				else:
					backpix.append((i,j))
					scaleonly[i,j] = (0,0,0)
	gCnt=len(leafpix)
	#rCnt=len(scalepix)
	if (delBack.get()):
		for i in backpix:
			pixels[i] = (255,255,255)



	#pic2 = Image.open(pic2)
	pic2 = pic2.convert('L')
	flat = np.array(pic2)

#	picr = Image.open(picr)
	picr = picr.convert('L')
	flatr = np.array(picr)



#	flat = scipy.misc.fromimage(pic2,flatten=1)
#	flatr= scipy.misc.fromimage(picr,flatten=1)

	blobs, leaves = ndimage.label(flat)
	blobsr, scales = ndimage.label(flatr)
	scalehist=ndimage.measurements.histogram(blobsr, 1,scales,scales)
#########################################
#Blob analysis.  Only the largest red blob is analyzed as scale area
	try: maxscale=max(scalehist)
	except: pass
	cnt=1
	gcnt=0
	parcnt=0
	rCnt=0
	largescale = []
	for s in scalehist:
		#print s
		#if s>1000:
		if s == maxscale:
			cnti=0
			cntj=0
			gcnt=0
			parcnt=parcnt+1
			for i in range(pic.size[0]):    # for every pixel:
				for j in range(pic.size[1]):
					if blobsr[j,i]==cnt:
						gcnt=gcnt+1
						rCnt=rCnt+1
						cnti=cnti+i
						cntj=cntj+j
						pixels[i,j]=(255,0,0)
						flat[j,i] = (0)
			cnti=cnti/gcnt
			cntj=cntj/gcnt
			largescale.append(gcnt)
			if labpix.get():
				draw=ImageDraw.Draw(pic)
				draw.text((cnti,cntj),str(gcnt), (0,0,0))


		cnt=cnt+1
############
#Leaf blob analysis
	blobhist=ndimage.measurements.histogram(blobs, 1,leaves,leaves)
	minPsize=minPscale.get()

########largest leaf elements only instead of minimum particle size
	try: maxleaf=max(blobhist)
	except: pass
	if ThereCanBeOnlyOne.get():
		cnt=1
		gcnt=0
		parcnt=0
		gCnt=0
		largeleaf = []
		for s in blobhist:
			if s == maxleaf:
				cnti=0
				cntj=0
				gcnt=0
				parcnt=parcnt+1
				for i in range(pic.size[0]):    # for every pixel:
					for j in range(pic.size[1]):
						if blobs[j,i]==cnt:
							gcnt=gcnt+1
							gCnt=gCnt+1
							cnti=cnti+i
							cntj=cntj+j
							pixels[i,j]=(0,255,0)
							flat[j,i] = (0)
				cnti=cnti/gcnt
				cntj=cntj/gcnt
				largeleaf.append(gcnt)
				if labpix.get():
					draw=ImageDraw.Draw(pic)
					draw.text((cnti,cntj),str(gcnt), (0,0,0))


			cnt=cnt+1
		leafprint= ', '.join(map(str, largeleaf))
#Leaf element minimum particle size:
	elif minPsize>10:
		cnt=1
		gcnt=0
		parcnt=0
		gCnt=0
		largeleaf = []
		for s in blobhist:
			if s>minPsize:
				cnti=0
				cntj=0
				gcnt=0
				parcnt=parcnt+1
				for i in range(pic.size[0]):    # for every pixel:
					for j in range(pic.size[1]):
						if blobs[j,i]==cnt:
							gcnt=gcnt+1
							gCnt=gCnt+1
							cnti=cnti+i
							cntj=cntj+j
							pixels[i,j]=(0,255,0)
							flat[j,i] = (0)
				cnti=cnti/gcnt
				cntj=cntj/gcnt
				largeleaf.append(gcnt)
				if labpix.get():
					draw=ImageDraw.Draw(pic)
					draw.text((cnti,cntj),str(gcnt), (0,0,0))
			cnt=cnt+1
		leafprint= ', '.join(map(str, largeleaf))
	else:
		print ("NO CONNECTED COMPONENT ANALYSIS")
		for i in leafpix:
			pixels[i] = (0,255,0)
		leafprint = "No connected component analysis"
	if rCnt < 1:
		rCnt+=1
	scalesize = SSscale.get()

	if scalesize ==0:
		print ("No scale.  Leaf areas not to scale")
		#scalesize =1
	leafarea = float(gCnt)/float(rCnt)*scalesize
	Show_pic(pic)
	highlightfile = dirF+'/leafarea.csv'
	pixdata=file+', '+str(gCnt)+', '+str(rCnt)+', '+'%.2f' % leafarea+','+leafprint+'\n'

	return gCnt, rCnt, pic, pixdata


def save_Output():
	global dirF
	global highlightfile
	global file
	global pixdata
	global pic
	print ("save output")
	with open(highlightfile, "a") as f:
		f.write(pixdata)
	tifffile = file.replace('.jpg', '.tiff')
	pic.save(dirF+'/highlight'+tifffile)

def showCalibraiton():
	global calibrate
	if calibrate == False:
		calibrate = True
		L0.grid(column=0,row=0)
		frame3.grid(column=2,row=0)
	else:
		L0.grid_forget()
		frame3.grid_forget()
		calibrate=False

def processELA():
		global processELAdone
		global timeT
		global today
		global dirF
		global dirS
		global curFile
		global imtkexists
		global highlightfile
		global file
		global pixdata
		global pic

		imtkexists = True

		processELAdone = True
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
		

			
			
		
		image = Image.fromarray(img2)
		
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

		filelabel= Label (frame4, height =1, width=30)
		speedP=speedPscale.get()
		xsize=xsize/speedP
		ysize=ysize/speedP
		filelabel.configure (text = file+" ")
		filelabel.grid (row =1, column =2)
		
		Pixlabel = Label(frame4, height = 5, width = 30)
		Pixlabel.configure (text = "Leaf pixels: "+ str(gCnt)+ " \n Scale pixels: "+ str(rCnt)+ " \n Leaf area: "+ '%.2f' % leafarea+ "cm^2")
		Pixlabel.grid(row =2, column =2)
		frame4.grid(column=3,row=0)
		highlightfile = dirF+f"/leafarea-{today}.csv"
		os.remove("dump/"+timeT)

		
		print ("Finished processing images")
	#time.sleep(0.1)


def saveStep():
	global processELAdone
	if processELAdone:
		frame5.pack()
		frame2.pack_forget()
		

		try:
			L0.grid_forget()
			frame3.grid_forget()
		except:
			pass



capture = False

root = Tk()

root.title("Easy Leaf Area")

root.attributes('-fullscreen',True)

#change scaling ratio
root.tk.call('tk','scaling',1)

processELAdone = False
cap = cv2.VideoCapture(1)


f1 = LabelFrame(root)
f1.pack()
picFrame = LabelFrame(f1)
picFrame.pack()
L1 = Label(picFrame)
L1.grid(column=1,row=0)
L0 = Label(picFrame)
#L0.grid(column=0,row=0)

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

calibrateButton = Button(frame2,text="Calibrate",height=2,width=15,command=showCalibraiton)
calibrateButton.grid(row=0,column=1,padx=30) 

processButton = Button(frame2,text="Process",height=2,width=15,command=processELA)
processButton.grid(row=0,column=2,sticky=E,padx=30)

next2Button = Button(frame2,text="Next",height=2,width=15,command=saveStep)
next2Button.grid(row=0,column=3,sticky=E,padx=30)

frame3 = LabelFrame(picFrame)
#frame3.grid(column=2,row=0)

frame4 = LabelFrame(picFrame)


frame5 = LabelFrame(f1)

backButton2 = Button(frame5,text="Back",height=2,width=15,command=backToSecond)
backButton2.grid(row=0,column=0,sticky=W,padx=30) 

saveButton = Button(frame5,text="Save",height=2,width=15,command=save_Output)
saveButton.grid(row=0,column=1,padx=30) 

homeButton = Button(frame5,text="Home",height=2,width=15,command=backToFirst)
homeButton.grid(row=0,column=2,sticky=E,padx=30)


autocheck = IntVar()



flipPic = IntVar()
C1 = Checkbutton(L0, text = "Flip image horizontal", variable = flipPic)
C1.pack()
flipPic.get()

rotPic = IntVar()
C2 = Checkbutton(L0, text = "Rotate image 180 deg", variable = rotPic)
C2.pack()
rotPic.get()


delBack = IntVar()
C3 = Checkbutton(L0, text = "Delete background", variable = delBack)
C3.pack()
delBack.get()

autocheck = IntVar()
C4 = Checkbutton(L0, text = "Use auto settings", variable = autocheck)
C4.pack()
autocheck.get()


labpix = IntVar()
C5 = Checkbutton(L0, text = "Label Pixels", variable = labpix)
C5.pack()
labpix.get()


ThereCanBeOnlyOne = IntVar()
C6 = Checkbutton(L0, text = "Only one Leaf component", variable = ThereCanBeOnlyOne)
C6.pack()
ThereCanBeOnlyOne.get()



minG =100
minGscale = Scale(frame3, from_=0, to=255, label="Leaf minimum Green RGB value:", orient=HORIZONTAL, tickinterval = 50, length = 250, variable = minG )
minGscale.set(25)
minGscale.pack()


ratG =1.2
ratGscale = Scale(frame3, from_=0.9, to=2, resolution = 0.02, label="Leaf Green Ratio: (G/R)", orient=HORIZONTAL, tickinterval = 0.5, length = 200, variable = ratG )
ratGscale.set(1.05)
ratGscale.pack()


ratGb =1.35
ratGbscale = Scale(frame3, from_=0.8, to=2, resolution = 0.02, label="Leaf Green Ratio: (G/B)", orient=HORIZONTAL, tickinterval = 0.5, length = 200, variable = ratGb )
ratGbscale.set(1.07)
ratGbscale.pack()

minR =200
minRscale = Scale(frame3, from_=0, to=255, label="Scale minimum Red RGB value:", orient=HORIZONTAL, tickinterval = 50, length = 250, variable = minR )
minRscale.set(225)
minRscale.pack()

ratR =1.3
ratRscale = Scale(frame3, from_=1, to=2, resolution = 0.02, label="Scale Red Ratio: (R/G & R/B)", orient=HORIZONTAL, tickinterval = 0.5, length = 200, variable = ratR )
ratRscale.set(1.95)
ratRscale.pack()

speedP =1
speedPscale = Scale(frame3, from_=1, to=8, resolution = 1, label="Processing Speed:", orient=HORIZONTAL, tickinterval = 1, length = 200, variable = speedP )
speedPscale.set(4)
speedPscale.pack()


minPsize =500
minPscale = Scale(frame3, from_=1, to=5000, resolution = 10, label="Minimum Leaf Size (pixels):", orient=HORIZONTAL, tickinterval = 1000, length = 250, variable = minPsize )
minPscale.pack()
minPscale.set(0)

Scalesize =4.1
SSscale = Scale(frame3, from_=0, to=20, resolution = 0.1, label="Scale area (cm^2):", orient=HORIZONTAL, tickinterval = 4, length = 250, variable = Scalesize )
SSscale.pack()
SSscale.set(4)
calibrate = False
today = ""
imtkexists = False
while True:
	if capture == False:
		img = cap.read()[1]
		img2 = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
		img = ImageTk.PhotoImage(Image.fromarray(img2))
		L1['image'] = img 
	elif imtkexists:
		L1['image'] = imtk
	
       
	root.update() 

#cap.release()