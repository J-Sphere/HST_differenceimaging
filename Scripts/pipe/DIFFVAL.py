#!/usr/bin/env python
import os, argparse, sys, math
import modules as mod
from modules import FitsFile, sort_images_by_single_keyword, move_im, MyError
import numpy as np

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-dir', type=str, default='./', help='rootdir')
    parser.add_argument('-onlyshow', action='store_true', default=False, help='give to not set any values  but to see what it would be doing')
    parser.add_argument('-mindiff', type=int, default=30.*6., help='minimum difference between two observation in days (default 6 months)')
    parser.add_argument('-reliable_intervall', default=None, type=int, help='variability arround the max and min date [in days]')
    args=parser.parse_args()
    return(args)

def mklists(names, onlyshow=True, r_i=None):
    if not onlyshow: print 'collecting data, FCNUM, DATE-OBS, EXPTIME, from images'
    fcnumlist=[]
    keylist=[]
    for x in names:
        myfile=FitsFile(direc+x)
        try:
            fcnum=myfile.keyword('FCNUM')
            date_obs=myfile.keyword('DATE-OBS')
            ep_time=myfile.keyword('EXPTIME')
        except KeyError:
            print '>>> image \t %s, keyword not found'%(myfile.name)
            continue
        try:
            diffval=myfile.keyword('DIFFVAL')
            myfile.remove('DIFFVAL')
            myfile.save()
        except:
            pass

        if onlyshow: print x, fcnum, date_obs
        if fcnum in keylist:
            idx=keylist.index(fcnum)
            fcnumlist[idx].extend([[ x, mod.est_obsdate2days(date_obs), ep_time ]])
        else:
            keylist.append(fcnum)
            fcnumlist.extend([[ [x, mod.est_obsdate2days(date_obs), ep_time ] ]])
    fcnumlist=[x for (y,x) in sorted(zip(keylist,fcnumlist))]

    keylist=sorted(keylist)
    return(fcnumlist, keylist)

def diffval(direc='./', inlist=[], keylist=[], minval=0, onlyshow=True, r_i=None):
    flags=[]
    for fcnum in xrange(len(inlist)):
        print '\n>>> FCNUM %i'%(fcnum)
        if len(inlist[fcnum])==1:
            print 'can not find subtraction pair, only one item in the list'
            flags.append(False)
            continue
        elif len(inlist[fcnum])==0:
            print 'can not find subtraction pair, no item in the list'
            flags.append(False)
            continue
        else:
            names=[]
            dates=[]
            eptimes=[]
            for el in inlist[fcnum]:
                names.append(el[0])
                dates.append(el[1])
                eptimes.append(el[2])
 
            flag=evaluate_dates(names, dates, eptimes, mindiff=minval, onlyshow=onlyshow, reliable_intervall=r_i)
            flags.append(flag)
    return(flags)

