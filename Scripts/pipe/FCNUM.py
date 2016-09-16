#!/usr/bin/env python
from astropy.io import fits
import os, math, argparse, sys
import numpy as np
from matplotlib import pyplot as plt
from modules import rainbow_colorcode
from modules import angle_of_separation as aos

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-radius', type=float, default=None, help='defines max radius for Fieldcenter search')
    parser.add_argument('-onlyshow', action='store_true', default=False, help='give to not rename files but to see what it would be doing')
    parser.add_argument('-survey', default=None, type=str, help='set surveyname')
    parser.add_argument('-dir', type=str, default='./', help='rootdir')
    parser.add_argument('-f', action='store_true', default=False, help='disable interactivity')

    args=parser.parse_args()
    return(args)

def rename(direc, filenames, scaling=0.04, radius=None, onlyshow=False):
    ra_u=[]
    dec_u=[]
    vis_u=[]
    colorlist=rainbow_colorcode(17)
    if radius!=None: givenrad=True
    else: givenrad=False
    for el in filenames:
        #open file, read header
        print '\n\n>>> %s' %(el)
        hdulist=fits.open(direc+el)
        try:
            CCD_1=hdulist[1].header['CCDCHIP']
        except KeyError:
            print '%s does not have information on CCD in its header (ext 0)' %(el)
            continue
        except IndexError:
            print '%s does not have more tha one ext.' %(el)
            continue        
        if CCD_1==1:
            print 'ext. 1 is UVIS1'
            refrael=hdulist[1].header['CRVAL1'] 
            refdecel=hdulist[1].header['CRVAL2'] 
            NAXIS2=hdulist[1].header['NAXIS2']
            mainccd=1
        elif CCD_1==2:
            print 'ext. 1 is UVIS2 thus using ext 4'
            refrael=hdulist[4].header['CRVAL1'] 
            refdecel=hdulist[4].header['CRVAL2']
            NAXIS2=hdulist[4].header['NAXIS2']
            mainccd=2
        else:
            print '%s is no flc/flt image, CCD=%s' %(el, CCD_1)
            continue
        if not givenrad:
            try:
                radius=scaling*NAXIS2
                print 'search radius is %f'%(radius)
            except:
                radius=0.001
                print 'couldnt find radius, set by default: %f'%(radius)
        else:
            print 'using radius',radius

        target=hdulist[0].header['TARGNAME'] 
        #assign field center number to image
        c=0
        field_nr=None
        vis=str(el[4])+str(el[5])
        vis_u.extend([[refrael, refdecel,int(vis)]])
        for ra, dec in zip(ra_u, dec_u):
            ra_check=np.mean(ra)
            dec_check=np.mean(dec)

            if check(refrael, ra_check, refdecel, dec_check, radius):
                field_nr=c
                ra_u[c].extend([refrael])
                dec_u[c].extend([refdecel])
                break
            else:
                c+=1
        if field_nr is None:
            field_nr=c
            ra_u.extend([[refrael]])
            dec_u.extend([[refdecel]])
        new_field=change_name(target, field_nr)
        #fits.setval(el, 'TARGNAME', value=new_field)
        #fits.setval(el, 'TARGNAME', value='30-DOR')
        #print 'new name for value "TARGNAME" %s is %s' %(el, new_field)

        print 'new name for value "FCNUM" (field nr) for %s is %s' %(el, field_nr)


        #splitting files int to new files (UVIS 1 and UVIS 2 in ext.1)

        #newname1='UVIS{}_'.format(mainccd)+el
        newname1=el
        if onlyshow:
            print 'Without -onlyshow: \n\tsave %s, assigning MAINCCD to %s, FCNUM to %s'%(newname1, mainccd, field_nr)
        else:
            hdulist.writeto(newname1, clobber=True)
            fits.setval(newname1, 'FCNUM', value=field_nr)
            fits.setval(newname1, 'TARGNAME', value=new_field)
            
            fits.setval(newname1, 'MAINCCD', value=str(mainccd))#CCD for image in extension 1 (UVIS)
            print 'save %s, assigning MAINCCD to %s, FCNUM to %s'%(newname1, mainccd, field_nr)
        """
        bu=hdulist

        if mainccd==1: mainccd_2=2
        elif mainccd==2: mainccd_2=1
        else: print 'Not existing mode'

        newname2='UVIS{}_'.format(mainccd_2)+el

        orig_order=np.arange(1, len(hdulist))
        new_order=np.zeros(len(orig_order), dtype=np.int)
        for i in xrange(len(orig_order)):
            new_order[i]=orig_order[i]

        new_order[0]=orig_order[3]
        new_order[1]=orig_order[4]
        new_order[2]=orig_order[5]
        new_order[3]=orig_order[0]
        new_order[4]=orig_order[1]       
        new_order[5]=orig_order[2]    
   
        print 'Original order of extensions\t',orig_order, 'in %s'%(newname1)
        print 'New order of extensions \t',new_order, 'in %s'%(newname2)

        newhdu=fits.HDUList(hdus=[bu[0]])
        for new_data in new_order:
            newhdu.append(hdulist[new_data])

        if onlyshow:
            print 'save %s, assigning MAINCCD to %s, FCNUM to %s'%(newname2, mainccd_2, field_nr)
            newhdu.close()
            hdulist.close()
        else:
            newhdu.writeto(newname2, clobber=True)
            fits.setval(newname2, 'MAINCCD', value=str(mainccd_2)) #CCD for image in extension 1 (UVIS)
            fits.setval(newname2, 'FCNUM', value=field_nr)
            
        """
    print 'assigned %i different fieldcenters'%(len(ra_u))

    #plotting image centers with mathplotlib
    plt.figure(1)
    for ra,dec in zip(ra_u, dec_u):
        plt.plot(ra,dec, 'o', markersize=20)
    plt.show(block=False)
    plt.figure(2)
    for el in vis_u:
        try:
            hexcol=colorlist[int(el[2])]
        except IndexError:
            hexcol=colorlist[-1]
        plt.plot(el[0], el[1],'o',markersize=20, color=hexcol)
    plt.show()
    return ()

def change_name(field, nr):
    name_str=field+str(nr)
    return name_str

def check(ra1, ra2, dec1, dec2, radius):
    myaos=aos(ra1, ra2, dec1, dec2)
    return (myaos<=radius)

if __name__ == '__main__':
    args=get_opt()
    if not args.f:
        if args.survey==None:
            i=str(raw_input('No -survey input, continue? (y/n): \t'))
            if i in ['q', 'exit', 'quit', 'n']:
                sys.exit('exiting...')
            else:
                pass

    scaling=0.04 #arcsec/pix
    scaling/=3600. #deg/pix
    direc=args.dir

    filenames=[]
    for x in os.listdir(direc):
        if x[-5:]=='.fits':
            filenames.append(x)
    filenames=sorted(filenames)
    rename(direc, filenames, scaling, radius=args.radius, onlyshow=args.onlyshow)
