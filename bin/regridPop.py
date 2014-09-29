#!/usr/bin/env python
# \author Bruno Combal
# \date April 2013

from osgeo import gdal
from osgeo.gdalconst import *
import numpy
import csv
import os
import os.path
import sys

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print 'Usage: regridPop.py -elevClass raster -urbanMask raster dataCsv csv outfile'

    sys.exit(exitCode)
  
##
def doRegridPop(elevClasses, urbanMask, dataCsv, separator, outfile, outformat, options):
 
    urbanRuralCode={'urban':2,'rural':1}
   
    # open raster files
    elevFID = gdal.Open(elevClasses, GA_ReadOnly)
    urbanFID= gdal.Open(urbanMask, GA_ReadOnly)
 
    # read csv data
    classElev=[]
    ruralUrban=[]
    pop=[]
    with open(dataCsv, 'rb') as csvfile:
        line = csv.reader(csvfile, delimiter=separator)
        # countryISO classElev ruralUrban pop1990 pop2000 pop2010 pop2030 pop2050 pop2100 area
        for row in line:
            classElev.append(int(row[1]))
            
            ruralUrban.append( urbanRuralCode[row[2].lower()] )
            pop.append( [int(row[3]), int(row[4]), int(row[5]), int(row[6]), int(row[7]), int(row[8])] )

    npop = 6

    # open output
    outDrv = gdal.GetDriverByName(outformat)
    outDs = outDrv.Create(outfile, elevFID.RasterXSize, elevFID.RasterYSize, npop, GDT_Int16, options)

    # process line by line
    print "number of lines to process ",elevFID.RasterYSize
    for il in range(elevFID.RasterYSize):
        
        urbanData=numpy.ravel(urbanFID.GetRasterBand(1).ReadAsArray(0, il, elevFID.RasterXSize, 1) )
        if urbanData.any():
            elevData=numpy.ravel(elevFID.GetRasterBand(1).ReadAsArray(0, il, elevFID.RasterXSize, 1) )
            for iurban in [1, 2]:
                for ielev in [1, 3, 5, 7, 9, 10, 12, 20]:
                    wtp = (urbanData == iurban) * (elevData == ielev)
                    if wtp.any():
                        # number of pixels
                        npixels = wtp.sum()
                        # value to regrid
                        wvalue = (ruralUrban == iurban) * (classElev == ielev)
                        print 'ielev={0}, npixels={1}, wvalue={2}'.format(ielev, npixels, wvalue)
                        if numpy.sum(wvalue) > 1:
                            print "stopping at line ",il
                            print "iurban=",iurban, "classElev=",ielev
                            print wvalue
                            messageOnExit('Error when processing csv file; found {0} values. Exit(200)'.format(numpy.sum(wvalue), 200))
                        elif numpy.sum(wvalue) == 1:
                            thisPopList = pop[wvalue]
                            for iband in range(npop):
                                outdata = numpy.zeros(elevData.shape[0]) - 1 # -1=no data
                                outdata[wtp] = thisPopList[iband] # nobody in investigated areas, by default
                                outDs.GetRasterBand(iband+1).WriteArray( outdata.reshape(1, -1) , 0, il)
                        else:
                            print "iurban=",iurban, "classElev=",ielev
                            print 'no data found, continue.'

    # close datasets
    elevFID = None
    urbanFID = None
    outDs = None

##
if __name__=="__main__":
    elevClasses=None
    urbanMask=None
    dataCsv=None
    outfile=None
    outformat='gtiff'
    options=['compress=lzw']
    separator=' '

    ii=1
    while ii < len(sys.argv):
        arg=sys.argv[ii]
        if arg=='-elevClasses':
            ii=ii+1
            elevClasses=sys.argv[ii]
        elif arg=='-urbanMask':
            ii=ii+1
            urbanMask=sys.argv[ii]
        elif arg=='-dataCsv':
            ii = ii + 1
            dataCsv=sys.argv[ii]
        elif arg=='-sep':
            ii = ii +1
            separator=sys.argv[ii]
        else:
            outfile=sys.argv[ii]
        ii=ii+1

    if urbanMask is None:
        messageOnExit('missing an urban mask, use option -urbanMask. Exit(100).', 100)
    if elevClasses is None:
        messageOnExit('missing an elevation classes mask, use option -elevClasses. Exit(101).',101)
    if dataCsv is None:
        messageOnExit('missing a csv data, use -dataCsv option. Exit(102).',102)
    if outfile is None:
        messageOnExit('output file is not defined. Exit(103).',103)

    doRegridPop(elevClasses, urbanMask, dataCsv, separator, outfile, outformat, options)