def evaluate_dates(names=[], dates=[], eptimes=[], mindiff=0, reliable_intervall=None, onlyshow=True):
    flag=False
    if  reliable_intervall==None: reliable_intervall=int(math.sqrt(mindiff))
    print 'mindiff and reliable intervall are:\t&i, %i'%(mindiff, reliable_intervall)
    print '%i images'%(len(names))
    print '%i different dates'%(len(list(set(dates))))
    if len(list(set(dates)))==1:
        print 'no subtraction possible'
    else:
        try:
            names=np.array(names)
            dates=np.array(dates)
            eptimes_s=sorted(eptimes)
            eptimes_s.reverse()
            eptimes_s=np.array(eptimes_s)
            eptimes=np.array(eptimes)
            

            max_date=np.max(dates)
            print 'latest observation:\t',max_date 
            min_date=np.min(dates)
            print 'recent observation:\t',min_date 
            if max_date-min_date<mindiff:
                raise MyError('No subtraction possible') 
            a=((dates<max_date+reliable_intervall) & (dates>max_date-reliable_intervall))
            b=((dates<min_date+reliable_intervall) & (dates>min_date-reliable_intervall))


            if len(dates[a])==1: 
                print 'one image from latest date'
                date_max=dates[a][0]
                name_max=names[a][0]
                eptime_max=eptimes[a][0]
            elif len(dates[a])==0:
                print 'no images from the latest observation??  with this number??'
                date_max=None
                name_max=None
                eptime_max=None
            else: 
                print 'multiple max dates'
                for i in eptimes_s:
                    a=((dates<max_date+reliable_intervall) & (dates>max_date-reliable_intervall) & (eptimes==i))
                    if dates[a]!=[]:
                        date_max=dates[a][0]
                        name_max=names[a][0]
                        eptime_max=eptimes[a][0]
                        break
        
            if len(dates[b])==1:
                print 'one min date'
                date_min=dates[b][0]
                name_min=names[b][0]
                eptime_min=eptimes[b][0]
            elif len(dates[b])==0:
                print 'no images from the latest observation??  with this number??'
                date_min=None
                name_min=None
                eptime_min=None
            else:
                print 'multiple min dates'
                for i in eptimes_s:
                    a=((dates<min_date+reliable_intervall) & (dates>min_date-reliable_intervall) & (eptimes==i))
                    if dates[b]!=[]: 
                        date_min=dates[b][0]
                        name_min=names[b][0]
                        eptime_min=eptimes[b][0]
                        break

            print 'Newest Image, with highest EXPTIME %s, obs taken [days since 01/01/2000]: %i, Exposure Time: %.2f'%(name_max, date_max, eptime_max)
            print 'Oldest Image, with highest EXPTIME %s, obs taken [days since 01/01/2000]: %i, Exposure Time: %.2f'%(name_min, date_min, eptime_min)
            if not onlyshow:
                maxfile=FitsFile(direc+name_max)
                minfile=FitsFile(direc+name_min)
                maxfile.set(keyword='DIFFVAL', value=1)
                minfile.set(keyword='DIFFVAL', value=-1)
                print direc+'DIFFVAL_-1/'+minfile.name
                print direc+'DIFFVAL_1/'+maxfile.name


            flag=True
        except MyError as error:
            print error.value
            flag=False

        
    return(flag)


if __name__=='__main__':
    args=get_opt()
    direc=args.dir
    onlyshow=args.onlyshow
    minval=args.mindiff
    r_i=args.reliable_intervall
    filenames=[]
    for x in sorted(os.listdir(direc)):
        if x[-5:]=='.fits':
            filenames.append(x)
    fclist, kyl=mklists(names=filenames, onlyshow=onlyshow)
    flags=diffval(direc=direc, inlist=fclist, keylist=kyl, minval=minval, onlyshow=onlyshow, r_i=r_i)
    print '\n\n'
    Tflags=0
    t=[]
    Fflags=0
    f=[]
    sort_images_by_single_keyword(keyword='DIFFVAL', dir=direc)
    move_im(dir=direc, ext='fits')

    for el in zip(kyl, flags):
        if el[1]: 
            Tflags+=1
            t.append(el[0])
        else: 
            Fflags+=1
            f.append(el[0])

    try:
        images_in_1=float(len(os.listdir(direc+'1')))
    except OSError:
        images_in_1=0.
    try:
        images_in__1=float(len(os.listdir(direc+'-1')))
    except OSError:
        images_in__1=0.
    try:    
        images_in_fits=float(len(os.listdir(direc+'fits')))
    except OSError:
        images_in_fits=0.

    try:
        print 'success rate for FCNUMS is %.2f %%'%(100.*float(Tflags)/float(Tflags+Fflags))
        print 'success rate for images is %.2f %%'%(100.*(images_in_1+images_in_1)/(images_in_1+images_in_1+ images_in_fits))
    except ZeroDivisionError:
        print 'no images processed'
    if t!=[]:
        t=list(np.array(t, dtype=str))
        print 'Field Center that worked:\n'+', '.join(t)
    else:
        print 'no images processsed'
