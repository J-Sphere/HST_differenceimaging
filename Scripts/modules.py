#!/usr/bin/env python
from __future__ import print_function

import os, sys, math
from astropy.io import fits
from astropy import wcs
from astropy.time import Time
import numpy as np
##############
# CLASSES
##############

###
#FitsFile
###
class FitsFile():
	def __init__(self, path, pattern=0):
		self.path=path
		self.pattern=pattern
		hdulist=fits.open(self.path, mode='update')

		self.mainhead=hdulist[0].header
		self.mainhead1=hdulist[1].header
		try:
			self.mainhead4=hdulist[4].header
		except IndexError:
			pass
		if pattern==0: self.hdulist=hdulist
		elif pattern == 1:
			self.hdulist_data={}
			self.hdulist_header={}
			for i in range(len(hdulist)):
				self.hdulist_data[i]=hdulist[i]
		self.name=self.path.split('/')[-1]
		self.c1, self.c2, self.c3, self.c4 = None, None, None, None
		self.other_corners=[]
		if pattern == 1: hdulist.close()
	#def __str__(self):
	#	return self.name
	def keyword(self, kw, ext=0):
		if self.pattern==1:
			if ext == 0: keyword=self.mainhead[kw]
			elif ext==1: keyword=self.mainhead1[kw]
			elif ext==4: keyword=self.mainhead4[kw]
			return(keyword)
		else:
			return(self.hdulist[ext].header[kw])
	
	def set(self, keyword='KEYWORD', value='value'):
		#if self.pattern==1:
	      	#self.hdulist=fits.open(self.path)
       		#self.hdulist_header[0][keyword]=str(value)
		#else:
		fits.setval(self.path, keyword, value=str(value))
		return()
	 
	def remove(self, keyword='KEYWORD'):
		if pattern==1: print('pattern 1, use pattern 0 to handle file itself')
		try:
			self.hdulist[0].header.remove(keyword)
			print('removed %s in %s'%(str(keyword), self.name))
		except ValueError:
			print('keyword not found')
			pass
		return()
	def data(self, ext=0):
		if self.pattern==1:
			return(self.hdulist_data[ext])
		else:
			return(self.hdulist[ext].data)

	def save(self, path=None):
		if self.pattern == 1:
			print('pattern 1, use pattern 0 to handle file itself')
		if path==None:
			self.hdulist.writeto(self.path,clobber=True)
		else:
			self.hdulist.writeto(path,clobber=True)
		return()
	def close(self):
		self.hdulist.close()
	def corners(self, ext=1):
		naxis1=self.keyword('NAXIS1', ext=ext)
		naxis2=self.keyword('NAXIS2', ext=ext)
		self.hdulist=fits.open(self.path)
		w=wcs.WCS(header=self.hdulist[ext].header, fobj=self.hdulist)  
		self.hdulist.close()
		points=[[0, 0, naxis1, naxis1],[0, naxis2, naxis2, 0]]
		lon, lat = w.all_pix2world(points[0],points[1], 0)
		c1 = (lon[0], lat[0], ext)
		c2 = (lon[1], lat[1], ext)
		c3 = (lon[2], lat[2], ext)
		c4 = (lon[3], lat[3], ext)
		if self.c1!=None:
			self.other_corners.extend([self.c1[2],[self.c1, self.c2, self.c3, self.c4]])
		self.c1, self.c2, self.c3, self.c4 = c1, c2, c3, c4
		return(c1, c2, c3, c4)
	def add_subtractable_list(self, sub_list=[]):
		self.sub_list=sub_list
		self.sub_list_names=[]
		for el in sub_list:
			self.sub_list_names.append(el.name)

	def extend_subtractable_list(self, element):
		self.sub_list.extend([element])
		self.sub_list_names.extend([element.name])
###
#MyError
###

class MyError(Exception):
	def __init__(self, string=None):
		self.value=string
	def __str__ (self):
		return(self.value)

	
		 
##############
# ROUTINES
##############

###
#angle_of_separation
###
def angle_of_separation(ra1, ra2, dec1, dec2):
	"""
	watch order
	ra, ra, dec, dec
	"""
	dra=math.radians(abs(ra1-ra2))
	ddec=math.radians(abs(dec1-dec2))
	a_o_s=math.degrees(math.acos(math.cos(dra)+math.cos(ddec)-1))
	return(a_o_s)
	
###
#calcPA
###
def calcPA(ra1,dec1,ra2,dec2):
	#print ra1,dec1,ra2,dec2
	deg2rad=0.0174532925199      # math.pi / 180.
	rad2deg=57.2957795131      # 180.0 / math.pi
	#ra1=RaInDeg(ra1)
	#ra2=RaInDeg(ra2)
	#dec1=DecInDeg(dec1)
	#dec2=DecInDeg(dec2)
	dec1rad=dec1*deg2rad
	dec2rad=dec2*deg2rad
	if ra1-ra2>180:
		ra2=ra2+360.0
	if ra1-ra2<-180:
		ra2=ra2-360.0
	dRa = ra2*deg2rad - ra1*deg2rad
	pa_deg = rad2deg*math.atan2(math.sin(dRa),math.cos(dec1rad)*math.sin(dec2rad)/math.cos(dec2rad)-math.sin(dec1rad)*math.cos(dRa));
	return pa_deg

