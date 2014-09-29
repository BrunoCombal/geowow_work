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
import string

def dateTime2Year(datetime):
    result=[]
    for ii in datetime:
        result.append(ii.year)
    return(numpy.array(result), sorted(set(result)))

def makeOutfileName(infile, outdir, prefix, year):
    return('{0}/{1}_{2}_{3}.nc'.format(outdir,prefix,os.path.basename(infile)[:-17], year))

def writeToFileOne(outfilename, data):
    if os.path.exists(outfilename): os.remove(outfilename)
    print 'writing {0}'.format(os.path.basename(outfilename))
    outfile = cdms2.open(outfilename, 'w')
    outfile.write(data)
    outfile.history='Created with '+__file__.encode('utf8')
    outfile.close()

def writeToFile(outfilename, data1, data2):
    if os.path.exists(outfilename): os.remove(outfilename)
    print 'writing {0}'.format(os.path.basename(outfilename))
    outfile = cdms2.open(outfilename, 'w')
    outfile.write(data1)
    outfile.write(data2)
    outfile.history='Created with '+__file__.encode('utf8')
    outfile.close()

# reference grid for regridding
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

    return((cdms2.createGenericGrid(latAxis, lonAxis, lat_bnds, lon_bnds), latAxis, lonAxis, lat_bnds, lon_bnds, None, None))

def makeGrid4D():
    xstart=0
    xend=360
    xstep=0.5
    ystart=-85
    yend=85
    ystep=0.5

#	zlevels=[6, 17, 27, 37, 47, 57, 68.5, 82.5, 100, 122.5, 150, 182.5, 220, 262.5, 310, 362.5, 420, 485, 560, 645, 740, 845, 960, 1085]
    zlevels=[3.3, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500]
    lvl_bnds=[]
    for ii in range(0, len(zlevels)):
        if ii==0:
            xs = 0
        else:
            xs = 0.5 * ( zlevels[ii-1] + zlevels[ii] )
        if ii==(len(zlevels)-1):
            xe = zlevels[ii] + 0.5 * (zlevels[ii] - zlevels[ii-1])
        else:
            xe = 0.5 * ( zlevels[ii] + zlevels[ii+1] )
        lvl_bnds.append( [xs, xe] )

    zlevels=numpy.array(zlevels)
    lvl_bnds=numpy.array(lvl_bnds)
    print zlevels
    print lvl_bnds
    lvlAxis = cdms2.createAxis(zlevels, lvl_bnds)
    lvlAxis.units='m'
    lvlAxis.long_name='depth'
    lvlAxis.id='level'
    lvlAxis.designateLevel(True)

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

    return((cdms2.createGenericGrid(latAxis, lonAxis, lat_bnds, lon_bnds), latAxis, lonAxis, lat_bnds, lon_bnds, lvlAxis, lvl_bnds))
# ____________________________
def shiftGrid(infile, outfile, variable, latShift=0, lonShift=-280):

    if os.path.exists(outfile): os.remove(outfile)
    
    thisfile=cdms2.open(infile)

    thisLon = thisfile[variable].getLongitude()
    thisLon[:].data[:] = (thisLon[:].data[:] - lonShift)%360
    newvar = cdms2.createVariable(MV.array(thisfile[variable][:]), id=variable, fill_value=1.e20)
    newvar.setAxisList((thisfile[variable].getTime(), thisfile[variable].getLatitude(), thisLon))

    if os.path.exists(outfile): os.remove(outfile)
    outFile = cdms2.open(outfile,'w')
    outFile.write(newvar)
    thisfile.close()
    outFile.close()
    sys.exit(1)

