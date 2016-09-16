#!/usr/bin/env python
import argparse, os
import modules as mod

def get_opt():
    parser=argparse.ArgumentParser()
    args=parser.parse_args()
    return(args)


if __name__=='__main__':
    args=get_opt()
    dir='./'
    for image in sorted(os.listdir(dir)):
        if image.endswith('fits'):
            ffile=mod.FitsFile(dir+image)
            date_obs=ffile.keyword('DATE-OBS')
            date_est=mod.est_obsdate2days(date_obs)
            print image, date_obs, ' ---> ', date_est
            ffile.set(keyword='OBS-DNO', value=date_est)
            ffile.close()
