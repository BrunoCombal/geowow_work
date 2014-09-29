#!/usr/bin/env python
## \author Bruno Combal
## \date February 2013

## \brief yearly max value in a time series

from itertools import takewhile
import numpy
import scipy.integrate
from scipy.io import netcdf
from osgeo import gdal
from osgeo.gdalconst import *
import os
import sys

def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: max_yearly.py '
    sys.exit(errorCode)

def doMaxYearly(inputFile, outfile, outformat, options):
    fh = gdal.Open(inputFile, GA_ReadOnly)
    if fh is None:
        exitMessage('Could not open file {0}. Exit(1).'.format(inputFile))

    outDrv= gdal.GetDriverByName(outformat)
    outDS = outDrv.Create(outfile, fh.RasterXSize, fh.RasterYSize, fh.RasterCount/12, GDT_Float32, options)

    if outDS is None:
        exitMessage('Could not create output file {0]. Exit(2)'.format(outfile))
    outDS.SetProjection(fh.GetProjection())
    outDS.SetGeoTransform(fh.GetGeoTransform())

    for iyear in range(0, fh.RasterCount, 12):
        # get max from iyear to iyear+12
        dataMaxRef = numpy.ravel(fh.GetRasterBand(1).ReadAsArray(0, 0, fh.RasterXSize, fh.RasterYSize))
        for itime in range(1,12):
            data = numpy.ravel(fh.GetRasterBand(iyear + itime + 1).ReadAsArray(0, 0, fh.RasterXSize, fh.RasterYSize))
            wmax = data > dataMaxRef
            if wmax.any():
                dataMaxRef[wmax] = data[wmax]
            gdal.TermProgress_nocb( (itime + iyear)/float(fh.RasterCount) )

        outDS.GetRasterBand(iyear/12 + 1).WriteArray(dataMaxRef.reshape(fh.RasterYSize, fh.RasterXSize))
    gdal.TermProgress_nocb(1)
                  
##
if __name__=="__main__":
    infile = None
    outfile=None
    outformat='gtiff'
    options=[]

    ii=1
    while ii < len(sys.argv):
        arg=sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outfile = sys.argv[ii]
        elif arg == '-of':
            ii = ii + 1
            outformat=sys.argv[ii]
        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
        else:
            infile=sys.argv[ii]
        ii = ii + 1


    if infile is None:
        exitMessage('Missing an input file name. Exit(1).', 1)
    if outfile is None:
        exitMessage('Missing an output file name. Exit(2).', 2)

    doMaxYearly(infile, outfile, outformat, options)

# EOF
