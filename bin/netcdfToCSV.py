#!/usr/bin/env python

## \author Bruno Combal
## \date March 2013

from scipy.io import netcdf
from scipy import interpolate
#import matplotlib.pyplot as plt
import numpy
from osgeo import gdal
from osgeo.gdalconst import *
import os
import sys

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: netdfToCSV.py infile outfile'
    print
    exit(errorCode)

def doNcdfToCsv(infile, varname, outfile):
    fh=netcdf.netcdf_file(infile, 'r')
    if fh is None:
        exitMessage("Could not open file {0}. Exit 2.".format(infile), 2)
    print fh.history
    if varname not in fh.variables.keys():
        exitMessage('variable named '+varname+' could not be found. Exit 4.', 4)
    
    yVar=numpy.array(fh.variables[varname][:])
    # read lat
    lat=numpy.array(fh.variables['lat'][:])
    # read lon
    lon=numpy.array(fh.variables['lon'][:])
    

    if len(lat.shape)==2:
        if (lat.shape[0]==yVar.shape[1]) and (lat.shape[1]==yVar.shape[2]):
            points = numpy.array( [numpy.ravel(lon), numpy.ravel(lat)] ).T
        elif (lat.shape[0]==yVar.shape[1]) and (lat.shape[1]==2):
            avgLon = numpy.repeat( numpy.array( [ numpy.ravel( 0.5*(lon[:,0]+lon[:,1]) ) ] ), lat.shape[0], 0)
            avgLat = numpy.repeat( numpy.array( [ numpy.ravel( 0.5*(lat[:,0]+lat[:,1]) ) ] ).T, lon.shape[0], 1)
            points = numpy.array( [numpy.ravel(avgLon), numpy.ravel(avgLat)] ).T
        else:
            exitMessage("Unknown case.", 2)

    elif len(lat.shape)==1:
        newLon = numpy.repeat(  [ lon ] , lat.shape[0], 0)
        newLat = numpy.repeat( [ lat.T ] , lon.shape[0], 1)
        points = numpy.array( [numpy.ravel(newLon), numpy.ravel(newLat)] ).T
        
    else:
        exitMessage('Unknown structure for lat/lon. Exit(3).', 3)

    for iband in range(yVar.shape[0]):
        outfile = open('/data/tmp/tos/{0}_contour.csv'.format(iband),"w")
        thisData=numpy.ravel(yVar[iband,:,:])
        wdata = thisData < 1.e20
        if any(wdata):
            thisData = thisData[wdata]
            thisXX = points[wdata,0]
            thisYY = points[wdata,1]
            for ii in xrange( len(thisData) ):
                outfile.write( '{0}, {1}, {2} \n'.format( thisXX[ii], thisYY[ii],  thisData[ii] ) )
        outfile.close()


if __name__=="__main__":
    
    doNcdfToCsv('/data/cmip5/rcp/rcp8.5/tos/tos_Omon_CMCC-CM_rcp85_r1i1p1_203101-204012.nc','tos','truc')
