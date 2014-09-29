#!/usr/bin/env python
## \author Bruno Combal
## \date January 2013

from scipy.io import netcdf
import matplotlib.pyplot as plt
import numpy
from osgeo import gdal
from osgeo.gdalconst import *

import os
import sys

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

    maxVal=numpy.asarray(yVar[0,:])
    maxDate=numpy.zeros( maxVal.shape, dtype=numpy.int16) # default is date=0 (first date)
    minVal=numpy.asarray(yVar[0,:])
    minDate=numpy.zeros( minVal.shape, dtype=numpy.int16) # default is date=0 (first date)

    if 0==0:
        wtk = (yVar[0,:] != nodata)
        for ii in range(1, orgShape[0], 1):
            if any(wtk):
                yDiff[ii, wtk]=yVar[ii, wtk]-yVar[ii-1, wtk]
                wtest = ( yVar[ii, wtk] > yVar[ii-1, wtk] )
                maxVal[wtk[wtest]] = yVar[ii, wtk[wtest]]
                maxDate[wtk[wtest]] = ii
                
                wtest = ( yVar[ii, wtk] < yVar[ii-1, wtk] ) # because we don't want <= (it would return the last found minimum in a series of equal values)
                minVal[wtk[wtest]] = yVar[ii, wtk[wtest]]
                minDate[wtk[wtest]] = ii
            gdal.TermProgress_nocb((ii-1)/float(orgShape[0]+1))
        gdal.TermProgress_nocb(1)
                
    # draw maps
    # set nodata to None
    mapdata=yVarTmp[0,:,:]
    wnodata = (mapdata == nodata)
    mapdata[wnodata]=None
    fig = plt.figure()
    myFig=fig.add_subplot(111)
    #myFig.imshow(mapdata, origin="lower")
    mapData = yDiff[10,:].ravel().reshape( (orgShape[1],orgShape[2]) )
    mapData[ mapData == nodata ] = None
    myFig.imshow( mapData , origin = "lower" )
    plt.show()

    seriesFig=plt.figure()
    seriesPlt=seriesFig.add_subplot(111)
    series = []
    for x in range(128,137):
        for y in range(72, 82):
            seriesPlt.plot(yDiff.ravel().reshape( orgShape )[1:, y, x] )

    #seriesFig.show()
    #os.system("read")
    
    locations=[ (314, orgShape[1]-33), (130, orgShape[1]-117), (56, orgShape[1]-141) ]
    for ii in locations:
        print ii[0], ii[1]
        print yVarTmp[:, ii[1], ii[0]]
    	
    # reshape them all

    # write to file
    

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
    
