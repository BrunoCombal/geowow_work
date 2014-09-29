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
from scipy import interpolate
import shutil
import struct

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print 'Usage: regridPop.py -elevClass raster -urbanMask raster dataCsv csv outfile'

    sys.exit(exitCode)
def makeGrid(xstart=0, xend=359, xstep=1, ystart=-90, yend=89, ystep=1):

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
# ________________
def do_transform(infile, outfile, template):
    # for netcdf3:
    cdms2.setNetcdfShuffleFlag(0)
    cdms2.setNetcdfDeflateFlag(0)
    cdms2.setNetcdfDeflateLevelFlag(0)

    with open(infile, mode='rb') as file:
        fileContent = file.read()


    (referenceGrid, latAxis, lonAxis, latBounds, lonBounds)=makeGrid()
    if os.path.exists(outfile):os.remove(outfile)
    fout = cdms2.open(outfile, "w")


    #thisData = struct.unpack(template['read_type'] * ((template['read_nl'] * template['read_ns']) // template['read_type_size']) , fileContent[template['skip_byte']:template['skip_byte']+(template['read_nl']*template['read_ns'])*template['read_type_size']] )
    skip=4*8 

    thisData = numpy.array(struct.unpack('>64800f', fileContent[skip:skip + (180*360)*4]))
    thisVar = cdms2.createVariable(thisData.reshape( (template['read_ns'], template['read_nl']) ), typecode=template['read_type'], id=template['id'], \
                                       fill_value=template['nodata'], grid=referenceGrid, copaxes=1 )
    fout.write(thisVar)

#    thisData2 = numpy.array(struct.unpack('64800B', fileContent[skip + (180*360)*4 : skip + (180*360)*4 + 180*360]))
#    thisVar2 = cdms2.createVariable(thisData2.reshape( (template['read_ns'], template['read_nl']) ), typecode='B', id='ice', \
#                                       fill_value=0, grid=referenceGrid, copaxes=1 )
#    fout.write(thisVar2)

    fout.close()
# _______________
if __name__=="__main__":


    infile=None
    outfile=None
    
    template={'skip_byte':4*8, 'read_type':'f', 'read_type_size':4, 'read_nl':360, 'read_ns':180, 'id':'sst', 'nodata':-100}

    ii=1
    while ii<len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outfile=sys.argv[ii]
        else:
            infile=arg
        ii=ii+1

    if infile is None:
        messageOnExit('Input file not defined. Exit(1).',1)
    if outfile is None:
        messageOnExit('Output file not defined. Exit(2).',2)

    do_transform(infile, outfile, template)
