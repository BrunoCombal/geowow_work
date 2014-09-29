#!/usr/bin/env python

# author: Bruno COMBAL, AMESD
# date: 2010/11/24
# purpose: operation between a scalar and an image


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
	return GDT_Float32
# ______________________________
def Usage(message):
    print
    print message
    print "Usage: myOperatorScalar [-of format] [-co options]* [-nodata nodata]"
    print "                  [-outType outtype] [-epsilon epsilon] [-out_nodata nodatavalue]"
    print "                  -o outfile (-op operator scalar|-op operator scalar1 scalar2) file"
    print "Supported operators:"
    print "-op +\t : adds scalar to the file"
    print "-op -\t : subtracts scalar from the file"
    print "-op '*'\t : multiplies the file by scalar"
    print "-op x\t : same as '*'"
    print "-op /\t : divides the file by scalar"
    print "-op inv\t : divides 1 by the file"
    print "-op linear a b\: a*image + b"
    print "-nodata defines a values that won't be processed."
    print "-epsilon epsilon: approximation of 0 for division (eg: -epsilon 0.0000000001, default is 1.E-6)"
    print "Default output type is Float32"
    print "Available output types are: "
    print "Byte, Int16, UInt16"
    print "Int32, UInt32, Float32, Float64"
    print "and for complex: CInt16, CInt32, CFloat32, CFloat64"
    
    print
    sys.exit(1)

# _____________________________
def op_addition(file, signIn, nodata, outnodata, outTypeIn, scalar, outfile, format, options):
    # sign: -1/1
    sign = 1
    if signIn < 0:
        sign = -1

    fid0 = gdal.Open(file, GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = 'GDT_Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs  = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())

    scalarArray=N.zeros(ns) + scalar

    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
            if nodata is None:
                dataout = data0 + sign * scalarArray
            else:
                wtc = (data0 != nodata)
                dataout = N.zeros(ns)+outnodata
                if wtc.any():
                    dataout[wtc] = data0[wtc] + sign * scalarArray[wtc]

            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl*nb) )

    gdal.TermProgress(1)
# ____________________________
def op_multiplication(file, nodata, outnodata, outTypeIn, scalar, outfile, format, options):

    fid0 = gdal.Open(file, GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = GDT_Float32
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())

    scalarArray=N.zeros(ns)+scalar

    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)

            if nodata is None:
                dataout = data0 * scalarArray
            else:
                wtc = (data0 != nodata) 
                dataout = N.zeros(ns) + outnodata
                if wtc.any():
                    dataout[wtc] = data0[wtc] * scalarArray[wtc]

            dataout.shape=(1, -1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl*nb) )

    gdal.TermProgress(1)

#_______________________________
def op_linear(file, nodata, outnodata, outTypeIn, scalar, scalarb, outfile, format, options):
    fid0 = gdal.Open(file, GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = GDT_Float32
    
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())

    linearA = N.zeros(ns) + scalar
    linearB = N.zeros(ns) + scalarb

    for ib in range(nb):
        for il in range(nl):
            data0 =  N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            if nodata is None:
                dataout = data0 * linearA + linearB
            else:
                wtc = (data0 != nodata)
                dataout = N.zeros(ns) + outnodata
                if wtc.any():
                    dataout[wtc] = data0[wtc] * linearA[wtc] + linearB[wtc]

            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib + 1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl*nb) )

    gdal.TermProgress(1)

# ______________________________
def op_inv(file, nodata, outnodata, outTypeIn, scalar, outfile, format, options):
    fid0 = gdal.Open(file, GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = GDT_Float32
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())

    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
            if nodata is None:
                wtp=(N.abs(data0) > epsilon)
            else:
                wtp=(N.abs(data0) > espilon)*(data0 != nodata)
                
            dataout=N.zeros(ns) + outnodata

            if wtp.any():
                dataout[wtp]=1./data0[wtp]


            dataout.shape=(1,-1)
            outDS.GetRasterBand(ib+1).WriteArray(N.array(dataout),0,il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl*nb) )

    gdal.TermProgress(1)
# _____________________________
if __name__=="__main__":

    outfile = None
    format  = 'GTiff'
    options = []
    file = None
    nodata = None
    outnodata=None
    opType = None
    outType = 'GDT_Float32'
    epsilon=1.0E-6
    scalar=None
    scalarb=None

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]

        if arg == '-of':
            ii = ii + 1
            format = sys.argv[ii]
        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
        elif arg == '-nodata':
            ii = ii + 1
            nodata = float(sys.argv[ii])
        elif arg == '-outType':
            ii = ii + 1
            outType = sys.argv[ii]
        elif arg == '-op':
            ii = ii + 1
            opType = sys.argv[ii]
            ii = ii + 1
            scalar = float(sys.argv[ii])
            if opType == 'linear':
                ii = ii + 1
                scalarb = float(sys.argv[ii])
            
        elif arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        elif arg == '-out_nodata':
            ii = ii + 1
            outnodata=float(sys.argv[ii])
        else :
            file=arg

        ii = ii + 1

    # check the command line
    if opType is None:
        Usage('missing operator')

    if scalar is None:
        Usage('missing scalar value')

    # check the input file exist on the drive
    if (os.path.isfile(file)):
        pass
    else:
        Usage('Input file does not exist: ' + file)

    # define outnodata
    if outnodata is None:
        outnodata = nodata

    # call the operator
    if opType=='+':
        op_addition(file, 1, nodata, outnodata, outType, scalar, outfile, format, options)
    elif opType=='-':
        op_addition(file, -1, nodata, outnodata, outType, scalar, outfile, format, options)
    elif opType=='*':
        op_multiplication(file,  nodata, outnodata, outType, scalar, outfile, format, options)
    elif opType=='x':
        op_multiplication(file,  nodata, outnodata, outType, scalar, outfile, format, options)
    elif opType=='/':
        op_division(file, nodata, outnodata, outType, scalar, outfile, format, options, epsilon)
    elif opType=='inv':
        op_inverse(file, nodata, outnodata, outType, scalar, outfile, format, options)
    elif opType=='linear':
        op_linear(file, nodata, outnodata, outType, scalar, scalarb, outfile, format, options)
    else:
        print "unknown operator."
        sys.exit(1)


