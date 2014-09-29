#!/usr/bin/env python

# \author Bruno Combal, IOC/UNESCO
# \date June 2013

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
import make_ensembleMean_TOS as MEM # to share some functions
import shutil

# ____________________
# Earth is modelled as a sphere (CMIP5 standard)
# Surface in km2
def sectorSurface(xMin, xMax, yMin, yMax, EarthRadius=6.371):
    
    return (0.5 * (abs(xMax[0]-xMin[0]) + abs(xMax[1]-xMin[1]) ) * EarthRadius * abs(yMax-yMin))

# _____________________
def do_iceArea(fileList, areacello, variable, outDir):

    latMin=45.0
    latMax=90.0

    for ifile in fileList:
        thisFile = cdms2.open(ifile)
        thisVarGnrl = thisFile(variable, latitude=(latMin, latMax, 'cc'))

        #myIce = MV.masked_where( thisVarGnrl <= 0.0 , thisVarGnrl)
        print ifile
        a=thisFile(variable).getGrid().toGenericGrid()
        
        orgBounds = a.getBounds()
#        theseBounds = thisVarGnrl.getGrid().toGenericGrid()

#        longitude = thisVarGnrl.getGrid().getLongitude()
#        latitude = thisVarGnrl.getGrid().getLatitude()
        
        for itime in thisVarGnrl.getTime().asComponentTime():
            thisVar = thisFile(variable, time = itime, latitude=(latMin, latMax, 'cc'), squeeze=1)

            wice = numpy.ravel(thisVar[:]) > 0
            print wice.shape
            if wice.any():
                print wice.sum()
#                thisLongitude = numpy.longitude[wice]
#            thisLatitude = latitude[wice]

#            condition = MV.masked_where(thisVar <= 0, thisVar)
#            thisLongitude = MV.take(longitude, condition )
#            thisLatitude = MV.take(latitude, condition) 
#            print itime, thisLongitude.shape, thisLatitude.shape

        thisFile.close()
# _____________________
# compute sea ice total surface, as a function of time
# for each model separately.
# Only the total surface is averaged
if __name__=="__main__":
    inDir='/data/cmip5/rcp/rcp8.5/sit'
    outDir=''
    variable='sit'

    minYear=2006
    maxYear=2050

    # model synthesis: let's work on monthly integrated values, rather than days

    modelList=(['sit_OImon_bcc-csm1', 'areacello_fx_bcc-csm1-1_rcp85_r0i0p0.nc'], ['sit_OImon_BNU-ESM', None], ['sit_OImon_HadGEM2-A0',None], ['sit_OImon_NorESM1-M', None])
    
    for imodel,iarea in modelList:
        fileList = glob.glob('{0}/{1}*nc'.format(inDir, imodel))
        do_iceArea(fileList, iarea, variable, outDir)
