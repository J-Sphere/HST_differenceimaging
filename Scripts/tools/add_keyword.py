#!/usr/bin/env python
import modules as m
import argparse, re, os

def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-dir', type=str, default='./', help='give root direcory')
    parser.add_argument('-pattern', type=str, default='.fits')
    parser.add_argument('keyword', type=str, default=None, nargs=2, help='NAME VALUE')
    args=parser.parse_args()
    return(args)
if __name__=='__main__':
    args=get_opt()
    name, value = args.keyword
    images=[]
    for image in sorted(os.listdir(args.dir)):
        if re.search(args.pattern, image):
            fitsfile=m.FitsFile(args.dir+image)
            print('>>> %s:\tsetting keyword %s to %s'%(fitsfile.name, name, value))
            m.FitsFile.set(fitsfile, keyword=name, value=value)
            images.append(image)
        
