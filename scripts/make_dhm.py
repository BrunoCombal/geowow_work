#!/usr/bin/env python

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

# computation of DHM
# 1./ compute a model climatology (ready made) and get an actual climato
# 1.a/ compute current model (SST - climato) -> delta
# 1.b/ apply delta to actual climato -> corrected SST
# 2./ From Corrected SST, compute DHM
# 2.a/ DHM: compare sum(past 4 months to now) to max(actual climato): 2 degrees above-> level 2

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

# _________________________________
# return the month count from year 0
def yyyymm2count(year, month):
    return year*12+month
# ________________
def count2yyyymm(count):
    year=int((count-1)/12)
    month = (count-12*year)
    return (year, month)
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
# _______________
def quickSave(data, name, path):
    # for netcdf3: set flags to 0
    cdms2.setNetcdfShuffleFlag(0) #1
    cdms2.setNetcdfDeflateFlag(0) #1
    cdms2.setNetcdfDeflateLevelFlag(0) #3

    outname=os.path.join(path, name)
    if os.path.exists(outname): os.remove(outname)
    fh = cdms2.open(outname, 'w')
    variable = cdms2.createVariable(data, id='data')
    fh.write(variable)
    fh.close()
# _______________
def saveData(outfilename, data, typecode, id, fill_value, grid, copyaxes, attribute1, attribute2, latAxis, lonAxis):
    
    # for netcdf3: set flags to 0
    cdms2.setNetcdfShuffleFlag(0) #1
    cdms2.setNetcdfDeflateFlag(0) #1
    cdms2.setNetcdfDeflateLevelFlag(0) #3

    if os.path.exists(outfilename): os.remove(outfilename)
    outfile = cdms2.open( outfilename, 'w')
    var = cdms2.createVariable(data, typecode=typecode, id=id, fill_value=fill_value, grid=grid, copyaxes=copyaxes, attributes=dict(long_name=attribute1, units=attribute2) )
    var.setAxisList((latAxis, lonAxis))
    outfile.write(var)
    outfile.close()
# _______________
# data have y first, then x
def do_resize(var, infile):
    yvar=infile[var][:] # y, x
    dim=yvar.shape

    points=numpy.zeros( (dim[0], dim[1], 2))
    for jj in range(dim[0]):
        for ii in range(dim[1]):
            points[jj, ii, 0] = jj
            points[jj, ii, 1] = ii

    outGY, outGX = numpy.mgrid[ -85 + 85 :85 + 85 :0.5 , 0:360:0.5 ]

    outvar = interpolate.griddata(numpy.reshape(points, (dim[0]*dim[1],2)), numpy.ravel(yvar), (outGY, outGX), method='linear')

    return outvar
# _______________
def do_resize_fit(var, infile):
    print 'try to open ',infile
    fh=cdms2.open( infile , 'r')
    data = numpy.squeeze(fh[var][:]) # 180x360

    dim = data.shape
    print 'dim=',dim

    points=numpy.zeros( (dim[0], dim[1], 2))
    for jj in range(dim[0]):
        for ii in range(dim[1]):
            points[jj, ii,0]=jj
            points[jj, ii,1]=ii

    outGY, outGX = numpy.mgrid[ 0 : dim[0] : 0.5 , 0: dim[1]:0.5 ]
    outvar = interpolate.griddata(numpy.reshape(points, (dim[0]*dim[1],2)), numpy.ravel(data), (outGY, outGX), method='linear')

    # now resize from -85 to 85
    outvar = outvar[ 5: 340]
    print 'do_resize_fit ->',dim, outvar.shape

    return numpy.flipud(outvar)
# _______________
def do_resize_all(var, infile):
    yvar=infile[var][:] # y, x
    dim=yvar.shape

    points=numpy.zeros( (dim[1], dim[2], 2))
    for ii in range(dim[1]):
        for jj in range(dim[2]):
            points[ii,jj,0]=ii
            points[ii,jj,1]=jj

    outGY, outGX = numpy.mgrid[ -85 + 85 :85 + 85  :0.5 , 0:360:0.5 ]

    outvar = numpy.zeros( (dim[0], outGX.shape[0], outGX.shape[1]) )
    for itime in range(0, 12):
        print 'regridding for time: {0}'.format(itime)
        tmp = interpolate.griddata(numpy.reshape(points, (dim[1]*dim[2],2)), numpy.ravel(yvar[itime, :, :]), (outGY, outGX), method='linear')
        outvar[itime,:,:] = numpy.flipud(tmp)
        
    return outvar
