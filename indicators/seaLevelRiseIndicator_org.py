#!/usr/bin/env python
## \author Bruno Combal
## \date January 2013

from scipy.io import netcdf
import matplotlib.pyplot as plt
import numpy
from osgeo import gdal
from osgeo.gdalconst import *
import rpy2.robjects as robjects

import os
import sys

def latlon():
    return 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'

def geoTrans(fh):

    lat=numpy.array(fh.variables['lat_bnds'][:])
    latmin=min(lat.ravel())
    latmax=max(lat.ravel())
    
    psy=(latmin-latmax)/float(len(lat)) # negative pixel size
    lon=numpy.array(fh.variables['lon_bnds'][:])
    lonmin=min(lon.ravel())
    lonmax=max(lon.ravel())
    psx=(lonmax-lonmin)/float(len(lon)) # positive pixel size
    return (lonmin, psx, 0, latmax, 0, psy)

def incrementDate(year, month):
    month=month+1
    if month >=13:
        month=1
        year=year+1
    return (year, month)

## Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: seaLevelRiseIndicator.py -o outputfile inputfile varname'
    exit(errorCode)

## Compute differences in a series
# input: varname
# output: varname[i]-varname[i-1], for i in 1...N-1
# output[0]=varname[0]
# The output first image is the first value in the series, the following values are successive difference.
# In consequence, the whole series can be rebuilt by adding successive differences to the first image.
# output[0]=varname[0]
# output[1]=varname[1]-varname[0]
# output[2]=varname[2]-varname[0]
# output[N-1]=varname[N-1]-varname[N-2]
def computeSeriesDiff(infile, varname, nodata, outfile, format, options):

    startYear=2006
    startMonth=01
    year=startYear
    month=startMonth
    fh=netcdf.netcdf_file(infile, 'r')
    
    print fh.history
    # check if the variable exists
    if varname not in fh.variables.keys():
        exitMessage('variable named '+varname+' could not be found. Exit 4.', 4)

    yVarTmp=numpy.array(fh.variables[varname][:])
    orgShape=fh.variables[varname].shape
    if len(orgShape) != 3:
        message='Variable '+varname+' must have only two dimensions, current dimensions are %s. Exit 5.' % (orgShape,)
        exitMessage(message, 5)

    yVar=yVarTmp.ravel().reshape(orgShape[0], -1)
    yDiff=numpy.zeros( yVar.shape, dtype=numpy.float32) + nodata
    yDiff[0,:] = yVar[0,:].copy()

    maxVal  = numpy.asarray(yVar[0,:]) # shape: (time, ny*nx)
    maxDate = numpy.zeros( maxVal.shape, dtype=numpy.int16) # default is date=0 (first date)
    minVal  = numpy.asarray(yVar[0,:])
    minDate = numpy.zeros( minVal.shape, dtype=numpy.int16) # default is date=0 (first date)
    maxExposure = numpy.asarray(yVar[0,:])

    # monthly zos differences
    wtk = (yVar[0,:] != nodata)
    if any(wtk):
        for ii in range(1, orgShape[0], 1): # for each date but the first one
            yDiff[ii, wtk] = yVar[ii, wtk]-yVar[ii-1, wtk] # compute difference
            # get min/max
            wtest = ( yVar[ii, wtk].ravel() > yVar[ii-1, wtk].ravel() ) 
            maxVal[wtk[wtest]] = yVar[ii, wtk[wtest]]
            maxDate[wtk[wtest]] = ii
        
            wtest = ( yVar[ii, wtk].ravel() < yVar[ii-1, wtk].ravel() )  # because we don't want "<=" operator
        #(it would return the last found minimum in a series of equal values)
            minVal[wtk[wtest]]  = yVar[ii, wtk[wtest]]
            minDate[wtk[wtest]] = ii
            gdal.TermProgress_nocb((ii-1)/float(orgShape[0]+1))
    gdal.TermProgress_nocb(1)

    # reshape them all
    yDiff = yDiff.reshape(orgShape)
    # write to file
    # this part will be greatly improved by writting in a netcdf file
    # for the time being, write into tif files
    outDrv = gdal.GetDriverByName('gtiff')
    outDS  = outDrv.Create(outfile+"_init_{0}_{1}.tif".format(startYear, startMonth), orgShape[2], orgShape[1], 1, GDT_Float32, ['compress=lzw'])
    outDS.SetProjection( latlon() )
    outDS.SetGeoTransform( geoTrans(fh) )
    print 'writing reference values'
    for il in range(orgShape[1]): # to write lines upside-down
        toWrite = yDiff[0, -il, :].ravel()
        wtc = (toWrite>=nodata)
        toWrite[wtc] = 0
        outDS.GetRasterBand(1).WriteArray( toWrite.reshape( (1, orgShape[2]) ), 0, il )
        gdal.TermProgress_nocb((il-1)/float(orgShape[1]+1))
    gdal.TermProgress_nocb(1)
    outDS=None

    # save min and max values
    outDrv = gdal.GetDriverByName('gtiff')
    outDS  = outDrv.Create(outfile+"_minMax.tif", orgShape[2], orgShape[1], 2, GDT_Float32, ['compress=lzw'])
    maxVal = maxVal.reshape( (orgShape[1], orgShape[2]) )
    minVal = minVal.reshape( (orgShape[1], orgShape[2]) )
    outDS.SetProjection( latlon() )
    outDS.SetGeoTransform( geoTrans(fh) )
    print 'writing min/max images'
    for il in range( orgShape[1] ):
        outDS.GetRasterBand(1).WriteArray(minVal[-il,:].reshape(1, maxVal.shape[1]), 0, il)
        outDS.GetRasterBand(2).WriteArray(maxVal[-il,:].reshape(1, maxVal.shape[1]), 0, il)
        gdal.TermProgress_nocb((il-1)/float(orgShape[1]+1))
    gdal.TermProgress_nocb(1)

    pressure=numpy.zeros( (orgShape[1], orgShape[2]) )
    (year, month) = incrementDate(year, month)
    for itime in range(1, orgShape[0]):
        outdate  = "_delta_{0}_{1}.tif".format(year,month)
        outDS    = outDrv.Create(outfile+outdate, orgShape[2], orgShape[1], 1, GDT_Float32, ["compress=LZW"])
        outDS.SetProjection(latlon())
        outDS.SetGeoTransform(geoTrans(fh))
        pressDate="_pressure_wrelease_{0}_{1}.tif".format(year, month)
        pressDS  = outDrv.Create(outfile+pressDate,  orgShape[2], orgShape[1], 1, GDT_Int16, ["compress=LZW"])
        pressDS.SetProjection(latlon())
        pressDS.SetGeoTransform(geoTrans(fh))

        #print 'writing ',outfile+outdate
        for il in range(orgShape[1]):
            toWrite = yDiff[itime, -il, :].ravel()
            wtc = (toWrite>=nodata)
            toWrite[wtc] = 0
            outDS.GetRasterBand(1).WriteArray(toWrite.reshape( (1, orgShape[2]) ), 0, il)
            #gdal.TermProgress_nocb((il-1)/float(orgShape[1]+1))
            wp = ( toWrite >= maxVal[-il,:].ravel() ) # if zos > amplitude, increment, else reset to 0
            #wz = ( toWrite <  maxVal[-il,:].ravel() )
            pressure[-il, wp] = pressure[-il, wp] + 1
            #pressure[-il, wz] = 0
            pressDS.GetRasterBand(1).WriteArray(pressure[-il,:].reshape((1,-1)), 0, il)
            pressDS.SetProjection(latlon())
            pressDS.SetGeoTransform(geoTrans(fh))
            
        gdal.TermProgress_nocb( (itime-1)/float(orgShape[0]+1) )
        outDS = None
        (year, month) = incrementDate(year, month)
    gdal.TermProgress_nocb(1)
    
    # close files
    fh.close()

