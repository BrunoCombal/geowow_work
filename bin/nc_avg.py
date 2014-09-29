#!/usr/bin/env python

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

# \brief compute average of a series of nc files


import cdms2
from cdms2 import MV
import numpy
import glob
import sys
import os
from os import path
import re
from scipy import interpolate
import shutil

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print "Compute the average of a set of files"
    print 'Usage: nc_avg.py [-nodata value] [-p datapath] -v var -o outfile file*'

    sys.exit(exitCode)
# ______________
def do_avg(infile, inpath, variable, nodata, outfile):
    # for netcdf3: set flags to 0
    cdms2.setNetcdfShuffleFlag(1)
    cdms2.setNetcdfDeflateFlag(1)
    cdms2.setNetcdfDeflateLevelFlag(3)

    # note that this version will erase data whereever a nodata is found in the series
    avg=None
    nodatamask = None
    for ifile in infile:
        fname = os.path.join(inpath, ifile)
        if not os.path.exists(fname): messageOnExit('file {0} not found on path {1}. Exit(100).'.format(ifile, path), 100)
        thisfile = cdms2.open(fname, 'r')
        
        if avg is None:
            avg = numpy.array(thisfile[variable][:])
            nodatamask = avg >= nodata
        else:
            avg = avg + numpy.array(thisfile[variable][:])
        thisfile.close()

    avg = avg/len(infile)
    if nodatamask.any():
        avg[nodatamask] = nodata
        
    if os.path.exists(outfile): os.remove(outfile)
    outfh = cdms2.open(outfile, 'w')
    outvar=cdms2.createVariable(avg, typecode='f', id=variable, fill_value=nodata )
    outfh.write(outvar)
    outfh.close()
# _______________
if __name__=="__main__":
    inpath=None
    infile=[]
    outfile=None

    variable=None
    nodata=1.e20

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile=sys.argv[ii]
        elif arg == '-v':
            ii = ii +1
            variable = sys.argv[ii]
        elif arg == '-p':
            ii = ii + 1
            inpath = sys.argv[ii]
        elif arg == '-nodata':
            ii= ii +1
            nodata=float(sys.argv[ii])
        else:
            infile.append(sys.argv[ii])
        ii=ii+1
                          
    if len(infile) == 0: messageOnExit('missing input files. Exit(1).',1)
    if outfile is None: messageOnExit('missing and output filename. Exit(2)',2)
    if variable is None: messageOnExit('missing a variable name. Exit(3)', 3)

    do_avg(infile, inpath, variable, nodata, outfile)