# ____________________________
def monthlyRegrid(variable, variableType, indir, imodel, validYearList, outdir):

    largeMemory=False
    maxDepth=1000

    rgYYYYMM_Files={}

    pattern=re.compile('.*_BNU-ESM_.*') # problem on this grid: longitude shift of about 280degrees, to be corrected with shiftGrid function
    maskpattern = re.compile('.*EC-EARTH.*') # nodata was set to 273.15
    nodata=1.e20

    # for netcdf3: set flag to 0
    cdms2.setNetcdfShuffleFlag(1)
    cdms2.setNetcdfDeflateFlag(1)
    cdms2.setNetcdfDeflateLevelFlag(3)
    # get the reference grid
    if variableType=='4d':
        (referenceGrid, latAxis, lonAxis, latBounds, lonBounds, lvlAxis, lvl_bnds)=makeGrid4D()
        maxDepth = lvl_bnds.max()
    else:
        (referenceGrid, latAxis, lonAxis, latBounds, lonBounds, lvlAxis, lvl_bnds)=makeGrid()

    print 'maxDepth=',maxDepth

    lstInFile=[f for f in glob.glob('{0}/{1}*{2}*.nc'.format(indir, variable, imodel)) if os.stat(f).st_size ]  #files with non-nul size
    if lstInFile is None:
        print 'Error 1: no file to process for this model. Return'
        return(None)

    print indir, variable, imodel
    print lstInFile

    # loop over files, extract month, regrid it
    for ifile in lstInFile:
        thisfile=cdms2.open(ifile)

        var=cdms2.createVariable(thisfile[variable]) # needed if one want to update the mask (else read only variable)
		
        if maskpattern.match(os.path.basename(ifile)):	
            # mask pixels where there is no change (abs(change)<1.e4)
            refshape=var.shape
            tmp = numpy.reshape(var, (refshape[0], refshape[1] * refshape[2]) )
            wtnodata = (tmp.max(axis=0) - tmp.min(axis=0)) < 0.001
            if wtnodata.any():
                for ii in range(refshape[0]):
                    tmp[ii, wtnodata] = nodata
                var[:] = numpy.reshape(tmp, refshape)

        if largeMemory is True:
            # note: time reference is stored in the file name
            print 'Regridding file {0} ...'.format(ifile),
            if var.getLevel() is None:
                print '(t,y,x) ...',
                regridedAll = var.regrid(referenceGrid, missing=nodata)
            else:
                print '(t,z,y,x) ...',
                regridedXY = var.regrid(referenceGrid, missing=nodata)
                regridedAll = regridedXY.pressureRegrid(lvlAxis, method="log" )
                print 'done'

        for itime in var.getTime().asComponentTime():

            if itime.year in validYearList:

                if largeMemory is False:
                    if var.getLevel() is None:
                        thisVar = var.subRegion(time=itime)
                        regrided = thisVar.regrid(referenceGrid, missing=nodata)
                    else:
                        thisVar = var.subRegion(time=itime, level=(0, maxDepth))
                        regridedXY = thisVar.regrid(referenceGrid, missing=nodata)
                        regrided = regridedXY.pressureRegrid(lvlAxis, method="log")
                else:
                    regrided = regridedAll.subRegion(time=itime)

                outfilename='{0}/{1}_{2}{3:02}.nc'.format(outdir, os.path.basename(ifile)[:-17], itime.year, itime.month)
                if os.path.exists(outfilename): os.remove(outfilename)

                temp1 = cdms2.createVariable(regrided, typecode='f', id=variable, fill_value=nodata, grid=referenceGrid, copyaxes=1, attributes=dict(long_name=var.long_name, units=var.units) )
                if var.getLevel() is None:
                    temp1.setAxisList( (latAxis, lonAxis) )
                else:
                    continue
                    #temp1.setAxisList( (lvlAxis, latAxis, lonAxis) )

                writeToFileOne(outfilename, temp1)
                rgYYYYMM_Files[itime] = outfilename
 
        thisfile.close()

    return rgYYYYMM_Files
