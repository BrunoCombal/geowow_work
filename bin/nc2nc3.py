#!/usr/bin/env python

# \author Bruno Combal, IOC
# \date September 2013

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

# export a variable from a netcdf4 in a single data netcdf3 file
# for processing with nco

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

# _______________
if __name__=="__main__":


    # for netcdf3: set flags to 0
    cdms2.setNetcdfShuffleFlag(0) #1
    cdms2.setNetcdfDeflateFlag(0) #1
    cdms2.setNetcdfDeflateLevelFlag(0) #3

    infile=None
    outfile=None
    variable=None

    ii=1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg=='-o':
            ii = ii + 1
            outfile=sys.argv[ii]
        elif arg=='-v':
            ii=ii+1
            variable=sys.argv[ii]
        else:
            infile=arg

        ii=ii+1

    if infile is None:
        print 'missing an input file'
        sys.exit()
    if outfile is None:
        print 'define the output file with -o'
        sys.exit()
    if variable is None:
        print 'define the variable to export with -v'
        sys.exit()

    thisfile=cdms2.open(infile,'r')
    if os.path.exists(outfile): os.remove(outfile)
    outfile=cdms2.open(outfile,'w')
    # read/write

    thisvar=thisfile[variable]
    outfile.write(thisvar)
    # close files
    outfile.close()
    thisfile.close()
