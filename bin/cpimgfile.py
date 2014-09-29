#!/usr/bin/env python

# author: Bruno COMBAL, JRC, European Commission
# date: 14/10/2008
# purpose: copy an image file to gtiff and optionally change format and options

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

# _____________________________
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
	return GDT_Byte


# ______________________________
def Usage(message):
    print message
    print "Usage: cpimgfile.py [-of format] [-co options] -o outfile infile"
    print "Copy an image file to Geotif. Optionally changes the output file format and creation options."
    print
    sys.exit(1)

# ______________________________
def cpimgfile(infile, outfile, format, options):
    
    indataset = gdal.Open( infile, GA_ReadOnly )
    out_driver = gdal.GetDriverByName(format)
    
    datatype = indataset.GetRasterBand(1).DataType
    
    outdataset = out_driver.Create(outfile, \
                                   indataset.RasterXSize, indataset.RasterYSize,\
                                   indataset.RasterCount, datatype, options)
    outdataset.SetProjection(indataset.GetProjection())
    outdataset.SetGeoTransform(indataset.GetGeoTransform())

    for iBand in range(1, indataset.RasterCount + 1):
        inband = indataset.GetRasterBand(iBand)
        outband = outdataset.GetRasterBand(iBand)

        for il in range(inband.YSize):
            scanline = inband.ReadAsArray(0, il, inband.XSize, 1)
            outband.WriteArray(scanline, 0, il)
# ______________________________
if __name__=="__main__":

    outfile = None
    format  = 'GTiff'
    options = []
    file = None

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]

        if arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]

        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
            
        elif arg == '-of':
            ii = ii + 1
            format = sys.argv[ii]

        else :
            file = arg

        ii = ii + 1

    if outfile is None:
        Usage('output filname is missing, use -o option')

    if file is None:
        Usage('input file is missing')

    cpimgfile(file, outfile, format, options)