# _______________________________________
# monthly average: average models for the same YYYYMM
# compute model ensemble mean, max, min, std.
def monthlyAvg(variable, indir, outdir, minYear=2006, maxYear=2059):
    nodata=1.e20
    minVar=273.15 - 40
    maxVar=273.15 + 100
    unitsAvg=None
    # assume data are aligned
    pattern=re.compile('.*_BNU-ESM_.*') # problem on this grid (use shiftGrid to create a new version, discard this one).
    # maskpattern = re.compile('.*EC-EARTH.*') # nodate was set to 273.15
    
    # for netcdf3: set flags to 0
    cdms2.setNetcdfShuffleFlag(1)
    cdms2.setNetcdfDeflateFlag(1)
    cdms2.setNetcdfDeflateLevelFlag(3)

    print minYear, maxYear

    dateList=[]
    for iyear in range(minYear, maxYear+1):
        for imonth in range(1,13):
            dateList.append('{0}{1:02}'.format(iyear,imonth))

    for idate in dateList:
        print 'processing date ',idate
        # get list of files for this iyear, excluding one file:
        lstFiles = [f for f in glob.glob(indir+'/{0}_*{2}*_{1}.nc'.format(variable, idate,select)) if not pattern.match(f) ]
        print indir+'/{0}_*{2}*_{1}.nc'.format(variable, idate,select)

        if len(lstFiles) > 1:
            print 'Model ensemble mean for date {0} with {1} files'.format(idate, len(lstFiles))
            # accumulate data
            accumVar=None
            accumN=None

            for iFile in lstFiles:
                print 'processing file ', iFile
                thisFile = cdms2.open(iFile)
                dimVar = numpy.squeeze(thisFile[variable][:]).shape # remove time-single dimension if exists
                thisVar = numpy.ravel(thisFile[variable][:])
 
                if accumVar is None:
                    accumVar  = numpy.zeros( dimVar[0]*dimVar[1] ) + nodata
                    accumN    = numpy.zeros( dimVar[0]*dimVar[1] )
                    unitsAvg  = thisFile[variable].units
                    oneMatrix = numpy.ones(dimVar[0]*dimVar[1])
                    maxEnsemble = thisVar.copy()
                    minEnsemble = thisVar.copy()

                # add to accumVar if accumVar is not no-data, and incoming data are in the range
                wtadd = (thisVar >= minVar ) * (thisVar <= maxVar) * (accumVar < nodata)
                # if the value in accumVar is no-data, replace it.
                wtreplace = (thisVar >= minVar ) * (thisVar <= maxVar) * ( accumVar >= nodata)
                # min, max
                wmax = (thisVar >= maxEnsemble) * (thisVar < nodata) * (thisVar >= minVar) * (thisVar <= maxVar)
                wmaxReplace = (maxEnsemble >= nodata) * (thisVar < nodata) * (thisVar >= minVar)
                wmin = (thisVar <= minEnsemble) * (thisVar >= minVar) * (thisVar <= maxVar) * (maxEnsemble < nodata)
                wminReplace = (minEnsemble >= nodata) * (thisVar < nodata) * (thisVar >= minVar)
                if wtadd.any():
                    accumVar[wtadd] = accumVar[wtadd] + thisVar[wtadd]
                    accumN[wtadd] = accumN[wtadd] + oneMatrix[wtadd]
                if wtreplace.any():
                    accumVar[wtreplace] = thisVar[wtreplace]
                    accumN[wtreplace] = oneMatrix[wtreplace]
                if wmax.any():
                    maxEnsemble[wmax] = thisVar[wmax]
                if wmin.any():
                    minEnsemble[wmin] = thisVar[wmin]
                if wmaxReplace.any():
                    maxEnsemble[wmaxReplace] = thisVar[wmaxReplace]
                if wminReplace.any():
                    minEnsemble[wminReplace] = thisVar[wminReplace]

                thisFile.close()

            # now compute the average, where accumN is not 0
            wnz = accumN > 0
            average = numpy.zeros(dimVar[0] * dimVar[1]) + nodata
            if wnz.any():
                average[wnz] = accumVar[wnz] / accumN[wnz]

            # and let's compute the std
            std = numpy.zeros(dimVar[0] * dimVar[1]) + nodata
            stdN = numpy.zeros(dimVar[0] * dimVar[1])
            for iFile in lstFiles:
                thisFile = cdms2.open(iFile)
                thisVar = numpy.ravel(thisFile[variable][:])
                wtadd = (thisVar < nodata ) * (average < nodata ) * (thisVar >= minVar) * (thisVar <= maxVar) # average should be clean, no need to implement a 'replace'
                if wtadd.any():
                    std[wtadd] = (average[wtadd] - thisVar[wtadd]) * (average[wtadd] - thisVar[wtadd])
                    stdN[wtadd] = stdN[wtadd] + 1.0
                thisFile.close()

            wtstd = (stdN > 0) * (std < nodata)
            std[wtstd] = numpy.sqrt( std[wtstd]/stdN[wtstd] )

            # save to disk
            outfilename='{0}/modelmean_{1}_{2}.nc'.format(outdir, variable, idate)
            (referenceGrid, latAxis, lonAxis, latBounds, lonBounds) = makeGrid()
            avgOut = cdms2.createVariable(numpy.reshape(average,dimVar), typecode='f', id=variable, fill_value=1.e20, grid=referenceGrid, copyaxes=1, attributes=dict(long_name='model average for {0} at date {1}'.format(variable, idate), units=unitsAvg))
            avgOut.setAxisList((latAxis, lonAxis))

            accumOut = cdms2.createVariable(numpy.reshape(accumN,dimVar), typecode='i', id='count_{0}'.format(variable), fill_value=1.e20, grid=referenceGrid, copyaxes=1, attributes=dict(long_name='count of valid for {0} at date {1}'.format(variable, idate), units=None))
            accumOut.setAxisList((latAxis, lonAxis))

            maxEns = cdms2.createVariable(numpy.reshape(maxEnsemble,dimVar), typecode='f', id='max {0}'.format(variable), fill_value=1.e20, grid=referenceGrid, copyaxes=1, attributes=dict(long_name='max ensemble for {0} at date {1}'.format(variable, idate), units=unitsAvg))
            maxEns.setAxisList((latAxis, lonAxis))

            minEns = cdms2.createVariable(numpy.reshape(minEnsemble,dimVar), typecode='f', id='min {0}'.format(variable), fill_value=1.e20, grid=referenceGrid, copyaxes=1, attributes=dict(long_name='min ensemble for {0} at date {1}'.format(variable, idate), units=unitsAvg))
            minEns.setAxisList((latAxis, lonAxis))

            stdVar = cdms2.createVariable(numpy.reshape(std,dimVar), typecode='f', id='std_{0}'.format(variable), fill_value=1.e20, grid=referenceGrid, copyaxes=1, attributes=dict(long_name='model std for {0} at date {1}'.format(variable, idate), units=unitsAvg))
            stdVar.setAxisList((latAxis, lonAxis))

            if os.path.exists(outfilename): os.remove(outfilename)
            print 'saving to file ', outfilename
            outfile = cdms2.open(outfilename, 'w')
            outfile.write(avgOut)
            outfile.write(accumOut)
            outfile.write(minEns)
            outfile.write(maxEns)
            outfile.write(stdVar)
            outfile.history='Created with '+__file__.encode('utf8')
            outfile.close()
