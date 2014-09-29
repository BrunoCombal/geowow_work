#!/usr/bin/env python

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

# compute rms of a set of files

import cdms2
from cdms2 import MV
import numpy
import glob
import sys
import os
from os import path
import re

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print "Compute the rms of a set of files"
    print 'Usage: nc_rms.py [-p datapath] -v var -o outfile file*'

    sys.exit(exitCode)
# _______________
def do_rms(infile, path, var, outfile):
    
    # to do: read no-data value, and discard the nodata from computation

    # compute average and max
    average=None
    for ifile in infile:
        thisfile=os.path.join(path, ifile)
        fh=cdms2.open(thisfile,'r')
        
        if average is None:
            average=fh[var][:]
        else:
            average = average + fh[var][:]

        fh.close()
    average = average / len(infile)

    # compute deviations
    deviation=None
    for ifile in infile:
        thisfile=os.path.join(path, ifile)
        fh=cdms2.open(thisfile,'r')

        if deviation is None:
            deviation = (fh[var][:] - average)*(fh[var][:] - average)
        else:
            deviation = deviation + (fh[var][:] - average)*(fh[var][:] - average)
        fh.close()

    deviation = numpy.sqrt( numpy.array(deviation) / float(len(infile)-1))

    fout=cdms2.open(outfile, 'w')
    thisVar=cdms2.createVariable(deviation, typecode='f', id='rms_{0}'.format(var))
    fout.write(thisVar)
    fout.close()

# _______________
if __name__=="__main__":


    infile=[]
    path=None
    outfile=None
    var=None

    ii=1
    while ii<len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outfile=sys.argv[ii]
        elif arg=='-p':
            ii = ii+1
            path=sys.argv[ii]
        elif arg=='-v':
            ii=ii+1
            var=sys.argv[ii]
        else:
            infile.append(arg)
        ii=ii+1

    if len(infile)==0:
        messageOnExit('Input file not defined. Exit(1).',1)
    if outfile is None:
        messageOnExit('Output file not defined. Exit(2).',2)
    if var is None:
        messageOnExit('Undefined variable. Exit(3).',3)

    do_rms(infile, path, var, outfile)
