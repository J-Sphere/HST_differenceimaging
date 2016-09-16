print '>>modules'
import argparse
import sys, os, re, time, drizzlepac
from modules import move_im 
from astropy.io import fits
start=time.time()

#mode Jakob needs ssbdev
"""
tweakreg pictures, allign them to catalogue
make sure they have header keyword 'FILTER' (eg run sort_images_by_filter.py in jpy)
"""
def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-trinput', type=str, default='flc.fits', help='uses all images which end with') 
    parser.add_argument('-VIS', type=str, default=[], nargs='*', help='give all visits, you want to run, standard is 01-20, example -VIS 01 04 10 15') #02, 14
    parser.add_argument('-FILTER', type=str, default=[], nargs='*', help='give all Filters (keyword filter) you want to run, otherwise all available Filters are taken, same syntax as -VIS') #F775W
    parser.add_argument('-mode', type=str, default='Jakob', help='only Jakob exists so far')
    parser.add_argument('-tr_refcat', type=str, default='30dor.0x900b.cat', help='give the catalogue (given in -dir(DONT USE IT DUE TO PROBLEMS EITH "." IN DIRECTORY NAME) or ./), MAKE SURE YOU ARE USING SSBDEV')
    parser.add_argument('-dir', type=str, default='./')
    
    args=parser.parse_args()
    return(args)

def tr_init(args, imdir):
    import drizzlepac
    print 'drizzlepac Version -> ', drizzlepac.__version__, '\n'
    from astropy.io import fits

    VIS=args.VIS
    print '\ninput: \nVIS', VIS
    FILTER=args.FILTER
    print 'FILTER', FILTER, '\n'
    mode=args.mode
    tr_refcat=args.tr_refcat
    cats=[]
    trinput=args.trinput
    if tr_refcat in os.listdir(imdir):
        print 'Using Cataloge %s'%(tr_refcat)
    else:
        for el in os.listdir(imdir):
            if re.search(tr_refcat, imdir):
                cats.append(el)
        if len(cats)!=1:
            print 'please specify catalogue'
            sys.exit(1)        

    start_filter=time.time()
    print '%.2f seconds since start, used for initialization'%(start_filter-start)
    if FILTER==[]:
        print('looking for Filter in all files, this might take some time')
        for el in os.listdir(imdir):
            if el.endswith(trinput):
                try:
                    hdulist=fits.open(imdir+el) 
                    new_filter=hdulist[0].header['FILTER']
                    if new_filter not in FILTER:
                        FILTER.append(new_filter)
                except:
                    print('could not open file %s'%(imdir+el))
            else:
                print('omitting %s')%(imdir+el)
    print 'It took %.2f seconds to find all filters'%(time.time()-start_filter)
    if VIS==[]:
        for i in xrange(1,21):
            if i<10: VIS.append('0'+str(i))
            else: VIS.append(str(i))
    return(VIS, FILTER, tr_refcat, trinput, mode)

def tr_rout(imdir, VIS, FILTER, tr_refcat, trinput, mode):
    print 'FILTER: ', FILTER
    print '>>running mode ', mode

    if mode=='Jakob':
        for VISno in VIS:
            time_visno=time.time()
            items=[]
            print '\n>>>Running VISIT ', VISno
            if VISno=='*':
                a=os.listdir(imdir)
                for el in a:
                    if el.endswith(trinput):
                        items.append(el)
            else:
                for el in os.listdir(imdir):
                    if re.search(str(VISno), el) and el.endswith(trinput):
                        items.append(el)
            print items
            for FILTERno in FILTER:
                time_filter=time.time()
                final_items=[]
                print '\nRunning FILTER ', FILTERno
                for el in items:
                    try:
                        hdulist=fits.open(imdir+el)
                        if hdulist[0].header['FILTER']==FILTERno:
                            print '\t',el
                            final_items.append(el)
                    except KeyError:
                        print '\tomitting %s'%(el)
                        continue
                outdir=imdir+str(FILTERno)+'_'+str(VISno)+'/'
                for image in final_items:
                    try:
                        os.rename(imdir+image, outdir+image)
                    except OSError:
                        print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\ncreating directory /%s/\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'%(str(FILTERno)+'_'+str(VISno))
                        os.mkdir(outdir)
                        os.rename(imdir+image, outdir+image)
                print tr_refcat
                if not final_items==[]: drizzlepac.tweakreg.TweakReg(files=outdir+'*'+trinput, refimage=None, interactive=False, clean=True, updatewcs=True, updatehdr=True, wcsname='NEWCS', refcat=imdir+tr_refcat, rfluxcol=2, rfluxunits='mag', see2dplot=False, residplot='No plot', minobj=1)                
                #if not final_items==[]: drizzlepac.tweakreg.TweakReg(files=imdir+'*'+trinput, refimage=None, interactive=False, clean=True, updatewcs=True, updatehdr=True, wcsname='UPDATEWCS', refcat=imdir+tr_refcat)

                else: print 'No images for Visit {} and Filter {}'.format(VISno, FILTERno)
                print 'It took %.2f seconds to run tweakreg for this filter'%(time.time()-time_filter)
                move_im('png', imdir)
                move_im('coo', imdir)
            print 'It took %.2f seconds to run tweakreg for this visit'%(time.time()-time_visno)

    else:
        print 'please give an existing mode'

    move_im('log', imdir)
    return(True)

if __name__=='__main__':
    args=get_opt()
    imdir=args.dir
    VIS, FILTER, tr_refcat, trinput, mode=tr_init(args, imdir)
    flag=tr_rout(imdir, VIS, FILTER, tr_refcat, trinput, mode)
