#!/usr/bin/env python

# author: Bruno Combal
# date: March 2013

try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *
try:
    import numpy as N
    N.arrayrange = N.arange
except ImportError:
    import Numeric as N

try:
    from osgeo import gdal_array as gdalnumeric
except ImportError:
    import gdalnumeric
    
import sys
import os.path
import cpimgfile
import operator
import math

# ______________________________
def Usage(message):
    print
    print message
    print 'Usage: \t myFilter.py [-of format] [-co options]* [-nodata nodatavalue]'
    print '\t [-min minvalue] [-max maxvalue] -o outfile file'
    print 'Read input raster file and mask value < minval or > maxval'
    print 'These values are forced to the nodata value (or 0 by default)'
    print 'All bands are processed.'
    print 
    
    sys.exit(1)

# ______________________________
def do_filter(file, nodata, minval, maxval, outformat, options):

    # get infos
    fid = gdal.Open(file, GA_ReadOnly)
    ns = fid.RasterXSize
    nl = fid.RasterYSize
    nb = fid.RasterCount
    dataType=fid.GetRasterBand(1).DataType

    # instantiate outputs
    outDrv=gdal.GetDriverByName(outformat)
    outDs=outDrv.Create(outfile, ns, nl, nb, dataType, options)
    outDs.SetProjection(fid.GetProjection())
    outDs.SetGeoTransform(fid.GetGeoTransform())

    for ib in range(1, nb+1, 1):
        for il in range(nl):
            data = N.ravel(fid.GetRasterBand(ib).ReadAsArray(0, il, ns, 1))
            dataOut = N.zeros(ns)
	    
            # Consider the cases when either minval or maxval are defined, or both
            if minval == None:
                dataOut = N.where( (data<=maxval), data, nodata)
            if maxval == None:
                dataOut = N.where( (data>=minval), data, nodata)
            if maxval != None and minval != None:
                dataOut = N.where(((data <=maxval)&(data>=minval)), data, nodata)
        
            dataOut.shape=(1,-1)
            outDs.GetRasterBand(ib).WriteArray(N.array(dataOut), 0, il)
        gdal.TermProgress( (ib*(ns*nl))/float(nl*ns*nb))

    gdal.TermProgress(1)

    outDs = None 
# ______________________________
if __name__ == "__main__":

    infile = None
    outformat  = 'GTiff'
    minval=None
    maxval=None
    outfile = None
    nodata = None
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

        elif arg == '-min':
            ii = ii + 1
            minval = float(sys.argv[ii])

        elif arg == '-max':
           ii = ii + 1
           maxval = float(sys.argv[ii])

        elif arg == '-nodata':
            ii = ii + 1
            nodata=float(sys.argv[ii])

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
    if ( minval is None and maxval is None):
        Usage('At least one value (min/max) must be defined') 

    do_filter(infile, nodata, minval, maxval, outformat, options)
