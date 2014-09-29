#!/usr/bin/env python
# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

import cdms2
from cdms2 import MV
import numpy
import glob
import sys
import os
from os import path
import re
import shutil


def makeGrid():
    xstart=0
    xend=360
    xstep=0.5
    ystart=-85
    yend=85
    ystep=0.5

    lon_bnds=[]
    lon=[]
    for ii in numpy.arange(xstart, xend, xstep):
        lon_bnds.append( [ii, ii+xstep] )
        lon.append(ii+0.5*xstep)
    lon_bnds=numpy.array(lon_bnds)
    lon=numpy.array(lon)

    lat_bnds=[]
    lat=[]
    for ii in numpy.arange(ystart, yend, ystep):
        lat_bnds.append([ii, ii+ystep])
        lat.append(ii+0.5*ystep)
    lat_bnds=numpy.array(lat_bnds)
    lat=numpy.array(lat)

    latAxis = cdms2.createAxis(lat, lat_bnds)
    latAxis.designateLatitude(True)
    latAxis.units='degrees_north'
    latAxis.long_name='Latitude'
    latAxis.id='latitude'

    lonAxis = cdms2.createAxis(lon, lon_bnds)
    lonAxis.designateLongitude(True, 360.0)
    lonAxis.units='degrees_east'
    lonAxis.id='longitude'
    lonAxis.long_name='Longitude'

    return((cdms2.createGenericGrid(latAxis, lonAxis, lat_bnds, lon_bnds), latAxis, lonAxis, lat_bnds, lon_bnds))
# __________________
# this code is used to regrid Reynolds data to 0.5x0.5
(referenceGrid, latAxis, lonAxis, latBounds, lonBounds) = makeGrid()
nodata = 1.e20

file=cdms2.open('/data/sst/reynolds_climatology/data.cdf','r')
sst=file('sst')[:]
sstregrid=sst.regrid(referenceGrid)
timeAxis=sst.getAxisList()[0]
print timeAxis.long_name
temp=cdms2.createVariable(sstregrid, typecode='f', id='sst', fill_value=1.e20, axes=[timeAxis, latAxis, lonAxis], copyaxes=0, attributes=dict(long_name=sstregrid.long_name, units=yVar.units) )
g = cdms2.open('/data/sst/reynolds_climatology/sstClimatology_0.5x0.5.nc')
g.write(temp)
g.close()
file.close()