#___________________________
if __name__=="__main__":
    variable='thetao'
    variableType='4d'
    indir='/databis/cmip5_bis/rcp/rcp8.5/{0}/'.format(variable)
#    dirHistorical='/data/cmip5/rcp/tos_historical/'
    tmpdir='/home/bruno/Documents/tmp/newcode/{0}_monthly/'.format(variable)
#    tmpdirHist='/home/bruno/Documents/tmp/tos_hist/'
    outdir='/data/cmip5/rcp/rcp8.5/tos_ensemble/'
#    outdirHist='/data/cmip5/rcp/rcp8.5/toshist_ensemble/'

    if not os.path.exists(tmpdir): os.makedirs(tmpdir)
#    if not os.path.exists(tmpdirHist): os.makedirs(tmpdirHist)
	
    modelList=['ACCESS1-0','ACCESS1-3','bcc-csm1-1','bcc-csm1-1-m','BNU-ESM','CanCM4','CanESM2',
               'CCSM4','CESM1-BGC','CESM1-CAM5','CMCC-CM','CMCC-CMS','CNRM-CM5','CSIRO-Mk3-6-0','EC-EARTH','FIO-ESM','GFDL-CM2p1',
               'GFDL-CM3','GFDL-ESM2G','GFDL-ESM2M','GISS-E2-H','GISS-E2-H-CC','GISS-E2-R','GISS-E2-R-CC','HadCM3','HadGEM2-AO',
               'HadGEM2-CC','HadGEM2-ES','inmcm4','IPSL-CM5A-LR','IPSL-CM5A-MR','IPSL-CM5B-LR','MIROC5','MIROC-ESM','MPI-ESM-LR',
               'MPI-ESM-MR','MRI-CGCM3','NorESM1-M','NorESM1-ME']

    modelList=['ACCESS1-0']

    yearStart=2006
    yearEnd=2059
    validYearList=numpy.arange(yearStart, yearEnd+1)
    # for each model: compute its ensemble mean, min, max, std: keep them, delete grids
    for imodel in modelList:
        rgYYYYMM_Files = monthlyRegrid(variable, variableType, indir, imodel, validYearList, tmpdir) #returns a map: key=date, data=list of files
        interAvg='{0}/stats_{1}.nc'.format(outdir, imodel)
        #monthlyAvg_1file(variable, rgYYYYMM_Files, interAvg) # compute monthly avg, for each date, in a single file
        # clean up regrid files (saving space)

        print 'deleting'

#        for idate in rgYYYYMM_Files.keys():
#            print idate
#            for ifile in rgYYYYMM_Files[idate]:	os.remove(ifile)
            # compute mean of means
	
	

