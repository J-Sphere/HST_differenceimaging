#!/usr/bin/env python
import os
from astropy.io import fits
import argparse

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-dir', type=str, default='./', help='give root direcory')
    args=parser.parse_args()
    return(args)


def s_i_b_filter(indir, images):
    for image in images:
        if not image[-5:]=='.fits':
            print '>>> image: \t %s does not end with an .fits, it is no fits file\n'%(image)
            continue
        print image
        try:
            hdulist=fits.open(indir+image)
        except IOError:
            print '>>> image: \t %s is not a .fits file or has no header\n'%(image)
            continue
        try:
            filter_from_image=hdulist[0].header['FILTER']
            fnum=0
        except KeyError:
            filter_from_image=None
        if filter_from_image is None:
            try:
                filter_from_image=hdulist[0].header['FILTER2']
                fnum=2
            except KeyError:
                pass

            if filter_from_image=='CLEAR2L':
                try: 
                    filter_from_image=hdulist[0].header['FILTER1']
                    fnum=1
                except KeyError:
                    pass    
            if filter_from_image=='CLEAR1L':
                print '>>>  image: \t %s does not have a Filter'%(image)
                continue
        if not filter_from_image is None:

            fits.setval(indir+image, 'FILTER', value=filter_from_image)
        else:
            continue

        try:
            print 'using filter %i'%(fnum)
        except:
            print 'image: \t %s does not have a Filter'%(image)
            continue    

        outdir=indir+filter_from_image+'/'
        print 'image: \t %s \tFilter \t %s \t from Filter %i' %(image, filter_from_image, fnum)
        print 'indir: \t %s' %(indir)
        print 'outdir:\t %s' %(outdir)
        print '\n'
        try:
            os.rename(indir+image, outdir+image)
        except OSError:
            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\ncreating directory /%s/\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%(filter_from_image)
            os.mkdir(outdir)
            os.rename(indir+image, outdir+image)
    return(True)


if __name__=='__main__':
    args=get_opt()
    indir=args.dir
    images=os.listdir(indir)
    flag=s_i_b_filter(indir, images)
