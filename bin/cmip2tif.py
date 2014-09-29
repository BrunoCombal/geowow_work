#!/usr/bin/env python

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

import cdms2
from cdms2 import MV
import numpy
import glob
import sys
import os
from os import path
import re
import string
import matplotlib.pyplot as plt

# ________________________________
def do_toTif(infile, var, outfile):
    infile = cdms2.open(infile)

    data = infile[var][:].data[:]

    if os.path.exists(outfile): os.remove(outfile)
    outFH = gdal.Open(outfile,'w')
    
    if infile[var].getGrid() is None:
        # set defaults
        xs=0
        ys=85
        xe=360
        ye=-85
        xstep=0.5
        ystep=0.5

    outFH.write(numpy.fliud(data))

    infile.close()
    outFH.close()
# _________________________________
if __name__=="__main__":
    indir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
    outdir='/data/cmip5/rcp/rcp8.5/tos_ensemble/tif'

    infile=glob.glob(indir+'dhm_*.nc')
    outfile=[os.path.join(outdir, os.path.split[1]) for f in infile]
    print
    #do_toTif(infile, 'dhm', outfile)
