#!/usr/bin/env python

# author: Bruno Combal
# date: April 2013

from osgeo import gdal
from osgeo.gdalconst import *
gdal.TermProgress = gdal.TermProgress_nocb
import numpy
import sys
import os.path

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: filterDEM.py -o outputfile [-of outputfile] [-co outputOptions] inputfile'
    print
    exit(errorCode)
## 
def doFilterDEM(infile, outfile, outformat, options):
    fid = gdal.Open(infile, GA_ReadOnly)
    ns = fid.RasterXSize
    nl = fid.RasterYSize
    nb = fid.RasterCount
    dataType=fid.GetRasterBand(1).DataType

    listClasses=[1, 3, 5, 7, 9, 10, 12, 20]
    print 'readining data'
    demdata = numpy.ravel(fid.GetRasterBand(1).ReadAsArray(0,0,ns,nl))

    classes=numpy.zeros(ns*nl)+255

    print 'classification'
    for iclass in listClasses[::-1]:
        print 'processing class ',iclass,' '
        wclass = demdata <= iclass
        if wclass.any():
            print ' writing '
            classes[wclass] = iclass
        else:
            print ' X'

    # instantiate outputs
    outDrv=gdal.GetDriverByName(outformat)
    outDs=outDrv.Create(outfile, ns, nl, nb, GDT_Byte, options)
    outDs.SetProjection(fid.GetProjection())
    outDs.SetGeoTransform(fid.GetGeoTransform())
    outDs.GetRasterBand(1).WriteArray(classes.reshape(ns,nl), 0, 0)
##
if __name__=="__main__":
    infile=None
    outfile=None
    outformat='gtiff'
    options=[]

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile=sys.argv[ii]

        elif arg == '-of':
            ii = ii + 1
            outformat = sys.argv[ii]

        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
        else:
            infile = arg
	   	
        ii = ii + 1

    if ( infile is None ):
        Usage('Input file argument missing') 
    if ( outfile is None ):
        Usage('Output file argument missing') 

    print 'running'
    doFilterDEM(infile, outfile, outformat, options)
