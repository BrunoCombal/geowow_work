#!/usr/bin/env python
# author: Bruno Combal
# date: 12/12/2010, update February 2014
# make a lut table for image (image magick). To be used at AMESD head quarter

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
import math
import os
import os.path
import glob
import string
# _________________________
def do_read_lut(file):
    
    steps=[]
    colors=[]
   
    with open(file,'r') as fid:
        line = fid.read()
        
    thisList = string.split(line)
    for ii in range(len(thisList)/5):
        steps.append( ( float(thisList[0+ii*5]), float(thisList[1+ii*5]) ) )
        colors.append( ( int(thisList[2+ii*5]), int(thisList[3+ii*5]), int(thisList[4+ii*5])))
        
    fid.close()
    return [steps, colors]

# _________________________
def do_slr(infile, outfile, minMax, nNegPos, nodata, bckColor):
    inFid = gdal.open(infile, GA_ReadOnly)
    
    data=numpy.ravel(inFid.GetRasterBand(1).ReadAsArray(0, 0, inFid.RasterXSize, inFid.RasterYSize))
    red=numpy.zeros(inFid.RasterXSize*inFid.RasterYSize)+bckColor[0]
    green=numpy.zeros(inFid.RasterXSize*inFid.RasterYSize)+bckColor[1]
    blue=numpy.zeros(inFid.RasterXSize*inFid.RasterYSize)+bckColor[2]

    # neg values
    for negVal in range(0, minMax[0], minMax[0]/float(nNegPos[0])):
        wtc = data<negVal
        red[wtc]=int(255 - (abs(minMax[0])/float(nNegPos[0])))
        green[wtc]=int(255 -  (abs(minMax[0])/float(nNegPos[0])) )
        blue[wtc]=255

    for posVal in range(0, minMax[1], minMax[1]/float(nNegPos[1])):
        wtc = data >= posVal
        red[wtc]=255
        green[wtc]=int(255 -  (abs(minMax[0])/float(nNegPos[0])) )
        blue[wtc]=int(255 - (abs(minMax[0])/float(nNegPos[0])))

    outDrv=gdal.GetDriverByName('png')
    outDS=outDrv.Create(outfile, inFid.RasterXSize, inFid.RasterYSize, inFid.RasterCount, inFid.GetRasterBand(1).DataType, [])

    outDS.GetRasterBand(1).Write(red.reshape(inFid.RasterXSize, inFid.RasterYSize),0,0)
    outDS.GetRasterBand(2).Write(green.reshape(inFid.RasterXSize, inFid.RasterYSize),0,0)
    outDS.GetRasterBand(3).Write(blue.reshape(inFid.RasterXSize, inFid.RasterYSize),0,0)
# _________________________
def do_lut(file, lutSteps, lutColors, nbins, bckColor):

    if len(lutSteps) != len(lutColors):
        print "inconsistencies"
        sys.exit(1)
        
    red  = N.zeros(nbins) + bckColor[0]
    green= N.zeros(nbins) + bckColor[1]
    blue = N.zeros(nbins) + bckColor[2]

    for ii in range(len(lutSteps)):
        steps = lutSteps[ii]
        color = lutColors[ii]
        for istep in range(steps[0],steps[1]):
            red[istep] = color[0]
            green[istep] = color[1]
            blue[istep] = color[2]
        
    outDrv = gdal.GetDriverByName('GTiff')
    # gtiff driver requires 2 lines at least
    outDS = outDrv.Create(file, nbins, 2, 3, GDT_Byte,[])
    red.shape  = (1,-1)
    green.shape= (1,-1)
    blue.shape = (1,-1)
    for iline in range(2):
        outDS.GetRasterBand(1).WriteArray(N.array(red),0,iline)
        outDS.GetRasterBand(2).WriteArray(N.array(green),0,iline)
        outDS.GetRasterBand(3).WriteArray(N.array(blue),0,iline)

# _________________________
if __name__=="__main__":
    
    outfile=None
    format='Gtiff'
    lutfile=None
    bckColor=(0,0,0)
    lutSteps=[(0,10),   (10,20),    (20,40),     (40,60),     (60,100)]
    lutColors=[(0,0,0), (200,20,0), (200,128,0), (128,220,10),(64,220,128)]
    modeList=('lut','slr')
    mode='lut'
    outfile='legend.tif'
    
    ii=1
    while ii < len(sys.argv):
        arg=sys.argv[ii]
        if arg=='-o':
            ii = ii+1
            outfile=sys.argv[ii]
        elif arg=='-l':
            ii = ii +1
            lutfile=sys.argv[ii]

        elif arg=='-bck':
            ii=ii+1
            red=int(sys.argv[ii])
            ii=ii+1
            green=int(sys.argv[ii])
            ii=ii+1
            blue=int(sys.argv[ii])
            bckColor=(red, green, blue)

        elif arg=='-mode':
            ii=ii+1
            mode=sys.argv[ii]
            if mode=='slr':
                ii=ii+1
                minSLR=float(sys.argv[ii])
                ii=ii+1
                maxSLR=float(sys.argv[ii])
                ii=ii+1
                nNeg=int(sys.argv[ii])
                ii=ii+1
                nPos=int(sys.argv[ii])
                ii=ii+1
                nodata=float(sys.argv[ii])

            else:
                file=sys.argv[ii]

        ii = ii +1

    if outfile is None:
        print 'please define an outfile'
        sys.exit(1)

    if mode not in modeList:
        print 'Mode '+mode+' unknown. Select one of '+modeList
        sys.exit(1)

    if mode=='lut':
        if lutfile is not None:
            [lutSteps, lutColors]=do_read_lut(lutfile)

        do_lut(outfile, lutSteps, lutColors, 255, bckColor)

    if mode=='slr':
        do_slr(outfile, (minSLR, maxSLR), (nNeg, nPos), nodata, bckColor)
