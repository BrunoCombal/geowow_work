#!/usr/bin/env python

## \author Bruno Combal
## \date February 2013
## read a time series (no a netcdf), detect constant values
## if none is set to nodata, set all constant series to nodata

from Scientific.IO.NetCDF import NetCDFFile
import itertools
import numpy
from osgeo import gdal
from osgeo.gdalconst import *
import os
import sys

def ParseType(type):	
    if type == 'Byte':
        return GDT_Byte
    elif type == 'Int16':
        return GDT_Int16
    elif type == 'UInt16':
        return GDT_UInt16
    elif type == 'Int32':
        return GDT_Int32
    elif type == 'UInt32':
        return GDT_UInt32
    elif type == 'Float32':
        return GDT_Float32
    elif type == 'Float64':
        return GDT_Float64
    elif type == 'CInt16':
        return GDT_CInt16
    elif type == 'CInt32':
        return GDT_CInt32
    elif type == 'CFloat32':
        return GDT_CFloat32
    elif type == 'CFloat64':
        return GDT_CFloat64
    else:
        return GDT_Float32

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: setNoDataInSeries.py -o outfile [-of outformat] [-co formatoption]* [-nodata nodatavalue] infile'
    print '-nodata: default is 1.e20'
    print
    exit(errorCode)

##
def  doSetNoDataInSeries(infile, nodata, variable, outfile):
    fileH = NetCDFFile(infile, mode="r")

    if fileH is None:
        exitMessage('Could not open file {0}. Exit(1).'.format(infile), 1)

    data = fileH.variables[variable][:]
    if len(data.shape)!=3:
        exitMessage('3d data needed for {0}. Exit(2).'.format(variable), 2)
    # if nodata are found on the first image, return
    wnodata = (data[0,:,:] == nodata)
    if wnodata.any():
        print 'No data already set. Return(0)'
        return(0)

    common = numpy.ravel(numpy.ones((data.shape[1], data.shape[2]), dtype=numpy.bool))

    for iband in range(1, data.shape[0]):
        wnequal = data[iband-1,:,:].ravel() == data[iband,:,:].ravel()
        if wnequal.any():
            common[wnequal]=False

        gdal.TermProgress_nocb(iband/float(data.shape[0]))
    common = numpy.reshape(common, (data.shape[1], data.shape[2]))
    data[common] = nodata

    # save result
    outfile = NetCDFFile(outfile, mode='w')
    # build a list of variables without the processed variable
    listOfVariables = list( itertools.ifilter( lamdba x:x!=variable , fileH.variables.keys() ) )
    for ivar in listOfVariables:
        
    
    varToWrite = fileH.createVariable('new_{0}'.format(variable), 'f', fileH.variables[variable].dimensions )
    varToWrite[:] = data

    fileH.close()

    gdal.TermProgress_nocb(1)

## Assume NETCDF
def doSetNoDataInSeriesOld(infile, nodata, outfile, outformat, options):
    fileH = gdal.Open(infile, GA_ReadOnly)
    if fileH is None:
        exitMessage('Could not open file {0}. Exit(1).'.format(infile), 1)
    
    # does not data exist?
    data = numpy.ravel( fileH.GetRasterBand(1).ReadAsArray())
    wnodata = (data==nodata)
    if wnodata.any():
        print 'No data already set. Return(0)'
        return(0)

    common = numpy.ones(data.shape)
    for iband in range(1, fileH.RasterCount):
        newdata = numpy.ravel(fileH.GetRasterBand(iband + 1).ReadAsArray())
        wnequal = data!=newdata
        common[wnequal] = 0
        gdal.TermProgress_nocb( (iband+1)/float( 2*fileH.RasterCount ) )

    # is there any constant time series?
    if common.any():
        outDrv = gdal.GetDriverByName(outformat)
        outDS = outDrv.Create(outfile, fileH.RasterXSize, fileH.RasterYSize, fileH.RasterCount, fileH.GetRasterBand(1).GetRasterDataType, options)
        outDS.SetProjection( fileH.GetProjection() )
        outDS.SetGeoTransform( fileH.GetGeoTransform() )
        #then set these time series to nodata
        for iband in range(fileH.RasterCount):
            data = numpy.ravel(fileH.GetRasterBand(iband + 1).ReadAsArray(0, 0, fileH.RasterXSize, fileH.RasterYSize))
            data[common] = nodata
            outDS.GetRasterBand( iband + 1 ).WriteArray( data.reshape(fileH.RasterYSize, fileH.RasterXSize), 0, 0)
            gdal.TermProgress_nocb( (iband+1+fileH.RasterCount) / float( 2*fileH.RasterCount ) )

    gdal.TermProgress_nocb(1)

##
if __name__=="__main__":

    infile = None
    variable = None
    nodata = 1.e20
    outfile = None
    outformat='hfa'
    options=[]
    
    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
    
        if arg == '-v':
            ii = ii + 1
            variable = sys.argv[ii]
        elif arg=='-o':
            ii = ii +1
            outfile = sys.argv[ii]
        elif arg == '-nodata':
            ii = ii + 1
            nodata = float(sys.argv[ii])
            
        else:
            infile=sys.argv[ii]
        ii = ii + 1

        
    if infile is None:
        exitMessage('Input file not defined. Exit(10).', 10)

    if variable is None:
        exitMessage('netcdf variable not defined. Exit(11).', 11)

    if outfile is None:
        exitMessage('Missing an output file name. Exit(12).', 12)

    doSetNoDataInSeries(infile, nodata, variable, outfile)
    

# end of code
