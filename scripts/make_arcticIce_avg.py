#!/usr/bin/env python

import numpy
import glob
import sys
import os
from os import path
import re
import string

# compute average of data[[year, val], [year, val], [...]]
def do_avg(data):
    # get list of years
    tmp=None
    for ii in data:
        if tmp is None:
            tmp=[]
        tmp.append(ii[0])

    lstYears=sorted(list(sorted(set(sorted(tmp)))))

    # now, for each year, compute its average
    avgList=None
    for iyear in lstYears:
        avg = None
        N = 0
        for ii in data:
            if iyear == ii[0]:
                if avg is None: avg=0
                avg += ii[1]
                N += 1
        if avgList is None: avgList=[]
        avgList.append([iyear, avg / float(N), N])

    return avgList

# compute models ensemble mean
# ignore years before 2006
def do_model_avg(infile):
    CSV = []
    f = open(infile, 'r')
    for line in f.readlines():
        CSV.append(line.replace('\n','').split(','))
    f.close()

    
    # get list of models
    tmp=None
    for ii in range(len(CSV)):
        if tmp is None: tmp=[]
        tmp.append(CSV[ii][0])

    if tmp is None:
        print 'Could not find any data to process. Exit(1).'
        sys.exit(1)

    modelList=list(sorted(set(sorted(tmp))))

    # for each model, compute its average
    # data[year, area]
    # average done for month = 9
    # ignore dates before 2006
    model_means=None
    for imodels in modelList:
        data = None
        for ii in range(len(CSV)):
            if (CSV[ii][0] == imodels) and (int(CSV[ii][2])==9) and (int(CSV[ii][1])>2005):
                if data is None:
                    data = []
                data.append( [ int(CSV[ii][1]), float(CSV[ii][4]) ] )
        if data is None:
            print 'Could not find any data to process. Exit(2)'
            sys.exit(2)

        avgList = do_avg(data)

        if model_means is None: model_means=[]
        for jj in avgList:
           model_means.append( [imodels, jj[0], jj[1], jj[1]/float(avgList[0][1]) , jj[2] ] )

    # now compute grand ensemble mean
    # get list of years
    tmp=[]
    for ii in model_means:
        tmp.append(ii[1])
        # print ii

    tmp2=sorted(tmp)
#    print list(sorted(set(tmp2)))
    lstYears=list(sorted(set(sorted(tmp))))
    print 'final'
    for iy in lstYears:
        avg = None
        N=0
        for ii in model_means:
            if ii[1] == iy:
                if avg is None:avg=0
                avg += ii[3]
                N += 1
        print iy, avg/float(N), N

# get a csv with models/input ensemble areas
# then compute average per models
# followed by grand average
# ___________________
if __name__=="__main__":

    sitArea='/home/bruno/Documents/tmp/arcticIce.csv'
    outFile='/home/bruno/Documents/tmp/arctic_avg.csv'

    do_model_avg(sitArea)
