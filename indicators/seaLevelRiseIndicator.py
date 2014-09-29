#!/usr/bin/env python
## \author Bruno Combal
## \date January 2013

from scipy.io import netcdf
#import matplotlib.pyplot as plt
import numpy
from osgeo import gdal
from osgeo.gdalconst import *
import os
import sys

def latlon():
    return 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'

def geoTrans(fh):
    # the ncdf arrays are not georeferenced
    # the actual coordinates, or bounding, of each cell is given in ancillary arrays
    # the arrays can be named lon_bnds/lat_bnds (left/right, north/south boundaries)
    # or lat_vertices, lon vertices: corners of each cell
    
    if 'lat_bnds' in fh.variables.keys():
        lat=numpy.array(fh.variables['lat_bnds'][:])
        lon=numpy.array(fh.variables['lon_bnds'][:])
    elif 'lat_vertices' in fh.variables.keys():
        lat=numpy.array(fh.variables['lat_vertices'][:])
        lon=numpy.array(fh.variables['lat_vertices'][:])
        
    latmin=min(lat.ravel())
    latmax=max(lat.ravel())
    psy=(latmin-latmax)/float(len(lat)) # negative pixel size
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

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: seaLevelRiseIndicator.py -o outputfile inputfile varname'
    exit(errorCode)

## \brief save an array, reverting y-axis order
def saveTopdown(data, ns, nl, nb, datatype, outformat, outoptions, outfilename, projection, geotrans):
    outDrv=gdal.GetDriverByName(outformat)
    outDS=outDrv.Create(outfilename, ns, nl, nb, datatype, outoptions)
    outDS.SetProjection(projection)
    outDS.SetGeoTransform(geotrans)
    for ib in range(nb):
        if len(numpy.shape(data))<2:
            thisData=data.reshape(nl, ns)
        else:
            thisData=data[ib]
            thisData=thisData.reshape(nl, ns)
        for il in range(nl):
            outDS.GetRasterBand(ib+1).WriteArray(thisData[-il,:].reshape(1, ns), 0, il)    

