#!/usr/bin/env python

# author: Bruno COMBAL, JRC, European Commission
# date: 2009/03/20
# simulate operator. The number of operand depend on the operator
# 
# Version history
# 1.0     2009/03/20    first version
# 1.1     2010/12/10    adding handling of out_nodata for ndvi


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
    print "Usage: myOperator [-of format] [-co options]*"
    print "                  [-nodata nodata] [-out_nodata out_nodata]"
    print "                  [-outType outtype] [-epsilon epsilon]"
    print "                  -o outfile -op operator file*"
    print "The number of files depends on the operator."
    print "Supported operators:"
    print "-op +\t addition, requires 2 files"
    print "-op -\t subtraction, requires 2 files"
    print "-op x\t multiplication, requires 2 files"
    print "-op /\t division, requires 2 files"
    print "-op -/\t (a-b)/c, required 3 files"
    print "-op ndvi (b-a)/(b+a), requires 2 files"
    print "-nodata defines a values that won't be processed."
    print "-out_nodata nodata value on output."
    print "-epsilon epsilon: approximation of 0 for division (eg: -epsilon 0.0000000001, default is 1.E-6)"
    print "Default output type is Float32"
    print "All internal operations are done on float data, only the output is cast to the output type requested by the user."
    print "Available output types are: "
    print "Byte, Int16, UInt16"
    print "Int32, UInt32, Float32, Float64"
    print "and for complex: CInt16, CInt32, CFloat32, CFloat64"
    print "Types Byte, Int16, UInt16, Int32, UInt32 result in rounding internal computation to the nearest integer. Values exceeding data type boundaries will receive the boundary values, e.g.: internal computation give 265.03 if you decided to code the result on a byte the pixel will be coded 255."
    print
    sys.exit(1)

# _____________________________
def op_addition(files, signIn, nodata, out_nodata, outTypeIn, linear, outfile, format, options):
    # sign: -1/1
    sign = 1
    if signIn < 0:
        sign = -1

    fid0 = gdal.Open(files[0], GA_ReadOnly)
    fid1 = gdal.Open(files[1], GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs  = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())

    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
            data1 = N.ravel(fid1.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)

            if nodata is None:
                dataout = data0 + sign * data1
            else:

                if out_nodata is None:
                    dataout = N.zeros(ns)
                else:
                    dataout = N.zeros(ns) + out_nodata

                wtc = (data0 != nodata) * (data1 != nodata)
                if wtc.any():
                    dataout[wtc] = data0[wtc] + sign * data1[wtc]

            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl) )

    gdal.TermProgress(1)
# ____________________________
def op_relativeDiff(files, nodata, out_nodata, outTypeIn, linear, outfile, format, options):

    fid0 = gdal.Open(files[0], GA_ReadOnly)
    fid1 = gdal.Open(files[1], GA_ReadOnly)
    fid2 = gdal.Open(files[2], GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    # instantiate output
    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    if out_nodata is None:
        out_nodata=nodata

    outDrv = gdal.GetDriverByName(format)
    outDs  = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())

    # compute relative difference, consider only 1 band
    ib = 0
    for il in range(nl):
        data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
        data1 = N.ravel(fid1.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
        data2 = N.ravel(fid2.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)

        # compute (data0-data1)/data2
        dataout = N.zeros(ns)
        if nodata is None:
            wnzero = (data2 != 0)
            if wnzero.any():
                dataout[wnzero] = (data0[wnzero]-data1[wnzero])/data2[wnzero]
        else:
            wtc = (data2 != 0) * (data0 != nodata) * (data1 != nodata)
            if wtc.any():
                dataout[wtc] = (data0[wtc] - data1[wtc])/data2[wtc]

            wtz = (data0 == nodata) + (data1 == nodata)
            if wtz.any():
                dataout[wtz] = out_nodata

        dataout.shape=(1,-1)
        outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

        gdal.TermProgress(il/float(nl))

    gdal.TermProgress(1)
# ____________________________
def op_ndvi(files, nodata, out_nodata, outTypeIn, linear, outfile, format, options):

    fidRed = gdal.Open(files[0], GA_ReadOnly)
    fidNir = gdal.Open(files[1], GA_ReadOnly)
    ns = fidRed.RasterXSize
    nl = fidRed.RasterYSize
    nb = fidRed.RasterCount

    epsilon=0.00001

    # check nodata
    if out_nodata is None:
        if nodata is None:
            out_nodata=0
        else:
            out_nodata=nodata

    # instantiate output
    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs  = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fidRed.GetProjection())
    outDs.SetGeoTransform(fidRed.GetGeoTransform())

   # compute ndvi, consider only 1st band per image
    ib = 0
    for il in range(nl):
        dataRed = N.ravel(fidRed.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)
        dataNir = N.ravel(fidNir.GetRasterBand(ib+1).ReadAsArray(0, il, ns, 1)).astype(float)

        # compute (dataNir-dataRed)/(dataNir+dataRed)
        dataout = N.zeros(ns) + out_nodata
        if nodata is None:
            wnzero = ( (dataNir+dataRed) != 0)
            if wnzero.any():
                dataout[wnzero] = (dataNir[wnzero]-dataRed[wnzero])/(dataRed[wnzero]+dataNir[wnzero])
        else:
            wtc = ( (dataNir+dataRed) != 0 ) * (dataRed != nodata) * (dataNir != nodata) * (abs(dataNir - dataRed) > epsilon)
            if wtc.any():
                dataout[wtc] = (dataNir[wtc] - dataRed[wtc])/(dataNir[wtc] + dataRed[wtc])

        dataout.shape=(1,-1)
        outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

        gdal.TermProgress(il/float(nl))

    gdal.TermProgress(1)

