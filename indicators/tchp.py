#!/usr/bin/env python
## \author Bruno Combal
## \date February 2013

## \brief compute Tropical Cyclone Heat Potential (THCP)
## http://www.kayelaby.npl.co.uk/general_physics/2_7/2_7_9.html
## sea water specific heat capacity, Cp=3993 J/kg/K
## sea water density varies with salinity, between 12.07 and 27.12 kg/m3

from itertools import takewhile
import numpy
import scipy.integrate
from scipy.io import netcdf
import cdms2
import os
import sys

##
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: tchp.py -o outfile [-theta thetvarname=theta0] [-rho rhovarname=rhopoto] [-of outputformat] [-co options] -frho rhopotofile -ftheta thetaofile'
    sys.exit(errorCode)

def latlon():
    return 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]'


def specificHeatCapacity(tempProfile, salinityProfile=35):
    # specific heat at a constant pressure of seawater (0.1MPa)
    # see code SW_SpcHeat.m form http://web.mit.edu/seawater/
    temperature = 1.00024 * tempProfile
    salinity = salinityProfile/1.00472
    
    A =  4206.8 - 6.6197*S + 1.2288E-2*S*S;
    B = -1.1262 + 5.4178E-2*S - 2.2719E-4*S*S;
    C =  1.2026E-2 - 5.3566E-4*S + 1.8906E-6*S*S;
    D =  6.8777E-7 + 1.517E-6 *S - 4.4268E-9*S*S;

    cp = A + B*T + C*T*T + D*T*T*T;

## \brief integral of potential temperature from 26 celsius degrees to surface
## see http://stackoverflow.com/questions/14897003/python-finding-a-continuous-list-of-values-matching-a-condition-starting-from
## Note: the level corresponding to 26 degrees likely need to be interpolated
## if last value is not 26deg, take depth of values surrounding 26deg, then interpolate its depth.
## Then build and array with irregularly spaced data before integration
def computeHeatPotential(profileTheta, profileRho, zlevels, threshold=299.15, nodata=1e+20):
    if (profileTheta[0] >= nodata) or (profileRho[0] >= nodata):
        return -1
    if (profileTheta[0] < threshold) :
        return 0

    # 1./ get subarrays with 26<= temp <= surface temp
    C = 3993
    zprofile=numpy.array(list(takewhile(lambda e:e>=threshold, profileTheta) ))
    if len(zprofile) == 0:
        return 0
    levels = zlevels[0 : len(zprofile) ]
    profile = (zprofile - min(zprofile) )* profileRho[ 0:len(zprofile) ]

    #print '>>> \n >>>code to be corrected here for integrating from the actual 26 Celsius degrees level\n >>>'

    # 2./ compute integral scipy.integrate.trapz

    integral=scipy.integrate.trapz(profile, levels)

    return C * integral

## \brief read input file, compute THCP, write output file 
def doTCHP(thetaFile, thetaVar, rhoFile, rhoVar, nodata, thresholdTemp, outFile, outFormat, options):

    print '# open file'
    fhTheta = cdms2.open(thetaFile)
    if fhTheta is None:
        exitMessage("Could not open file {0}. Exit 2.".format(thetaFile), 2)

    fhRho = cdms2.open(rhoFile)
    if fhRho is None:
        exitMessage("Could not open file {0}; Exit(2).".format(rhoFile), 2)

    thetao = fhTheta.variables[thetaVar][:] # [time, levels, lat, lon]
    rho = fhRho.variables[rhoVar][:]
    levelsTmp = fhTheta.variables['lev_bnds'][:]
    levels = numpy.ravel(0.5*(levelsTmp[:,0] + levelsTmp[:,1] ))
    print '# mapHeat : time, lat, lon'
    mapHeat = numpy.zeros( (thetao.shape[0], thetao.shape[2], thetao.shape[3]) ) - 1
    
    print '# Compressing loops...'
    timelatlon=[]
    for itime in range(thetao.shape[0]):
        for ilat in range(thetao.shape[2]):
            for ilon in  range(thetao.shape[3]):
                if thetao[itime, 0, ilat, ilon] < nodata:
                    timelatlon.append((itime, ilat, ilon))

    # loop over time, lat and lon
    print "parsing the maps"
    counter=0
    for ill in timelatlon:
        profileTheta = thetao[ ill[0], : ,ill[1], ill[2] ].ravel()
        profileRho = rho[ ill[0], : ,ill[1], ill[2] ].ravel()
        heat = 0
        heat = computeHeatPotential( profileTheta, profileRho, levels, thresholdTemp, nodata )
        mapHeat[ ill[0], ill[1], ill[2] ] = heat
        #gdal.TermProgress_nocb( counter/float(len(timelatlon)) )
        counter = counter+1
 
    #gdal.TermProgress_nocb(1)

    # save result
 #   outDrv = gdal.GetDriverByName(outformat)
 #   outDS = outDrv.Create(outFile, mapHeat.shape[2], mapHeat.shape[1], mapHeat.shape[0], GDT_Float32, options)
 #   outDS.SetProjection(latlon())

    output=cdms2.open(outfile, 'w')
    output.write(mapHeat)
    output.close()
    fhTheta.close()
    fhRho.close()

#    for itime in range(thetao.shape[0]):
#        print '.',
#        data = numpy.ravel(mapHeat[itime, :, :])
 #       outDS.GetRasterBand(itime+1).WriteArray( numpy.flipud( data.reshape((mapHeat.shape[1], mapHeat.shape[2])) ) )
 #       gdal.TermProgress_nocb( itime/float(thetao.shape[0]) )
#    gdal.TermProgress_nocb(1)

    print
    outDS = None

##
if __name__=="__main__":
    theta_file = None
    rho_file = None
    outfile = None
    thresholdTemp = 26+273.15
    outformat = 'gtiff'
    options = []
    nodata = 1e+20
    thetao_var='thetao'
    rho_var = 'rhopoto'

    ii=1
    while ii < len(sys.argv):
        arg=sys.argv[ii]
        if arg == '-o':
            ii=ii+1
            outfile = sys.argv[ii]
        elif arg == '-theta':
            ii = ii +1
            thetao_var = sys.argv[ii]
        elif arg== '-rho':
            ii = ii +1
            rho_var = sys.argv[ii]
        elif arg == '-of':
            ii = ii + 1
            outformat=sys.argv[ii]
        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
        elif arg == '-frho':
            ii = ii+1
            rho_file = sys.argv[ii]
        elif arg == '-ftheta':
            ii = ii+1
            theta_file = sys.argv[ii]
        ii = ii + 1

    if rho_file is None:
        exitMessage('Missing an input file name for potential Rho. Exit(1).', 1)

    if not os.path.exists(rho_file):
        exitMessage('Rho file {0} does not exists. Exit(20).', 20)

    if theta_file is None:
        exitMessage('Missing an input file name for potential Theta. Exit(1).', 1)

    if not os.path.exists(theta_file):
        exitMessage('Theta file {0} does not exists. Exit(30).', 30)

    if outfile is None:
        exitMessage('Missing an output file name. Exit(2).', 2)

    if thetao_var is None:
        exitMessage('Missing a variable name for thetao. Exit(3).', 3)

    if rho_var is None:
        exitMessage('Missing a variable name for rhopoto. Exit(4)', 4)

    doTCHP(theta_file, thetao_var, rho_file, rho_var, nodata, thresholdTemp, outfile, outformat, options)

# EOF