###
#decimal2hexcode
###
def decimal2hexcode(number):
	"""
	converts number into two digit hexnumber 255 --> ff etc 
	"""
	if number>255:
		print('give a smaller number')
		string='ff'
	else:
		string=int(number/16)
		string0=number%16
		if string==10:
			string='a'
		elif string==11:
			string='b'
		elif string==12:
			string='c'
		elif string==13:
			string='d'
		elif string==14:
			string='e'
		elif string==15:
			string='f'
		else:
			string=str(string)
		if string0==10:
			string0='a'
		elif string0==11:
			string0='b'
		elif string0==12:
			string0='c'
		elif string0==13:
			string0='d'
		elif string0==14:
			string0='e'
		elif string0==15:
			string0='f'
		else:
			string0=str(string0)
		string=string+string0
	return (string)

###
#est_obsdate2days
###
def est_obsdate2days(date_obs):
	obs=Time(date_obs, format='iso') 
	obs.format='mjd'
	mjd=obs.value
	
	return mjd

###
#gaussian_function
###
def gaussian_function(x,mu,sigma):
	
	a=1./(math.sqrt(2.*math.pi)*sigma)
	b=-(((x-mu)**2)/(2*sigma**2))
	phi_x=a*math.exp(b)
	
	return(phi_x)

###
#LE_eq
###
def LE_eq(d, alpha, t): #Sugarman paper, alpha in deg
	"""
	d=distace to dust sheet along the line of sight in ly
	alpha= angle of seperation between SN and LE
	t= time since observation in yr
	"""
	alpha_rad=math.radians(alpha) #conversion into rad
	t_fl=float(t) #converison into float
	rho=d*math.sin(alpha_rad) #perpendicular distance to the line of sight from the SN
	h=d*math.cos(alpha_rad) #distance observer, intersection from rho and los(SN)
	
	sum1=(rho**2)/(2.*t_fl) #rho**2/2t
	sum2=(t_fl/2.)#t/2
	z=sum1-sum2 #LEeq, distance SN, intersection
	
	D=z+h
	return (D) #Light Echo Equation

###
#move_im 
###
def move_im(ext, dir, verbose=False):
	"""
	ext is the extension used
	dir the root dir
	move_im('png', './')
	creates dir png/ moves *.png --> png/
	"""
	all_files=os.listdir(dir)
	for filename in all_files:
		if filename.split('.')[-1]==ext:
			if not os.path.isfile(dir+filename): continue
			if verbose: print(filename, '\t--->', ext)
			try:
				os.rename(dir+filename, dir+ext+'/'+filename)
			except OSError:
				if verbose: print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\ncreating directory /%s/\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%(dir+ext+'/'+filename))
				os.mkdir(dir+ext+'/')
				os.rename(dir+filename, dir+ext+'/'+filename)
		else:
			continue
	return ()
	
###
#rainbow_colorcode (c)
###
def rainbow_colorcode(n): 
	"""
	returns list of n color codes
	"""
	position_list=[]
	list_of_colorcodes=[]
	
	if n == 1 : list_of_colorcodes=['#ff0000']
	else: 
		intervall=1./float(n-1)
		print('colorcode intervall is: ', intervall)
		for i in xrange(n):
			pos=i*intervall
			position_list.append(pos)
			if 0.25>=pos>=0:
				greenval=decimal2hexcode(int(1020.*pos))
				list_of_colorcodes.append('#ff'+greenval+'00')
			elif 0.5>=pos>0.25:
				redval=decimal2hexcode(int(255-1020.*(pos-0.25)))
				list_of_colorcodes.append('#'+redval+'ff00')
			elif 0.75>=pos>0.5:
				blueval=decimal2hexcode(int(1020.*(pos-0.5)))
				list_of_colorcodes.append('#00ff'+blueval)
			elif 1>=pos>0.75:
				greenval=decimal2hexcode(int(255-1020.*(pos-0.75)))
				list_of_colorcodes.append('#00'+greenval+'ff')
			else:
				print('error, there is no way this can happen, better quit')
				print(10*'\n')
	print('\n')
	return list_of_colorcodes

###
#sort_images_by_single_keyword
###
def sort_images_by_single_keyword(keyword, dir='./', verbose=False):
	"""
	sorts images by keyword 
	dir is the root dir
	"""
	indir=dir
	images=os.listdir(indir)
	for image in images:
		if not image[-5:]=='.fits':
			if verbose: print('>>> image: \t %s does not end with an .fits, it is no fits file\n'%(image))
			continue
		try:
			hdulist=fits.open(indir+image)
		except IOError:
			if verbose: print('>>> image: \t %s is not a .fits file or has no header\n'%(image))
			continue
		try:
			kw=str(hdulist[0].header[keyword])
		except KeyError:
			if verbose: print('>>> image: \t %s, Keyword not found\n'%(image))
			continue
		outdir=indir+kw+'/'
		try:
			os.rename(indir+image, outdir+image)
		except OSError:
			if verbose: print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\ncreating directory /%s/\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%(kw))
			os.mkdir(outdir)
			os.rename(indir+image, outdir+image)
	return(True)
		
if __name__ =='__main__':
	pass
