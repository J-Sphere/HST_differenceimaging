#!/usr/bin/env python
import os, argparse
from astropy import wcs
from astropy.io import fits
from matplotlib import pyplot as plt
from modules import FitsFile, rainbow_colorcode
def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-dir',type=str, default=['./'], help='rootdir', nargs='*')
    args=parser.parse_args()
    return(args)


def plot_images(dir='./', color=None):

    plt.figure('ra vs dec')
    files=[]
    for el in sorted(os.listdir(dir)):
        if el.endswith('.fits'):
            files.append(el)
    #ra, dec = [], []
    for image in files:
        try:
            myfile=FitsFile(dir+image)
            try:
                ra_im=FitsFile.keyword(myfile, 'CRVAL1', ext=1)
                dec_im=FitsFile.keyword(myfile, 'CRVAL2', ext=1)
                print ra_im, dec_im
                plt.plot(ra_im, dec_im, 'o', color=color)
            except IndexError:
                pass
            try:
                ra_im=FitsFile.keyword(myfile, 'CRVAL1', ext=4)
                dec_im=FitsFile.keyword(myfile, 'CRVAL2', ext=4)
                print ra_im, dec_im
                plt.plot(ra_im, dec_im, 'o', color=color)
            except IndexError:
                pass
            if True:
                try:
                    naxis1=myfile.keyword('NAXIS1', ext=1)
                    naxis2=myfile.keyword('NAXIS2', ext=1)
                    w=wcs.WCS(header=myfile.hdulist[1].header, fobj=myfile.hdulist)                    
                    points=[[0, 0, naxis1, naxis1, 0],[0, naxis2, naxis2, 0, 0]]
                    lon, lat = w.all_pix2world(points[0],points[1], 1)
                    plt.plot(lon, lat, color=color)
                    w=wcs.WCS(header=myfile.hdulist[4].header, fobj=myfile.hdulist)
                    lon, lat = w.all_pix2world(points[0],points[1], 1)
                    plt.plot(lon, lat, color=color)
                except IndexError:
                    pass
        except KeyError:
            print 'nf'
            pass
    return(True)
if __name__=='__main__':
    args=get_opt()
    direcs=args.dir
    a=0
    colors=rainbow_colorcode(len(direcs))
    for d in direcs:
        try:
            plot_images(dir=d+'/', color=colors[a])
            a+=1
        except OSError:
            pass
    plt.show()
