#!/usr/bin/env python
import argparse, os, math, sys
import modules as mod
import numpy as np
def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-mindiff', default=180., type=float, help=' Minimum days between observations')
    parser.add_argument('-scaling', default=0.04, type=float, help='arcsec/pix, WFC3 has 0.04, ACS 0.13' )

    args=parser.parse_args()
    return(args)

def test_for_intersections(fits1, fits2):
    ret=False

    a1, a2, a3, a4 = fits1.corners()
    b1, b2, b3, b4 = fits2.corners()

    sides1 = [(a1,a2),(a2,a3),(a3,a4),(a4,a1)]
    sides2 = [(b1,b2),(b2,b3),(b3,b4),(b4,b1)]
    
    for side1 in sides1:
        for side2 in sides2:
            if test_sides_for_intersections(side1[0], side1[1], side2[0], side2[1]):
                ret=True
                return(ret)
            else:
                continue
            
    return(False)

def test_sides_for_intersections(P1=(0.,0.), P2=(2.,2.), Q1=(2.,0.), Q2=(0.,2.)):
    
    a, b, c, d = P1[0], P1[1], P2[0]-P1[0], P2[1]-P1[1]
    e, f, g, h = Q1[0], Q1[1], Q2[0]-Q1[0], Q2[1]-Q1[1]
    up = f*c+d*a-c*b-d*e
    down = d*g-h*c
    if down==0: return False
    m = up/down
    up = g*f+h*a-e*h-g*b
    down = d*g-e*h
    if down==0: return False
    n=up/down
    if m>0 and n>0 and m<1 and n<1: return(True)
    else: return False

def compare_files(fits1, fits2, scaling=None, mindiff=None):
    val=False
    ra1, dec1 = fits1.keyword('CRVAL1', ext=1), fits1.keyword('CRVAL2', ext=1)
    ra2, dec2 = fits2.keyword('CRVAL1', ext=1), fits2.keyword('CRVAL2', ext=1)
    center1 = (ra1, dec1)
    center2 = (ra2, dec2)
    radius=mod.angle_of_separation(ra1, ra2, dec1, dec2)
    
    axis1, axis2 = float(fits1.keyword('NAXIS1', ext=1)), float(fits1.keyword('NAXIS2', ext=1))
    
    smallax = min([axis1, axis2])
    
    scaling*=(1./3600.)
    smallval = (smallax)*scaling
    bigval = math.hypot(axis1, axis2)*scaling
    print 'smallval %f, \tbigval %f, \tmindiff %f'%(smallval, bigval, mindiff)

    if radius<smallval: val=True
    elif radius>bigval: pass
    else:
        val=test_for_intersections(fits1, fits2)
    if val: 
        date_obs1 = fits1.keyword('DATE-OBS')
        date_obs2 = fits2.keyword('DATE-OBS')
        date1 = mod.est_obsdate2days(date_obs1)
        date2 = mod.est_obsdate2days(date_obs2)
        if abs(date2-date1)<mindiff:
            val=False
    return(val)

if __name__=='__main__':
    args=get_opt()
    dir='./'
    if args.scaling==0.04:
        print 'ARE YOU SURE YOU ARE USING THE RIGHT SCALING? WFC=0.04 (default), ACS=0.13? (y/n)'
        a=raw_input()
        if a=='y':
            pass
        else:
            sys.exit('give scaling')
    fitsfiles1=[]
    for el in sorted(os.listdir(dir)):
        if el.endswith('.fits'):
            
            myfile=mod.FitsFile(dir+el, pattern=1)
            print 'reading %s'%(myfile.name)
            mod.FitsFile.corners(myfile, ext=1)
            myfile.add_subtractable_list(sub_list=[])
            fitsfiles1.append(myfile)

    print '\nreading done\n'
    for file1 in fitsfiles1:
        print '\n>>> Comparing to file %s'%(file1)
        for file2 in fitsfiles1:
            if file2.name == file1.name: continue
            boolval = compare_files(file1, file2, scaling=args.scaling, mindiff=args.mindiff)
            if boolval:
                print file1.name, 'and ', file2.name,'match!: compare_files=', boolval
                file2.extend_subtractable_list(file1)
    
    print '\n'
    for file1 in fitsfiles1:
        print file1.name, '\t:\t',file1.sub_list_names,'\n', file1.sub_list
        if file1.sub_list_names==[]:
            outpath=file1.path.split('/')[0:-1]
            new_path='/'.join(outpath)
            new_path+='/useless/'
            try:
                os.rename(file1.path, new_path+file1.name)
                file1.path=new_path+file1.name
            except OSError:
                os.mkdir(new_path)
                os.rename(file1.path, new_path+file1.name)
                file1.path=new_path+file1.name

    field_list_names=[]
    field_list=[]
    field_nr=0
    print '\n'
    for file1 in fitsfiles1:
        if file1.sub_list_names==[]: continue
        q=False # is the file already present

        for field_names in field_list_names:
            if file1.name in field_names:
                q=True
        if q: continue
        print 'starting new field with %s (is not present in any field). Adding...'%(file1.name)

        field=[file1]
        field_names=[file1.name]
        
        new_elements=[file1]
        new_elements_names=[file1.name]

        while new_elements!=[]: 
            new_elements=[]
            new_elements_names=[]

            for element, element_name in zip(field, field_names):
                for next_file, next_file_name in zip(element.sub_list, element.sub_list_names):
                    if (next_file_name in field_names) or (next_file in field): 
                        continue
                    else: 
                        new_elements.append(next_file)
                        new_elements_names.append(next_file.name)
                        field.append(next_file)
                        field_names.append(next_file.name)
            print len(new_elements)
        print '\tcreated field %i:'%(field_nr), field_names
        for fits in field:
            fits.set(keyword='FCNUM', value=field_nr)    
        field_list.extend([field])
        field_list_names.extend([field_names])
        field_nr+=1
    print '\n%i field(s) found'%(field_nr)
    c=0
    for field, field_names in zip(field_list, field_list_names):
        if len(field)>3: print c, ':\t', field_names[0:2], '...'
        else: print c, ':\t', field_names
        c+=1
        
 
