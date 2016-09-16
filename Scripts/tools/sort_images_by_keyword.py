#!/usr/bin/env python 
import argparse, sys
from modules import sort_images_by_single_keyword
def get_opt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-dir', type=str, default='./', help='give root direcory')
    parser.add_argument('-keyword', type=str, default=None)
    args=parser.parse_args()
    return(args)
if __name__=='__main__':
    args=get_opt()
    if args.keyword==None: 
        print('please specify keyword:\n -keyword KEYWORD')
        sys.exit(1)
    sort_images_by_single_keyword(keyword=args.keyword, dir=args.dir)
