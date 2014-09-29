#!/usr/bin/env python
# \author: Bruno Combal, IOC/UNESCO
# \date: July 2013

try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *

import numpy
import glob
import sys
import os
from os import path
import re
import string
from subprocess import call
import shutil

def do_init():
    ulx=-180
    uly=85
    psx=0.5
    psy=-0.5
    ns=int(3*abs(ulx)/psx) # from -180 to 360
    nl=int(abs((2*uly)/psy))
    return (ulx, uly, psx, psy, ns, nl)

# 1./ mask the input: caution mask is larger than the file to process
# 2./ compute contour
def do_contourMasked(datafile, landMask, shpOut, savedRaster):
    (ulxM, ulyM, psxM, psyM, nsM, nlM) = do_init()

    #1. mask -> tmp
    dataH = gdal.Open(datafile)
    maskH = gdal.Open(landMask)
    ns=dataH.RasterXSize
    nl=dataH.RasterYSize
    nodata = 1.e20

    # cutting the mask out on longitude
    data = dataH.GetRasterBand(1).ReadAsArray(0, 0, ns, nl)
    mask = maskH.GetRasterBand(1).ReadAsArray(nsM - ns, 0, ns, nl)
    wmask = (mask == 1)
    if wmask.any():
        data[wmask] = nodata

    # write to temp file
    if os.path.exists(savedRaster): os.remove(savedRaster)

    outDrv = gdal.GetDriverByName('gtiff')
    outDs = outDrv.Create(savedRaster, ns, nl, 1, dataH.GetRasterBand(1).DataType, ["compress=lzw"])
    outDs.SetProjection(dataH.GetProjection())
    outDs.SetGeoTransform(dataH.GetGeoTransform())
    outDs.GetRasterBand(1).WriteArray(data, 0, 0)

    outDs = None

    # now compute contours
    if os.path.exists(shpOut): os.remove(shpOut)
#    lvl = numpy.arange(0,12+1) / 12.0
    interval = 0.05
    #cmdStr = 'gdal_contour -snodata {0} -3d -a dhm '.format(nodata) + '-nln {} '.format('contour') + '-fl {} '.format(str(lvl).strip('[]')).replace('\n','').replace('\r','').replace('\t',' ') + '{0} {1} '.format(savedRaster, shpOut)
    cmdStr = 'gdal_contour -snodata {0} -3d -a dhm '.format(nodata) + '-nln {} '.format('contour') + ' -i {} '.format(interval) + '{0} {1} '.format(savedRaster, shpOut)
    print cmdStr
    call(cmdStr, shell=True)

# blankfile is a mask: 0 nodata, 1 land
def do_blankFile(blankfile):

    (ulx, uly, psx, psy, ns, nl) = do_init()

    if os.path.exists(blankfile): os.remove(blankfile)

    outDrv=gdal.GetDriverByName('gtiff')
    outDS = outDrv.Create(blankfile, ns, nl, 1, GDT_Byte,["compress=lzw"])
    outDS.SetProjection('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]')
    outDS.SetGeoTransform((ulx, psx, 0, uly, 0, psy))
    bufferOut = numpy.zeros((1,ns))
    for il in range(nl):
        outDS.GetRasterBand(1).WriteArray(bufferOut, 0, il)
        
    outDS = None
# _________________________
def do_rasterize(shpfile, layername, referenceRaster, outRaster):
    # burn the vector to the file
    if os.path.exists(outRaster): os.remove(outRaster)
    shutil.copyfile(referenceRaster, outRaster)

    print 'gdal_rasterize -b 1 -burn 1 -l {0} {1} {2}'.format(layername, shpfile, outRaster)
    returnCode = call('gdal_rasterize -b 1 -burn 1 -l {0} {1} {2}'.format(layername, shpfile, outRaster), shell=True)

# _________________________
def do_replicate(rasterFName):
    

    (ulx, uly, psx, psy, ns, nl) = do_init()

    xs_t=int(360/psx)
    xs_s=0
    length = ns - xs_t
    

    handle=gdal.Open(rasterFName, GA_Update)
    nl = handle.RasterYSize
    ns = handle.RasterXSize
    for il in range(nl):
        line = handle.GetRasterBand(1).ReadAsArray(0, il, ns, 1)
        line[0, xs_t : xs_t + length] = line[0, xs_s : xs_s + length]
        handle.GetRasterBand(1).WriteArray(line, 0, il)

    handle = None

# _________________________
if __name__=="__main__":
    blankfile='/data/gis/general_data/blank_reference.tif'
    shpfile='/data/gis/general_data/world.shp'
    landMask='/data/gis/general_data/landMask.tif'
    tmpdir='/home/bruno/Documents/tmp'
    dhmDir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
    contourShpDir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
    layername='world'

    
    do_blankFile(blankfile)
    do_rasterize(shpfile, layername, blankfile, landMask)
    do_replicate(landMask)


    for filename in ['frequency_dhm_2030', 'frequency_dhm_lvl2_2030', 'frequency_dhm_2050', 'frequency_dhm_lvl2_2050']:
        do_contourMasked('{0}/{1}.tif'.format(dhmDir, filename), \
                             landMask, \
                             '{0}/contour_{1}.shp'.format(contourShpDir, filename), \
                             '{0}/contour_{1}.tif'.format(contourShpDir, filename) )
