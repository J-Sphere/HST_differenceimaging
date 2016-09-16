#!/usr/bin/env python
import argparse
import modules as mod
from astropy.io import fits
def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-im1', nargs='*')
    parser.add_argument('-im2', nargs='*')
    args=parser.parse_args()
    return(args)


if __name__=='__main__':
    args=get_opt()
    im1, im2 = args.im1, args.im2
    for ima, imb in zip(im1, im2):
        print ima, '\n', imb
        fits1=mod.FitsFile(ima)
        fits2=mod.FitsFile(imb)
        data1=fits1.hdulist[0].data
        data2=fits2.hdulist[0].data
        print 'data found', fits1.name, fits2.name
        new_data=data2-data1
        print new_data
        new_name='new_'+fits1.name[0:8]+fits2.name[0:8]+'_diff_jh.fits'
        print new_name
        hdu = fits.PrimaryHDU(new_data)
        hdu.writeto(new_name, clobber=True)
        fits1.close()
        fits2.close()
