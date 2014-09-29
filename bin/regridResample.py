#!/usr/bin/env python

## \author Bruno Combal
## \date February 2013

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
    print 'Usage: regrid.py -o outputfile -v varname [-nodata nodata=1.e20] [-of outformat=HFA] [-co options]* inputfile'
    print
    exit(errorCode)

def latlon():
    return 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'

## \brief resample the data into a regular grid
def doRegrid(infile, varname, nodata, outfile, outformat, options, xRange, yRange, gt):
    # read infile
    fh=netcdf.netcdf_file(infile, 'r')
    if fh is None:
        exitMessage("Could not open file {0}. Exit 2.".format(infile), 2)
    print fh.history

    # read variable
    if varname not in fh.variables.keys():
        exitMessage('variable named '+varname+' could not be found. Exit 4.', 4)
    
    yVar=numpy.array(fh.variables[varname][:])
    # read lat
    lat=numpy.array(fh.variables['lat'][:])
    # read lon
    lon=numpy.array(fh.variables['lon'][:])

    # if arrays are 2-d, 1 lat/lon per pixel
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

    xi=[]
    for ix in xRange:
        for iy in yRange:
            xi.append([ix, iy])

    # instantiate a file
    outDrv = gdal.GetDriverByName(outformat)
    outDS = outDrv.Create(outfile, len(xRange), len(yRange), yVar.shape[0], GDT_Float32, options)
    outDS.SetProjection(latlon())
    outDS.SetGeoTransform(gt)

    # interpolate
    for iband in range(yVar.shape[0]):
        yInt = interpolate.griddata(points, yVar[iband, :, :].ravel(), xi, method='linear', fill_value=nodata)
        yIntToWrite = yInt.reshape(len(xRange), len(yRange)).copy()
        # save to file
        outDS.GetRasterBand( iband + 1 ).WriteArray( numpy.flipud(yIntToWrite.T), 0, 0)
        gdal.TermProgress_nocb( (iband+1)/float(yVar.shape[0]) )

    gdal.TermProgress_nocb(1)

##
if __name__=="__main__":

    infile = None
    outfile = None
    variable = None
    nodata = 1.e20
    outformat='hfa'
    options=[]
    
    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]

        elif arg== '-v':
            ii = ii + 1
            variable = sys.argv[ii]

        elif arg == '-nodata':
            ii = ii + 1
            nodata = float(sys.argv[ii])
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
        exitMessage('Input file not defined. Exit(10).', 10)

    if outfile is None:
        exitMessage('Output file not defined. Exit(11).', 11)

    if variable is None:
        exitMessage('Define a variable name (zos, ph, o2min, ...). Exit(12).', 12)

    xstart=0
    xend=360
    xstep=0.5
    ystart=-90
    yend=90
    ystep=0.5

    gt = (xstart, xstep, 0, yend, 0, -ystep)

    if not os.path.exists(infile):
        exitMessage('File {0} does not exist. Exit(1).'.format(infile), 1)


    doRegrid(infile, variable, nodata, outfile, outformat, options, numpy.arange(xstart, xend, xstep), numpy.arange(ystart, yend, ystep), gt)