# _____________________________
def op_multiplication(files, nodata, outTypeIn, linear, outfile, format, options):

    fid0 = gdal.Open(files[0], GA_ReadOnly)
    fid1 = gdal.Open(files[1], GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())


    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            data1 = N.ravel(fid1.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)

            if nodata is None:
                dataout = data0 * data1
            else:
                wtc = (data0 != nodata) * (data1 != nodata)
                dataout=N.zeros(ns)
                if wtc.any():
                    dataout[wtc] = data0[wtc] * data1[wtc]

            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)
            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl) )

    gdal.TermProgress(1)

# _____________________________
def op_division(files, nodata, outTypeIn, linear, outfile, format, options, epsilon):

    fid0 = gdal.Open(files[0], GA_ReadOnly)
    fid1 = gdal.Open(files[1], GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())
    
    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            data1 = N.ravel(fid1.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            
            # compute data0/data1
            if nodata is None:
                wtc = (N.abs(data1) > epsilon)
            else:
                wtc = (data0 != nodata) * (data1 != nodata) * (N.abs(data1) > epsilon)

            dataout=N.zeros(ns)
            if wtc.any():
                dataout[wtc] = data0[wtc] / data1[wtc]
			
            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl) )

    gdal.TermProgress(1)
#_____________________________
def op_percent(files, nodata, outTypeIn, linear, outfile, format, options, epsilon):

    fid0 = gdal.Open(files[0], GA_ReadOnly)
    fid1 = gdal.Open(files[1], GA_ReadOnly)
    ns = fid0.RasterXSize
    nl = fid0.RasterYSize
    nb = fid0.RasterCount

    outType = outTypeIn
    if outTypeIn is None:
        outType = 'Float32'
    outDrv = gdal.GetDriverByName(format)
    outDs = outDrv.Create(outfile, ns, nl, nb, ParseType(outType), options)
    outDs.SetProjection(fid0.GetProjection())
    outDs.SetGeoTransform(fid0.GetGeoTransform())
    
    for ib in range(nb):
        for il in range(nl):
            data0 = N.ravel(fid0.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            data1 = N.ravel(fid1.GetRasterBand(ib+1).ReadAsArray(0,il,ns,1)).astype(float)
            
            # compute data0/data1
            if nodata is None:
                wtc = (N.abs(data1) > epsilon)
            else:
                wtc = (data0 != nodata) * (data1 != nodata) * (N.abs(data1) > epsilon)

            dataout=N.zeros(ns)
            if wtc.any():
                data1_float=data1.astype(float)
                dataout[wtc] = data0[wtc]/data1_float[wtc] * 100

            dataout.shape=(1,-1)
            outDs.GetRasterBand(ib+1).WriteArray(N.array(dataout), 0, il)

            gdal.TermProgress( (ib*(ns*nl)+il*ns) / float(ns*nl) )

    gdal.TermProgress(1)
#_____________________________
if __name__=="__main__":

    outfile = None
    format  = 'GTiff'
    options = []
    file = []
    nodata = None
    out_nodata = None
    opType = None
    outType = 'Float32'
    opList = (('+',2), ('-',2), ('x',2), ('/',2) , ('-/',3) , ('ndvi',2), ('%',2))
    linear=[1.0, 0.0] # linear adaptation
    epsilon=1.0E-6

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
        elif arg == '-out_nodata':
            ii = ii + 1
            out_nodata = float(sys.argv[ii])
        elif arg == '-outType':
            ii = ii + 1
            outType = sys.argv[ii]
        elif arg == '-trans':
            ii = ii + 1
            linear[0] = float(sys.argv[ii])
            ii = ii + 1
            linear[1] = float(sys.argv[ii])
        elif arg == '-op':
            ii = ii + 1
            opType = sys.argv[ii]
        elif arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        else :
            file.append(arg)

        ii = ii + 1

    # check the command line
    if opType is None:
        Usage('missing operator')

    # check if the operator is in the list
    # and check the number of input files

    # check the input file exist on the drive
    for ifile in file:
        if (os.path.isfile(ifile)):
            pass
        else:
            Usage('Input file does not exist: ' + ifile)

    # call the operator
    try:
        iop = map(operator.itemgetter(0), opList).index(opType)
        nfiles = map(operator.itemgetter(1),opList)[iop]
    except ValueError:
        Usage('Operator does not exist: '+opType)

    if len(file) != nfiles:
            Usage('you must have '+str(nfiles)+' input files, you have '+str(len(file)))
    
    if opType=='+':
        op_addition(file, 1, nodata, out_nodata, outType, linear, outfile, format, options)
    elif opType=='-':
        op_addition(file, -1, nodata, out_nodata, outType, linear, outfile, format, options)
    elif opType=='x':
        op_multiplication(file,  nodata, outType, linear, outfile, format, options)
    elif opType=='/':
        op_division(file, nodata, outType, linear, outfile, format, options, epsilon)
    elif opType=='-/':
        op_relativeDiff(file, nodata, out_nodata, outType, linear, outfile, format, options)
    elif opType=='ndvi':
  	    op_ndvi(file, nodata, out_nodata, outType, linear, outfile, format, options)            
    elif opType=='%':
  	    op_percent(file, nodata, outType, linear, outfile, format, options, epsilon)            

