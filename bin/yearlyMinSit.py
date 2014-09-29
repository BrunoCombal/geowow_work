#!/usr/bin/env python

## \author Bruno Combal
## \date March 2013
## definition: in a year, the extent of ice that is always > 0

import cdms2
import numpy
import math
import os
import sys

##
def yearlyMinIce(infile, variable, outfile, latMin, latMax):
    fh = cdms2.open(infile)
    if fh is None:
        exitMessage("Could not open file {0}. Exit 2.".format(infile), 2)

    if varname not in fh.variables.keys():
        exitMessage('variable named '+varname+' could not be found. Exit 4.', 4)

    yVar = fh(varname)
    
    stepType=None
    if fh['time'].units().startwith('days'):
        stepType='days'
        step=366
    elif fh['time'].units().startwith('month'):
        stepType='month'
        step=12
    if stepType is None:
        exitMessage('time step unknown {0}. Exit(5).'.format(fh['time'].units() ),5)

    # for time use selector, see page 102

    for itime in range(1, fh['time'].max()+1, step ):
        cube = yVar.subRegion(':', time=('2006-1-1', '2006-12-1'), level=None, latitude=(latMin, latMax), longitude=(0,360))


##
if __name__=="__main__":

    infile = None
    outfile = None
    variable = None
    
    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        elif arg== '-v':
            ii = ii + 1
            variable = sys.argv[ii]
        else:
            infile=sys.argv[ii]
        ii = ii + 1

    if infile is None:
        exitMessage('Input file not defined. Exit(10).', 10)
    if outfile is None:
        exitMessage('Output file not defined. Exit(11).', 11)
    if variable is None:
        exitMessage('Define a variable name (sit, ...). Exit(12).', 12)


    latMin = 50
    latMax = 90
    
    if not os.path.exists(infile):
        exitMessage('File {0} does not exist. Exit(1).'.format(infile), 1)

    doYearlyMinIce(infile, variable, outfile, latMin, latMax )