# _______________
def readVar(var, infile):
    fh = cdms2.open(infile, 'r')
    data = fh[var][:]
    fh.close()
    return data

# _______________
# arrays were interpolated: creation of false 'nodata' values along the coast.
# no data are all reset
def resetNoData(data, limit, nodata):
    wtnd = data>limit
    if wtnd.any():
        data[wtnd] = 1.e20
    return data
# _______________
# note: real Climato has a coarser resolution
def do_dhm(var, inhist, modelClimatoRootName, indir, sstRootName, realClimato, maxRealClimato, realClimRMSAtMaxSST, outdir, dhmRootName, yearList):

    nodata = 1.e20
    (referenceGrid, latAxis, lonAxis, latBounds, lonBounds) = makeGrid()

    # open climatoMas
    climMax = readVar('sst', maxRealClimato)
    climMax = resetNoData(climMax, 50, nodata)
    RMSatMaxSST=readVar('rms_at_max',realClimRMSAtMaxSST)
    RMSatMaxSST=resetNoData(RMSatMaxSST, 50, nodata)
    climMax = climMax + RMSatMaxSST

    # open realClimato
    realClim = readVar('sst', realClimato)
    realClim = resetNoData(realClim, 50, 1.e20) # realClim a le meilleur masque de nodata

    # open the 12 model climatos
    modelClim=[]
    frequencyLvl2=numpy.zeros( realClim[0].shape[0] * realClim[0].shape[1] )
    for imonth in range(1,13):
        thisName=os.path.join(inhist, '{0}{1:02}.nc'.format(modelClimatoRootName, imonth))
        if not os.path.exists(thisName): 
            print 'missing model climato {0}. Exit.'.format(thisName)
            sys.exit(1)
        modelClim.append(cdms2.open(thisName,'r'))

    # processing loop
    for iyear in yearList:

        dhmYearly = numpy.zeros( realClim[0].shape[0] * realClim[0].shape[1] ) # defined as the max dhm for this year
        for imonth in range(1,13):

            dhm = numpy.zeros( realClim[0].shape[0] * realClim[0].shape[1] )
            for ishift in 0, -1, -2, -3:
                shiftYear, shiftMonth = count2yyyymm( yyyymm2count(iyear, imonth) + ishift)
                #print 'rolling window: ', iyear, imonth, ishift, ' >> ', shiftYear, shiftMonth
                sstFName = os.path.join(indir, '{0}{1}{2:02}.nc'.format(sstRootName, shiftYear, shiftMonth))
                #print '!!! opening ',sstFName
                thisModelSST = cdms2.open( sstFName, 'r' )

                # thisModelSST: K ; modelClim: K ; realClimato: C
                # thisModelSST: continents=1.e20, modelClim=continents=1.e20
                tosCorrected = realClim[ shiftMonth-1, :, : ] + ( thisModelSST[var][:] - modelClim[ shiftMonth-1 ]['Band1'][:])

                #quickSave(realClim[ thisMonth,:,: ], 'realClim.nc', '/data/tmp')
                quickSave(thisModelSST[var][:], 'thisModelSST.nc','/data/tmp')
                quickSave(modelClim[ shiftMonth-1 ]['Band1'][:], 'modelClim.nc','/data/tmp')
                #quickSave(climMax, 'climMax.nc','/data/tmp')
                #quickSave(RMSatMaxSST,'rmsMaxSST.nc','/data/tmp')
                #quickSave(tosCorrected, 'tosCorrected_{0:02}_{1}.nc'.format(imonth,ishift), '/data/tmp')
                if ishift == 0:
                    delta = thisModelSST[var][:] - modelClim[ shiftMonth-1 ]['Band1'][:]
                    quickSave(delta, 'delta_{0}_{1:02}_{2}.nc'.format(iyear,imonth,ishift), '/data/tmp')
                #sys.exit()

                thisModelSST.close()

                ##
                # wtk = tosCorrected.ravel() > ( numpy.ravel(climMax + RMSatMaxSST) )
                ## use an already corected version of climMax
                wtk = numpy.ravel(tosCorrected) > numpy.ravel(climMax)
                if wtk.any():
                    ##
                    # dhm[wtk] = dhm[wtk] + numpy.ravel(tosCorrected - climMax - RMSatMaxSST)[wtk]
                    ##
                    dhm[wtk] = dhm[wtk] + numpy.ravel(tosCorrected - climMax )[wtk]

            # reset nodata: from realClim and modelClim
            wnodata = numpy.ravel(modelClim[ 0 ]['Band1'][:]) >= nodata
            if wnodata.any():
                dhm[wnodata] = nodata
                dhmYearly[wnodata] = nodata
            wnodata = realClim[0,:,:].ravel() >= nodata
            if wnodata.any():
                dhm[wnodata] = nodata
                dhmYearly[wnodata] = nodata

            wtk = dhm > dhmYearly
            if wtk.any():
                dhmYearly[wtk] = dhm[wtk]

            # write output
            outfilename=os.path.join( outdir , '{0}{1}{2:02}.nc'.format(dhmRootName, iyear, imonth) )
            saveData(outfilename, dhm.reshape( (realClim[0].shape[0] , realClim[0].shape[1])  ), 'f', 'dhm', 1.e20, referenceGrid, 1, 'dhm', 'None', latAxis, lonAxis)
        #sys.exit()
        # all months done for this year    
        saveData( os.path.join( outdir , '{0}{1}.nc'.format(dhmRootName, iyear)), dhmYearly.reshape( (realClim[0].shape[0] , realClim[0].shape[1])  ), 'f', 'dhm', 1.e20, referenceGrid, 1, 'dhm', 'None', latAxis, lonAxis)

        # update frequency
        wtk = dhmYearly > 2
        if wtk.any():
            frequencyLvl2[wtk] = frequencyLvl2[wtk] + 1
        wnodata = numpy.ravel(modelClim[ 0 ]['Band1'][:]) >= nodata
        if wnodata.any():
            frequencyLvl2[wnodata] = -1
        wnodata = realClim[0,:,:].ravel() >= nodata
        if wnodata.any():
            frequencyLvl2[wnodata] = -1

    # save frequency
    saveData(os.path.join( outdir , '{0}{1}.nc'.format('frequency_lvl2_', yearList[0])), frequencyLvl2.reshape( (realClim[0].shape[0] , realClim[0].shape[1])  ), 'i', 'lvl2_freq', -1, referenceGrid, 1, 'dhm', 'None', latAxis, lonAxis)
    for ii in modelClim:
        ii.close()
