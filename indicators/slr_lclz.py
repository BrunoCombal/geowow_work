#!/usr/bin/env python
## \author Bruno Combal
## \date April 2013


from osgeo import gdal
from osgeo.gdalconst import *
import numpy
import sys

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: seaLevelRiseIndicator.py -o outputfile inputfile varname'
    exit(errorCode)


## \brief select DEM pixels with minElev <= elevation <= maxElev
## return coordinates list
def doSelectDEM(demFile, minElev, maxElev, outfile='tmp.tif', typeProc='value'):
    infile = gdal.Open(demFile, GA_ReadOnly)
    data = numpy.ravel(infile.GetRasterBand(1).ReadAsArray(0,0, infile.RasterXSize, infile.RasterYSize))

    #1 save the resulting mask
    if typeProc=='value':
        wtk = (data >= minElev) * (data <= maxElev)
        data[ data < minElev ]=-100000
        data[ data > maxElev ]= 100000
        typeOut=GDT_Float32
    else:
        data[ data>maxElev] = 254
        data[ data<minElev ] = 255
        wti = (data >= minElev) * (data <= maxElev)
        data[ wti ] = data[ wti ].round(0)
        typeOut=GDT_Byte
    drv=gdal.GetDriverByName('gtiff')
    outds = drv.Create(outfile, infile.RasterXSize, infile.RasterYSize, 1, typeOut, ['compress=lzw'])
    outds.GetRasterBand(1).WriteArray( numpy.reshape(data, (infile.RasterXSize, infile.RasterYSize)), 0, 0)
    proj = infile.GetProjection()
    geotrans = infile.GetGeoTransform()
    outds.SetProjection(proj)
    outds.SetGeoTransform(geotrans)
    outds=None

    #2 generate a list of locations
#    print 'compute locations'
#    wtk = wtk.reshape((infile.RasterXSize, infile.RasterYSize))
#    locations=[]
#    for ii in range(data.shape[0]):
#        for jj in range(data.shape[1]):
#            if wtk[ii, jj]:
#                print '.',
#                locations.append([ii, jj])
#    return ( proj, geotrans, locations)

## This code is made for processing tiles of a DEM
## A single DEM tile is compared to 
if __name__=="__main__":
    popFile=''
    demFile='/data/dem/ace2/tmp/00N090E_3S.ACE2'
    maskOutFile=None
    minElev=0
    maxElev=10
    typeProc='value'

    ii=1
    while ii<len(sys.argv):
        arg=sys.argv[ii]
        if arg == '--maskOutFile':
            ii = ii +1
            maskOutFile=sys.argv[ii]
        elif arg == '--minmax':
            ii=ii+1
            minElev=float(sys.argv[ii])
            ii=ii+1
            maxElev=float(sys.argv[ii])
        elif arg== '--type':
            ii=ii+1
            typeProc=sys.argv[ii]
        elif arg == '--demInFile':
            ii=ii+1
            demFile=sys.argv[ii]
        ii=ii+1

    if maskOutFile is None:
        exitMessage('Missing a dem file, use option --demInFile. Exit(101).',101)
    if maskOutFile is None:
        exitMessage('Missing an output file name for mask, use option --maskOutFile. Exit(102).', 102)

    doSelectDEM(demFile, minElev, maxElev, maskOutFile, typeProc)
