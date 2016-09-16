#!/usr/bin/env python
import sys, os, re, math, optparse, types, copy, shutil, glob
import pyfits,scipy,numpy
sys.path.append(os.path.join(os.environ['PIPE_PYTHONSCRIPTS'],'tools'))
from sigmacut import calcaverageclass
from tools import rmfile
from texttable import txttableclass
from astropy.time import Time

class cpfixWFC3class:
    def __init__(self):
        self.verbose=False
        self.data=None
        self.hdr=None
        self.mask=None

    def add_options(self, parser=None, usage=None):
        if parser == None:
            parser = optparse.OptionParser(usage=usage, conflict_handler='resolve')
        parser.add_option('-v', '--verbose', action='count', dest='verbose',default=0)

        parser.add_option('--imformat',default=(16,1.0,32768.0), type='float', nargs=3,
                          help='bitpix, bscale, and bzero of image (default=%default)')
        parser.add_option('--pedestal',default=10.0, type='float', 
                          help='pedestal added to image, necessary if sky is too low and bitpix=16 (default=%default)')
        parser.add_option('-p','--autopedestal', default=False, action='store_true', 
                          help='add a pedestal so that no good pixel values are <=0 (default=%default)')
        parser.add_option('--maxpedestal',default=None, type='float', 
                          help='upper limit on pedestal that is added to the image. This can be used to make sure that --autopedestal does not go wild... (default=%default)')
        parser.add_option('--photcode',default=None, type='int', 
                          help='specificy photcode, which will be written to the fits header (default=%default)')
        parser.add_option('-s','--autosat', default=None, type='float', 
                          help='scale the image so that saturation value=autosat (default=%default)')
        parser.add_option('--zpttype',default='STMAG', type='choice',  choices=('STMAG','ABMAG','VEGAMAG'),
                          help='specify which zeropoint will be stored in the ZPTMAG fitskey (default=%default)')


        return(parser)

    def erode_mask(self,mask,left=1,right=1,up=1,down=1):

        if self.verbose:
            print 'Eroding mask...'

        erodemasktotal = copy.deepcopy(mask)

        for i in xrange(0,left):
            erodemaskleft = scipy.zeros(mask.shape, dtype=mask.dtype)
            #erodemaskleft[:,0:-2]=mask[:,1:-1]
            erodemaskleft[:,i:-i-2]=mask[:,i+1:-i-1]
            erodemasktotal|=erodemaskleft
        for i in xrange(0,right):
            erodemaskright = scipy.zeros(mask.shape, dtype=mask.dtype)
            erodemaskright[:,i+1:-i-1]=mask[:,i:-i-2]
            erodemasktotal|=erodemaskright
        for i in xrange(0,up):
            erodemaskup = scipy.zeros(mask.shape, dtype=mask.dtype)
            erodemaskup[i+1:-i-1,:]=mask[i:-i-2,:]
            erodemasktotal|=erodemaskup
        for i in xrange(0,down):
            erodemaskdown = scipy.zeros(mask.shape, dtype=mask.dtype)
            erodemaskdown[i:-i-2,:]=mask[i+1:-i-1,:]
            erodemasktotal|=erodemaskdown

        #erodemasktotal=scipy.where(erodemasktotal,scipy.uint8(1),scipy.uint8(0))

        return(erodemasktotal)

    def calcsky(self, data, hdr,mask,saturation):
        print 'Calculating SKYADU and SKYSIG...'
        #negmaskarray = scipy.ones(data.shape)
        # 2015-06-23 KWS Force the mask arrays to be uint8
        negmaskarray = scipy.ones(data.shape, dtype=scipy.uint8)
        negmaskarray[mask]=0
        gooddata = data[scipy.where(scipy.logical_and(negmaskarray,data<saturation))]
        mediansky = scipy.median(gooddata)
        print 'median sky:',mediansky
        
        # get the empirical sky noise
        print '111111'
        diff = gooddata - mediansky
        print '111111222'
        diffneg = diff[numpy.where(diff<=0)]
        print '111111333'
        data = numpy.zeros(diffneg.shape[0]*2)
        print '111111444'
        data[:diffneg.shape[0]]=diffneg
        print '111111555'
        data[-diffneg.shape[0]:]=-diffneg
        print '111111666',data.shape
    

        print 'aaaa'
        sigmacut = calcaverageclass()
        print 'bbbb'
        sigmacut.calcaverage_sigmacutloop(data,Nsigma=3.0,fixmean=0.0,verbose=3)
        print sigmacut.__str__()
        skysig_empirical=sigmacut.stdev
        print 'skysig(empirical):',skysig_empirical

        hdr['SKYADU']=mediansky
        hdr['SKYSIG']=skysig_empirical
        print 'SKYADU=%f SKYSIG=%f' % (hdr['SKYADU'],hdr['SKYSIG'])

    def cpfixfile(self, inputfilename,outputfilename,
                  imformat=(16,1.0,32768.0),
                  autosat=None,pedestal=0.0,autopedestal=False,
                  ignorehotpixelflag=True,
                  saterodeleft=1,
                  sateroderight=1,
                  saterodeup=1,
                  saterodedown=1,
                  CRerodeleft=1,
                  CReroderight=1,
                  CRerodeup=1,
                  CRerodedown=1,
                  photcode=None,
                  zpttype4ZPTMAG=None):

        print 'Loading ',inputfilename
        imptr = pyfits.open(inputfilename)
        self.filename = inputfilename

        self.hdr0=imptr[0].header
        if re.search('30-DOR',self.hdr0['TARGNAME']):
            print '30dor images'
            mainccd=self.hdr0['MAINCCD']
            if mainccd=='2': _flag123=True
            elif mainccd=='1': _flag456=True
            else: print mainccd
        else:
            _flag123=False
            _flag546=False

        if re.search('\.CCD2\.',inputfilename) or _flag123:
            UVIS=2
            print 'UVIS %i, \t Image ext 1-3'
            
            self.data = imptr[1].data
            self.hdr = imptr[1].header
            if imptr[1].header['EXTNAME']!='SCI': 
                raise RuntimeError,"BUG!!! extension 1 in %s should be a SCI extension, but is %s!"%(inputfilename,imptr[1].header['EXTNAME'])
            self.err = imptr[2].data
            if imptr[2].header['EXTNAME']!='ERR': 
                raise RuntimeError,"BUG!!! extension 2 in %s should be a ERR extension, but is %s!"%(inputfilename,imptr[2].header['EXTNAME'])
            self.dq = imptr[3].data
            if imptr[3].header['EXTNAME']!='DQ': 
                raise RuntimeError,"BUG!!! extension 3 in %s should be a DQ extension, but is %s!"%(inputfilename,imptr[3].header['EXTNAME'])
        
        elif re.search('\.CCD1\.',inputfilename) or _flag456:
            UVIS=1
            print 'UVIS %i, \t Image ext 4-6'
            self.data = imptr[4].data
            self.hdr = imptr[4].header
            if imptr[4].header['EXTNAME']!='SCI': 
                raise RuntimeError,"BUG!!! extension 4 in %s should be a SCI extension, but is %s!" % (inputfilename,imptr[4].header['EXTNAME'])
            self.err = imptr[5].data
            if imptr[5].header['EXTNAME']!='ERR': 
                raise RuntimeError,"BUG!!! extension 5 in %s should be a ERR extension, but is %s!" % (inputfilename,imptr[5].header['EXTNAME'])
            self.dq = imptr[6].data
            if imptr[6].header['EXTNAME']!='DQ': 
                raise RuntimeError,"BUG!!! extension 6 in %s should be a DQ extension, but is %s!" % (inputfilename,imptr[6].header['EXTNAME'])
        else:
            raise RuntimeError, "data is either in ext 1 or 4"
        CCD=str(UVIS)
        inputrdnoise=numpy.mean([imptr[0].header['READNSEC'],imptr[0].header['READNSED']])
            

        if self.dq is None:
            raise RuntimeError,"BUG!!! filename=%s, does not fit *.A_flc.fits or *.B_flc.fits!" %(inputfilename,imptr[3].header['EXTNAME'])

            
        inputgain = imptr[0].header['CCDGAIN']
        inputsat = 65535

        if self.verbose:
            print 'GAIN: %.2f SATURATION: %.2f RDNOISE: %.1f' % (inputgain,inputsat,inputrdnoise)

        if ignorehotpixelflag:
            # we skip warm and hot pixels.
            # hot pixels: 16
            # warm pixels: 64
            #dq_keepbits = scipy.zeros(self.dq.shape,dtype=scipy.uint16)+scipy.uint16(0xffff & ~(16+64))
            #print type(self.dq)
            self.dq = scipy.bitwise_and(self.dq,scipy.zeros(self.dq.shape,dtype=scipy.uint16)+scipy.uint16(0xffff & ~(16+64)))

        # get the saturation mask
        satmask = self.erode_mask(scipy.where(self.data>=inputsat,scipy.uint16(256),scipy.uint16(0)),
                                  left =saterodeleft,
                                  right=sateroderight,
                                  up   =saterodeup,
                                  down =saterodedown)
        # in dq file: saturation=256
        # if I don't do this step, then some of the extra pixels set to saturation in the dq files are then
        # classified as bad pixels, and set to zero.
        satmask_from_dq = scipy.bitwise_and(self.dq,scipy.zeros(self.dq.shape,dtype=scipy.uint16)+scipy.uint16(256))
        satmask[satmask_from_dq>0]=256


        # erode cosmic rays
        # cosmic rays: 4096
        if CRerodeleft+CReroderight+CRerodeup+CRerodedown>0:
            print 'Eroding CRs'
            dq_CR = scipy.bitwise_and(self.dq,scipy.zeros(self.dq.shape,dtype=scipy.uint16)+scipy.uint16(4096))
            # remove the saturated pixels from the CR file
            dq_CR = scipy.bitwise_and(dq_CR,scipy.where(satmask,scipy.uint16(0),scipy.uint16(4096)))

            dq_CR_eroded = self.erode_mask(dq_CR,
                                           left =CRerodeleft,
                                           right=CReroderight,
                                           up   =CRerodeup,
                                           down =CRerodedown)
            self.dq = scipy.bitwise_or(self.dq,dq_CR_eroded)
            #pyfits.writeto('CR_eroded.fits',dq_CR_eroded,clobber=True)


        masklist=scipy.where(self.dq>0)

        if autopedestal:
            print 'CHECK!!!!'
            sys.exit(0)
            minval = numpy.amin(self.data[scipy.where(self.data>0.0)])
            if self.verbose:
                print 'minval:',minval       
            #pedestal = math.fabs(int(minval/10.0)*10.0)+10.0
            pedestal = pedestal-minval
            if self.verbose:
                print 'Autopedestal: Setting pedestal to ',pedestal
            else:
                print 'no pedestal necessary, pedestal=',pedestal

        if pedestal!=0.0:
            print 'Applying pedestal=%f' % pedestal
            self.data  += pedestal
 
        scalefactor=None
        if autosat!=None:
            #maxpixval = numpy.amax(self.data)
            maxpixval = inputsat
            if maxpixval>65535.0:
                scalefactor = 65535.0/maxpixval
                if self.verbose:
                    print 'max fluxval=%f>65535, thus scaling image by %f' % (maxpixval,scalefactor)
                self.data *= scalefactor
                outputpedestal = pedestal*scalefactor
                outputrdnoise = inputrdnoise*scalefactor
                outputgain = inputgain/scalefactor
                outputsat = min(65535.0,inputsat*scalefactor)
                #print '!!!HACK HACK HACK!!!! increasing effective gain since we know many images went into the template!!'
                #outputgain*=10.0
                if self.verbose:
                    print 'Changing: output GAIN: %.2f SATURATION: %.2f RDNOISE: %.1f PEDESTAL: %.2f' % (outputgain,outputsat,outputrdnoise,outputpedestal)
            else:
                outputgain = inputgain
                outputsat = inputsat+pedestal
                outputrdnoise = inputrdnoise
                outputpedestal=pedestal
        else:
            outputgain = inputgain
            outputsat = inputsat+pedestal
            outputrdnoise = inputrdnoise
            outputpedestal=pedestal

        if int(imformat[0])==16:
            maxval = int(32767*imformat[1]+imformat[2])
            print 'max value for bitpix=%d: %d' % (imformat[0],maxval)
            if outputsat>maxval: 
                print 'Warning: saturation level %f above maximum value %d that can be saved in fits file, setting saturation to %d' %(outputsat,maxval,maxval)
                outputsat = maxval

        if self.verbose:
            print 'OUTPUT GAIN: %.2f SATURATION: %.2f RDNOISE: %.1f' % (outputgain,outputsat,outputrdnoise)

        # copy important keywords
        for keyword in ['TELESCOP','INSTRUME','TARGNAME','PROPOSID',
                        'RA_TARG','DEC_TARG','PROPOSID',
                        'EXPSTART','EXPEND','EXPFLAG','DARKTIME',
                        'OPUS_VER','CAL_VER','OBSTYPE','OBSMODE',
                        'DETECTOR','FILTER','DATE-OBS','TIME-OBS','EXPTIME',
                        'FCNUM']:
            self.hdr[keyword]=self.hdr0[keyword]
        # Set MASKIM=0 and NOISEIM=0. This makes DIFFIM understand that there are no mask and noise images for this image...
        self.hdr['MASKIM']=0
        self.hdr['NOISEIM']=0

        self.hdr['GAIN']=outputgain
        self.hdr['SATURATE']=outputsat
        self.hdr['RDNOISE']=outputrdnoise

        self.hdr['FX_PDSTL']=(outputpedestal,'Pedestal added to image')        
        self.hdr['FX_SCALE']=(scalefactor,'scale applied to image')

        if photcode!=None:
            self.hdr['PHOTCODE']='0x%x' % photcode

        dateobject=Time('%sT%s' % (self.hdr['DATE-OBS'],self.hdr['TIME-OBS']),scale='utc')
        self.hdr['MJD']=dateobject.mjd

        # get the zeropoint
        if zpttype4ZPTMAG!=None:
            t = txttableclass()
            t.configcols(['STMAG','ABMAG','VEGAMAG'],'f','%.3f')
            instrument=self.hdr0['INSTRUME']

            if instrument=='WFC3':
                zptfilename = '%s/UVIS%s.zpt.txt' % (os.environ['PIPE_CONFIGDIR'], CCD)
            elif instrument=='ACS':
                zptfilename = '%s/ACS.WFC.zpt.txt' % (os.environ['PIPE_CONFIGDIR'])
            else:
                sys.exit('Neither WFC3 nor UVIS, check again please')
            t.loadfile(zptfilename)
            zptkeys = t.CUT_inrange('Filter',self.hdr['FILTER'],self.hdr['FILTER'])
            if len(zptkeys)!=1:
                raise RuntimeError,"Could not find filter %s in %s" %(self.hdr['FILTER'],zptfilename)
            for zpttype in ('STMAG','ABMAG','VEGAMAG'):
                self.hdr[zpttype]=t.getentry(zptkeys[0],zpttype)
                if zpttype==zpttype4ZPTMAG:
                    print t.getentry(zptkeys[0],zpttype)
                    print (self.hdr0['EXPTIME'])
                    self.hdr['ZPTMAG']=t.getentry(zptkeys[0],zpttype)+2.5*math.log10(self.hdr0['EXPTIME'])


        self.calcsky(self.data,self.hdr,masklist,outputsat)

        hdu_im = pyfits.PrimaryHDU(self.data,header=self.hdr)
        if int(imformat[0])==16:
            #make sure there are not negative values!
            negdata = scipy.where(self.data<0.0)
            toobigdata = scipy.where(self.data>=outputsat)
            self.data[masklist]=0
            self.data[negdata]=0
            self.data[scipy.where(satmask)]=outputsat
            hdu_im.scale('int16', bscale=imformat[1],bzero=imformat[2])
        elif int(imformat[0])==-32:
            hdu_im.scale('float32')
        else:
            print "ERROR: BITPIX=",imformat[0],"not yet implemented"
            raise RuntimeError
            
        print 'Saving ',outputfilename
        rmfile(outputfilename)
        hdu_im.writeto(outputfilename,clobber=True,output_verify='ignore')
        
        return(0)

           

if __name__ == "__main__":
    cpfixWFC3 = cpfixWFC3class()
    usagestring='USAGE: cpfixWFC3.py inputimage outputimage'
    parser=cpfixWFC3.add_options(usage=usagestring)
    options, args = parser.parse_args()
    
    if len(args)!=2:
        parser.parse_args(args=['--help'])

    (inputfile,outputfile)=args
    cpfixWFC3.verbose=options.verbose
    cpfixWFC3.cpfixfile(inputfile,outputfile,
                        imformat=options.imformat,
                        autosat=options.autosat,
                        pedestal=options.pedestal,
                        autopedestal=options.autopedestal,
                        photcode=options.photcode,
                        zpttype4ZPTMAG=options.zpttype)
   
    print 'SUCCESS cpfixWFC3UVIS.py'