# _______________
if __name__=="__main__":

    inhist='/data/cmip5/rcp/rcp8.5/toshist_ensemble/'
    modelClimatoRootName='climato_tos_1971_2000_' # climato 1980-2000 based on model output ensemble mean, make_tos_climato.sh
    #indir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
    indir='/data/cmip5/rcp/rcp8.5/tos4.5_ensemble/'

    sstRootName='modelmean_tos_' # ensemble mean of projection
    #outdir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
    outdir='/data/cmip5/rcp/rcp8.5/tos4.5_ensemble/'
    
    dhmRootName='dhm_'

    dekad=2050
    yearList=range(dekad, dekad+10)
    #yearList=range(2007, 2060)


    tmpdir='/data/tmp/'
    var='tos'

    realClimato='/data/sst/reynolds_climatology/noaa_oist_v2/resized_fitted/sst.ltm.1971-2000_resized.nc' # has continent=1.e20
    maxRealClimato='/data/sst/reynolds_climatology/noaa_oist_v2/resized_fitted/max_sst.ltm.1971-2000_resized.nc' # has continent=1.e20
    realClimRMSAtMaxSST='/data/sst/reynolds_climatology/noaa_oist_v2/resized_fitted/rms_at_maxsst_resized.nc' # has continent outline

    do_dhm(var, inhist, modelClimatoRootName, indir, sstRootName, realClimato, maxRealClimato, realClimRMSAtMaxSST, outdir, dhmRootName, yearList)
