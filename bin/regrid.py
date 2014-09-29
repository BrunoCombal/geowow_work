#!/usr/bin/env python

## \author Bruno Combal
## \date March 2013

import cdms2
import numpy
import math
import os
import sys

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: regrid.py -o outputfile -v varname [-polar] inputfile'
    print
    exit(errorCode)

##
def doPolarGrid():
    latMin = 50
    latMax = 90
    latStep = 0.5
    latMinRad = latMin * numpy.pi / 180.0
    latMaxRad = 0.5*numpy.pi 
    latStepRad = latStep * numpy.pi / 180.0
    lonMinRad = 0
    lonMaxRAd = 2 * numpy.pi

    xRange = numpy.arange( -latMinRad,  latMinRad, latStepRad )
    yRange = numpy.arange( -latMinRad, latMinRad, latStepRad )

    latArray = numpy.zeros( ( xRange.shape[0], yRange.shape[0]) )
    lonArray = numpy.zeros( ( xRange.shape[0], yRange.shape[0]) )

    for ii in range(len(xRange)):
        for jj in range(len(yRange)):
            rho   = math.sqrt( xRange[ii] * xRange[ii] + yRange[jj] * yRange[jj] )
            theta = math.atan2( xRange[ii], yRange[jj] )
            latArray[ ii, jj ] = 90 - rho*180/numpy.pi
            lonArray[ ii, jj ] = theta * 180 / numpy.pi

    return latArray,lonArray

## \brief resample the data into a regular grid
def doRegrid(infile, varname, outfile, lon, lat, lon_bnds, lat_bnds):

    cdms2.setNetcdfShuffleFlag(1)
    cdms2.setNetcdfDeflateFlag(1)
    cdms2.setNetcdfDeflateLevelFlag(2)

    fh = cdms2.open(infile)
    if fh is None:
        exitMessage("Could not open file {0}. Exit 2.".format(infile), 2)

    if varname not in fh.variables.keys():
        exitMessage('variable named '+varname+' could not be found. Exit 4.', 4)

    yVar = fh(varname)

    latAxis = cdms2.createAxis(lat, lat_bnds)
    latAxis.designateLatitude(True)
    latAxis.units = 'degree_north'
    latAxis.long_name = 'Latitude'

    lonAxis = cdms2.createAxis(lon, lon_bnds)
    lonAxis.designateLongitude(True, 360.0)
    lonAxis.units = 'degree_east'
    lonAxis.long_name='Longitude'

    listAxisOrg = yVar.getAxisList()
    timeAxis = listAxisOrg[0]
    

    grid = cdms2.createGenericGrid(latAxis, lonAxis, lat_bnds, lon_bnds)
    regridded = yVar.regrid(grid)

    g=cdms2.open(outfile, 'w')
    
    #g.write(regridded, None, None, None, varname, None, 1.e20, None, cdms2.CdFloat)
    temp1 = cdms2.createVariable(regridded, typecode='f', id=varname, fill_value=1.e20, axes=[timeAxis, latAxis, lonAxis], copyaxes=0, attributes=dict(long_name=yVar.long_name, units=yVar.units) )
    g.write(temp1)
    g.close()

##
if __name__=="__main__":

    infile = None
    outfile = None
    variable = None
    polar = False
    lon_bnds=[]
    lat_bnds=[]
    lon=[]
    lat=[]
    
    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        elif arg== '-v':
            ii = ii + 1
            variable = sys.argv[ii]
        elif arg == '-polar':
            polar=True
        else:
            infile=sys.argv[ii]
        ii = ii + 1

    if infile is None:
        exitMessage('Input file not defined. Exit(10).', 10)

    if outfile is None:
        exitMessage('Output file not defined. Exit(11).', 11)

    if variable is None:
        exitMessage('Define a variable name (zos, ph, o2min, ...). Exit(12).', 12)

    if not polar:
        xstart=0
        xend=360
        xstep=0.5
        ystart=-90
        yend=90
        ystep=0.5
        

        for ii in numpy.arange(xstart, xend, xstep):
            lon_bnds.append( [ii, ii+xstep] )
            lon.append(ii+0.5*xstep)

        lon_bnds=numpy.array(lon_bnds)
        lon = numpy.array(lon)

        for ii in numpy.arange(ystart, yend, ystep):
            lat_bnds.append( [ii, ii+ystep] )
            lat.append(ii+0.5*ystep)

        lat_bnds = numpy.array(lat_bnds)
        lat = numpy.array(lat)

        print lat_bnds.shape, lat.shape

    else:
        yRange, xRange = doPolarGrid()
        

    if not os.path.exists(infile):
        exitMessage('File {0} does not exist. Exit(1).'.format(infile), 1)

    doRegrid(infile, variable, outfile, lon, lat, lon_bnds, lat_bnds )