## \brief computes difference between current and former month
def computeMonthlyDifference(yVar, orgShape, nodata, cmptMaxDiffToStart=False, cmptMinDiffToStart=False):
    yDiff              = numpy.zeros( yVar.shape, dtype=numpy.float32) + nodata
    yDiffToStart       = numpy.zeros( yVar.shape, dtype=numpy.float32) + nodata
    yDiff[0, :]        = yVar[0,:].copy()
    yDiffToStart[0, :] = yVar[0,:].copy()
    maxDiffToStart     = numpy.zeros( (orgShape[0], orgShape[1]*orgShape[2]), dtype=numpy.float32) - 1.e20
    minDiffToStart     = numpy.zeros( (orgShape[0], orgShape[1]*orgShape[2]), dtype=numpy.float32) + 1.e20
    
    maxVal = numpy.zeros(orgShape[2]*orgShape[1])
    maxVal[:] = yVar[0,:].copy()
    
    minVal = numpy.zeros(orgShape[2]*orgShape[1])
    minVal[:] = yVar[0,:].copy()
    
    maxDate = numpy.zeros( maxVal.shape, dtype=numpy.int16) # default is date=0 (first date)
    minDate = numpy.zeros( minVal.shape, dtype=numpy.int16) # default is date=0 (first date)
    maxExposure = numpy.asarray(yVar[0,:])
    
    wtk = (yVar[0,:] != nodata)
    wtk=wtk.ravel()
    if any(wtk):
        wtkIndex = numpy.asarray(range(orgShape[1]*orgShape[2]))
        wtkIndex = wtkIndex[wtk]
        for ii in range(1, orgShape[0], 1): # for each date but the first one
            yDiff[ ii, wtk ] = yVar[ ii, wtk ] - yVar[ ii-1, wtk ] # compute difference
            yDiffToStart[ ii, wtk ] = yVar[ ii, wtk ] - yVar[ 0, wtk ]
            # get min/max
            if cmptMaxDiffToStart: #largest value observed since the start
                if ii<=1:
                    maxDiffToStart[ 0, : ] = yDiffToStart[ 0, : ]
                    maxDiffToStart[ 1, : ] = yDiffToStart[ 1, : ]
                else:
                    wtest = (yDiffToStart[ ii, wtk ] > maxDiffToStart[ ii-1, wtk ] )
                    maxDiffToStart[ii, :] = maxDiffToStart[ii-1, :] # in any case, transfer values
                    if any(wtest):
                        maxDiffToStart[ ii, wtkIndex[wtest] ] = yDiffToStart[ ii, wtkIndex[wtest] ]

            if cmptMinDiffToStart: #smallest value observed since the start
                if ii<=1:
                    minDiffToStart[ 0, : ] = yDiffToStart[ 0, : ]
                    minDiffToStart[ 1, : ] = yDiffToStart[ 1, : ]
                else:
                    wtest = (yDiffToStart[ ii, wtk ] < minDiffToStart[ ii-1, wtk ] )
                    minDiffToStart[ii, :] = minDiffToStart[ii-1, :] # in any case, transfer values
                    if any(wtest):
                        minDiffToStart[ ii, wtkIndex[wtest] ] = yDiffToStart[ ii, wtkIndex[wtest] ]

            wtest = ( yVar[ ii, wtk ] > yVar[ ii-1, wtk ] )
            if any(wtest):
                maxVal[ wtkIndex[wtest] ] = yVar[ ii, wtkIndex[wtest] ]
                maxDate[ wtkIndex[wtest] ] = ii

            wtest = ( yVar[ ii, wtk ] < yVar[ ii-1, wtk ] )  # because we don't want "<=" operator
                                          #(it would return the last found minimum in a series of equal values)
            if any(wtest):
                minVal[ wtkIndex[ wtest ]]  = yVar[ ii, wtkIndex[ wtest ]]
                minDate[ wtkIndex[ wtest ]] = ii

    return (yDiff, yDiffToStart, maxDiffToStart, minDiffToStart, maxVal, maxDate, minVal, minDate)

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
def computeSeriesByproducts(infile, varname, nodata, maxToStart, minToStart, outfile, format, options):

    startYear=2006
    startMonth=01
    year=startYear
    month=startMonth
    ProgressIndex=0
    ProgressSteps=8
    
    fh = netcdf.netcdf_file(infile, 'r')
    if fh is None:
        exitMessage("Could not open file {0}. Exit 2.".format(infile), 2)
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

    # monthly differences
    print 'computing monthly indicators '
    (yDiff, yDiffToStart, maxDiffToStart, minDiffToStart, maxVal, maxDate, minVal, minDate) = computeMonthlyDifference(yVar, orgShape, nodata, maxToStart, minToStart)
    print 'done.'

    print 'saving estimators '
    saveTopdown(yDiff[0,:], orgShape[2], orgShape[1], 1, GDT_Float32,
		"gtiff", ["compress=lzw"], outfile+"_init_{0}_{1}.tif".format(startYear,startMonth),
		latlon(), geoTrans(fh))
    saveTopdown((minVal, maxVal), orgShape[2], orgShape[1], 2, GDT_Float32,
                'gtiff', ['compress=lzw'], outfile+"_minMax.tif", latlon(), geoTrans(fh))
    saveTopdown((minDate, maxDate), orgShape[2], orgShape[1], 2, GDT_Int16,
                'gtiff', ['compress=lzw'], outfile+"_minMaxDate.tif", latlon(), geoTrans(fh))
    print 'done.'
    
    # save differences
    year = startYear
    month = startMonth
    print 'saving monthly indicators ',
    for itime in range(1, orgShape[0]):
        (year, month) = incrementDate(year, month)
        saveTopdown( yDiff[itime, :], orgShape[2], orgShape[1], 1, GDT_Float32,
                    "gtiff", ["compress=lzw"], outfile+"_delta_{0}_{1}.tif".format(year, month),
                    latlon(), geoTrans(fh))
        saveTopdown( yDiffToStart[itime, :], orgShape[2], orgShape[1], 1, GDT_Float32,
                    "gtiff", ["compress=lzw"], outfile+"_deltaToStart_{0}_{1}.tif".format(year, month),
                    latlon(), geoTrans(fh))
        if maxToStart:
            saveTopdown( maxDiffToStart[itime, :], orgShape[2], orgShape[1], 1, GDT_Float32,
                         "gtiff", ["compress=lzw"], outfile+"_maxDeltaToStart_{0}_{1}.tif".format(year, month),
                         latlon(), geoTrans(fh))
        if minToStart:
            saveTopdown( minDiffToStart[itime, :], orgShape[2], orgShape[1], 1, GDT_Float32,
                         "gtiff", ["compress=lzw"], outfile+"_minDeltaToStart_{0}_{1}.tif".format(year, month),
                         latlon(), geoTrans(fh))
    print 'done.'
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
    maxToStart=True
    minToStart=False

    outputFormat='gtiff'
    outputOptions=[]


    inputFile='/data/cmip5/rcp/rcp8.5/zos/zos_Omon_CanESM2_rcp85_r1i1p1_200601-210012.nc'
    outputFile='/data/tmp/slr/slr.tif'
    outputOptions=['compress=LZW']
    varname='zos'
    nodata=1.e20

    # process command line options and parameters
    ii=1
    while ii<len(sys.argv):
        arg=sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outputFile=sys.argv[ii]
        elif arg == '-maxToStart':
            maxToStart=True
        elif arg == '-minToStart':
            minToStart=True
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

    computeSeriesByproducts(inputFile, varname, nodata, maxToStart, minToStart, outputFile, outputFormat, outputOptions)
    
