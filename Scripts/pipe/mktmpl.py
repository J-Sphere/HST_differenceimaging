#!/usr/bin/env python
import argparse, os
import modules as mod
import numpy as np

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-sort', default=False, action='store_true', help='move images in 1 and -1')
    parser.add_argument('-dir',type=str, default='./', help='rootdir')
    args=parser.parse_args()
    return(args)


if __name__=='__main__':
    args=get_opt()
    dir=args.dir
    sort=args.sort
    fitsfiles=[]
    date_obs=[]
    for el in sorted(os.listdir(dir)):
        if el.endswith('.fits'):
            try:
                myfile=mod.FitsFile(dir+el)
                date=mod.est_obsdate2days(myfile.keyword('DATE-OBS'))
                print 'reading %s: \t %s --> %i'%(myfile.name, myfile.keyword('DATE-OBS'), date)
            except KeyError:
                continue
            fitsfiles.append(myfile)
            date_obs.append(date)

    date_obs=np.array(date_obs)
    date_obs_unique=np.unique(date_obs)

    maxd=np.max(date_obs_unique)
    mind=np.min(date_obs_unique)
    print 'newest', maxd
    print 'oldest', mind
    new_files=[]
    new_dates=[]

    old_files=[]
    old_dates=[]

    for date, myfile  in zip(date_obs, fitsfiles):
        if abs(date-mind)>abs(date-maxd):
            print date, myfile.name, '--> new'
            new_dates.append(date)
            new_files.append(myfile)
            myfile.set(keyword='DIFFVAL', value=1)
        elif abs(date-maxd)>=abs(date-mind):
            old_dates.append(date)
            old_files.append(myfile)
            myfile.set(keyword='DIFFVAL', value=-1)

            print date, myfile.name, '--> old'

    print '\n\nnew'
    for el, date in zip(new_files, new_dates):
        print el.name, date
    print '\nold'
    for el, date in zip(old_files, old_dates):
        print el.name, date

    old_dates_unique=np.unique(old_dates)
    new_dates_unique=np.unique(new_dates)
    new_min=np.min(new_dates_unique)
    old_max=np.max(old_dates_unique)
    print 'new images range:\t%i to %i'%(new_min, maxd)
    print 'old images range:\t%i to %i'%(mind, old_max)
    
    if sort: mod.sort_images_by_single_keyword('DIFFVAL', dir=dir)
