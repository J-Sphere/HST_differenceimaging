#!/usr/bin/env python
print '>>modules'
import argparse
import sys, os, re, time
from astropy.io import fits
start=time.time()


#mode Jakob needs ssbrel
"""
astrodrizzle them to clean from crs, this gives a whole lot of s***, one is interested in the _crclean images...
make sure they have header keyword 'FILTER' (eg run sort_images_by_filter.py in jpy)
"""

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-adinput', type=str, default='flc.fits', help='uses all images which end with') 
    parser.add_argument('-VIS', type=str, default=['[0-9][0-9]'], nargs='*', help='give all visits, you want to run, standard is 01-20, example -VIS 01 04 10 15') 
    parser.add_argument('-FILTER', type=str, default=[], nargs='*', help='give all Filters (keyword filter) you want to run, otherwise all available Filters are taken, same syntax as -VIS') #F775W
    parser.add_argument('-mode', type=str, default='Jakob', help='only Jakob exists so far' )
    parser.add_argument('-dir', type=str,default='./', help='give root directory')
    args=parser.parse_args()
    return(args)

def ad(args):
    import drizzlepac
    print 'drizzlepac Version -> ', drizzlepac.__version__, '\n'
    from drizzlepac import astrodrizzle

    VIS=args.VIS
    print '\ninput: \nVIS', VIS
    FILTER=args.FILTER
    print 'FILTER', FILTER, '\n'

    mode=args.mode
    indir=args.dir
    adinput=args.adinput

    start_filter=time.time()
    print '%.2f seconds since start, used for initialization'%(start_filter-start)
    if FILTER==[]:
        print('looking for Filter in all files, this might take some time')
        for el in os.listdir(indir):
            if el.endswith(adinput):
                try:
                    hdulist=fits.open(indir+el) 
                    new_filter=hdulist[0].header['FILTER']
                    if new_filter not in FILTER:
                        FILTER.append(new_filter)
                except:
                    print('could not open file %s'%(indir+el))
            else:
                print('omitting %s')%(indir+el)
    print 'It took %.2f seconds to find all filters'%(time.time()-start_filter)
    if VIS==[]:
        for i in xrange(1,21):
            if i<10: VIS.append('0'+str(i))
            else: VIS.append(str(i))
    elif VIS==['[0-9][0-9]']:
        pass
    print 'FILTER: ', FILTER
    print 'VIS:', VIS


    print '>>running mode ', mode
    if mode=='Jakob':
        for VISno in VIS:
            time_visit=time.time()
            items=[]
            print '\n>>>Running VISIT ', VISno
            for el in os.listdir(indir):
                if re.search(str(VISno), el):
                    items.append(el)
            for FILTERno in FILTER:
                time_filter=time.time()
                final_items=[]
                print '\nRunning FILTER ', FILTERno
                for el in items:
                    try:
                        hdulist=fits.open(indir+el)
                        if hdulist[0].header['FILTER']==FILTERno:
                            print '\t',el
                            final_items.append(el)

                    except:
                        print '\tomitting %s'%(el)
                        continue
                outdir=indir+str(FILTERno)+'_'+str(VISno)+'/'
                for image in final_items:
                    if not VIS==['[0-9][0-9]']:
                        try:
                            os.rename(indir+image, outdir+image)
                        except OSError:
                            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\ncreating directory /%s/\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%(str(FILTERno)+'_'+str(VISno))
                            os.mkdir(outdir)
                            os.rename(indir+image, outdir+image)

                        if not final_items==[]:  astrodrizzle.AstroDrizzle(input=outdir+'*'+adinput, output=outdir+FILTERno+'_'+VISno, clean=False, driz_cr_corr=True)
                    else:
                        if not final_items==[]:  astrodrizzle.AstroDrizzle(input=indir+'*'+adinput, output=indir+FILTERno+'_'+VISno, clean=False, driz_cr_corr=True)
                else: print 'No images for Visit {} and Filter {}'.format(VISno, FILTERno)
                print 'It took %.2f seconds to run astrodrizzle for this filter'%(time.time()-time_filter)
            print 'It took %.2f seconds to run astrodrizzle for this visit'%(time.time()-time_visit)

    else:
        print 'please give an existing mode'

    return(True)

if __name__=='__main__':
    args=get_opt()
    flag=ad(args)
