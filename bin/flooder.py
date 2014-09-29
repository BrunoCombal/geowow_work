#!/usr/bin/env python
## \author Bruno Combal
## \date February 2013
## Compute a flood map

import sys
import os
import myTools
from osgeo import gdal
from osgeo.gdalconst import *

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print 'Usage: flooder.py -o outfile -dem demfile -time t inputZOS'
    print 'Outfile is deleted first.'
    
    sys.exit(exitCode)

##
def initDEM(dem, zos):
    # set to None any DEM cell corresponding to ocean
    # fill gaps between shore line and ocean
    continue

##
## dem and sea are two superimposable arrays
## shoreline=[(x,y, z0+zos), (x,y, z0+zos), (x,y, z0+zos),...]
## output: sea: the new sea extent
def computeFlood(dem,sea, shoreline):
    seed = shoreline.copy()
    newSeed=[]
    while len(seed) !=0:
        for iseed in seed:
            (x,y, ztotal)=iseed
            for idir in [(x-1,y-1),(x,y-1),(x+1,y-1),(x-1,y),(x+1,y),(x-1,y+1),(x,y+1),(x+1,y+1)]:
                if sea[idir] is False and dem[idir]<ztotal:
                    sea[idir]=True
                    newSeed.append(idir)
        seed=newSeed.copy()

    return(sea)

##
def doFloodmap(demFile, inZOS, outFile):
    # read demFile
    demFid = gdal.open( demFile, GA_ReadOnly )
    dem = demFid.GetRasterBand(1).ReadAsArray( 0, 0, demFid.RasterXSize, demFid.RasterYSize )
    demGT = demFid.GetGeoTransform()
    pixelToMap(demFid.XRaster)
    # read inZOS
    zosFid = gdal.open( inZOS, GA_ReadOnly )
    # cut out the area needed to cover the DEM
    xstart, ystart = myTools.mapToPixel(demGT[0], demGT[3], zosFid.GetGeoTransform())
    xend, yend = myTools.mapToPixel
    xend, yend = bidule
    zos = zosFid.GetRasterBand(1).ReadAsArray( xstart, ystart, xend-xstart+1, yend-ystart+1)
    
    # recode dem
    # go through zos, and set a None in dem where zos is found, at the same lat/lon

    # complete zos
    # where zos is None and DEM is None, propagate/interpolate closest values

    # collect data along the shoreline
    # shoreline is a precomputed array
    # with shoreline, collect MSL

    
##
## input data:
## 1./ DEM (ace2)
## 2./ sea background (same grid as ace2): 1 out of the shoreline shapefile
## 3./ shoreline raster (same grid as ace2): MSL value on the shoreline
## 4./ zos (same grid as ace2)

## data preparation
## fill no-data in MSL (qgis, analyse, fill no data)
## split MSL in large grid cells (10°x10°)
## split ACE2 in the same grid cells
## transform shoreline polygone into a line, burn to empty MSL grid, collect MSL where pixel=1 -> (3)
## for each ACE2 grid cell, burn sea background
## for each zos: capture zos values for the same MSL
if __name__=="__main__":
    inZOS=None
    outFile=None
    demFile=None
    time=None

    # get parameters
    
    # check parameters
    
    # time decision: if None: process all available dates

    # complete DEM file with ZOS data
	doFlood(demFile, inZOS, outFile)