## main
# processes the command line options and parameters
# synopsis: seaLevelRiseIndicator.py -o outputfile [-of outputfileFormat] [-co outputfileFormatOptions]* inputfile varname
if __name__=="__main__":
    inputFile=None
    outputFile=None
    varname=None
    nodata=None

    outputFormat='gtiff'
    outputOptions=[]


    #inputFile='/Users/bruno/Desktop/UNESCO/geowow/showcases/CMIP5/zos_Omon_CanESM2_rcp26_r5i1p1_200601-210012.nc'
    #outputFile='/Users/bruno/Downloads/indicator.tif'
    #outputOptions=['compress=LZW']
    #varname='zos'
    nodata=1.e20

    # process command line options and parameters
    ii=1
    while ii<len(sys.argv):
        arg=sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outputFile=sys.argv[ii]
        else:
            inputFile=sys.argv[ii]
            ii = ii +1
            varname=sys.argv[ii]
        ii=ii+1

    if inputFile is None:
        exitMessage('Please define an inputFile. Exit 1', 1)
    if outputFile is None:
        exitMessage('Please define an outputFile. Exit 2', 2)
    if varname is None:
        exitMessage('Please define the name of the variable to process. Exit 3.', 3)

    computeSeriesDiff(inputFile, varname, nodata, outputFile, outputFormat, outputOptions)
    
