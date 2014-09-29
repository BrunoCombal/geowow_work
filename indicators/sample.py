#!/usr/bin/env python
## \author Bruno Combal
## \date January 2013

from scipy.io import netcdf
import matplotlib.pyplot as plt
import numpy

import os
import sys

file='/Volumes/wddrive/cmip5/sea_level_above_geoid/rcp8.5/zos_Omon_FGOALS-s2_rcp85_r1i1p1_200601-210012.nc'
nodata=1.e20
variable='zos'
fh=netcdf.netcdf_file(file,"r")
yVar=numpy.array(fh.variables[variable][:])
orgShape=fh.variables[variable].shape # time, y, x

# let's sample locations
xstep=40
ystep=40
output=[]
outputxy=[]
for iy in range(0, orgShape[1], ystep):
    for ix in range(0, orgShape[2], xstep):
        if yVar[0, iy, ix] < nodata:
            outputxy.append((ix,iy))
            output.append(yVar[:, iy, ix].ravel())
print '#',
for xy in outputxy:
    print xy,
print

for ii in range(orgShape[0]):
    for series in output:
        print series[ii],
    print

