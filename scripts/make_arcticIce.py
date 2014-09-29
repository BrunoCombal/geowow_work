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
import matplotlib.pyplot
import matplotlib.dates as mdates
import colorsys

# define pairs of models and areas
# caution: in spite of what is written in some metainfo, some grids are taken from areacella not areacello
def getModelAreas():
    pairs=(['sit_OImon_ACCESS1-0', 'areacello_fx_ACCESS1-0_rcp85_r0i0p0.nc'],\
           ['sit_OImon_ACCESS1-3', 'areacello_fx_ACCESS1-3_rcp85_r0i0p0.nc'],\
           ['sit_OImon_bcc-csm1-1', 'areacello_fx_bcc-csm1-1_rcp85_r0i0p0.nc'],\
           ['sit_OImon_bcc-csm1-1-m', 'areacello_fx_bcc-csm1-1_rcp85_r0i0p0.nc'],\
           ['sit_OImon_BNU-ESM', ''],\
           ['sit_OImon_CanESM2', '../areacella/areacella_fx_CanESM2_historical_r0i0p0.nc'],\
           ['sit_OImon_CCSM4', 'areacello_fx_CCSM4_rcp85_r0i0p0.nc'],\
           ['sit_OImon_CESM1-BGC', 'areacello_fx_CESM1-BGC_rcp85_r0i0p0.nc'],\
           ['sit_OImon_CESM1-CAM5', 'areacello_fx_CESM1-CAM5_rcp85_r0i0p0.nc'],\
           ['sit_OImon_CESM1-WACCM', 'areacello_fx_CESM1-WACCM_rcp85_r0i0p0.nc'],\
           ['sit_OImon_CMCC-CESM', 'areacello_fx_CMCC-CESM_historical_r0i0p0.nc'], # see email
           ['sit_OImon_CMCC-CM_', 'areacello_fx_CMCC-CM_historical_r0i0p0.nc'], # see email
           ['sit_OImon_CMCC-CMS_', 'areacello_fx_CMCC-CMS_historical_r0i0p0.nc'], # see email
           ['sit_OImon_CNRM-CM5', 'areacello_fx_CNRM-CM5_rcp85_r0i0p0.nc'],\
           ['sit_OImon_CSIRO-Mk3-6-0', '../areacella/areacella_fx_CSIRO-Mk3-6-0_rcp85_r0i0p0.nc'], # not sure, see email
           ['sit_OImon_EC-EARTH', ''],\
           ['sit_OImon_FGOALS-g2', 'areacello_fx_FGOALS-g2_rcp85_r0i0p0.nc'],\
           ['sit_OImon_FIO-ESM', ''], #corrompu
           ['sit_OImon_GFDL-CM3', 'areacello_fx_GFDL-CM3_rcp85_r0i0p0.nc'],\
           ['sit_OImon_GFDL-ESM2G', 'areacello_fx_GFDL-ESM2G_rcp85_r0i0p0.nc'],\
           ['sit_OImon_GFDL-ESM2M', 'areacello_fx_GFDL-ESM2M_rcp85_r0i0p0.nc'],\
           ['sit_OImon_GISS-E2-H', '../areacella/areacella_fx_GISS-E2-H_rcp45_r0i0p0.nc'], # check again
           ['sit_OImon_GISS-E2-R', '../areacella/areacella_fx_GISS-E2-R_rcp45_r0i0p0.nc'], # check again
           ['sit_OImon_HadGEM2-AO', ''],\
           ['sit_OImon_HadGEM2-CC', 'areacello_fx_HadGEM2-CC_rcp85_r0i0p0.nc'],\
           ['sit_OImon_HadGEM2-ES', 'areacello_fx_HadGEM2-ES_rcp85_r0i0p0.nc'],\
           ['sit_OImon_inmcm4', 'areacello_fx_inmcm4_rcp85_r0i0p0.nc'],\
           ['sit_OImon_IPSL-CM5A-LR', ''],\
           ['sit_OImon_IPSL-CM5A-MR', 'areacello_fx_IPSL-CM5A-MR_rcp85_r0i0p0.nc'],\
           ['sit_OImon_IPSL-CM5B-LR', 'areacello_fx_IPSL-CM5B-LR_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MIROC5_', 'areacello_fx_MIROC5_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MIROC-ESM_', 'areacello_fx_MIROC-ESM_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MIROC-ESM-CHEM_', 'areacello_fx_MIROC-ESM-CHEM_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MPI-ESM-LR', 'areacello_fx_MPI-ESM-LR_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MPI-ESM-MR', 'areacello_fx_MPI-ESM-MR_rcp85_r0i0p0.nc'],\
           ['sit_OImon_MRI-CGCM3', 'areacello_fx_MRI-CGCM3_rcp85_r0i0p0.nc'],\
           ['sit_OImon_NorESM1-M_', 'areacello_fx_NorESM1-M_rcp85_r0i0p0.nc'], # email
           ['sit_OImon_NorESM1-ME', 'areacello_fx_NorESM1-M_rcp85_r0i0p0.nc'], #email
           ['sit_OImon_SP-CCSM4', 'areacello_fx_CCSM4_rcp85_r0i0p0.nc']\
)
    return (pairs)
# __________________________
# create a list of N colors
def do_createColors(N):
    HSV_tuples = [(x*1.0/N, 0.5, 0.5) for x in range(N)]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)

    return RGB_tuples
# ___________________________
def do_date2float(stringDate):
    yS, mS, dS = stringDate.split('-')
    return int(yS), int(mS), int(dS), (float(yS)*10000 + 100*float(mS)/12 + float(dS)/31. )/10000
# ___________________________
def doAreaIce(indir, model, variable, areacello):

    print 'processing model ',model

    lstFiles=glob.glob('{0}/{1}*.nc'.format(indir, model))

    areaH = cdms2.open(areacello)
    if 'areacello' in areaH.variables.keys():
        areaVar='areacello'
    elif 'areacella' in areaH.variables.keys():
        areaVar='areacella'
    areashape = areaH[areaVar].shape # lat, lon
    area = numpy.ravel(areaH[areaVar][:][0.5*areashape[0]:, :])

    nodata = 1.e20
    minIce = 0
    csvData = []
    for ifile in lstFiles:
        experiment = os.path.basename(ifile).rsplit('_')[-2]
        print 'file: ',ifile, experiment
        thisFile = cdms2.open(ifile)
        thisShape = thisFile[variable][:].shape # time, lat, lon
        if (thisShape[1] != areashape[0]) or (thisShape[2] != areashape[1]):
            print '!!!! no correspondance for ', model, ifile, areacello
            print thisShape, areashape
            return []
        timeAxis = thisFile[variable].getTime()

        for itime in timeAxis.asComponentTime()[:]:
            tmp = thisFile[variable].subRegion(time=itime)
            thisVar = numpy.ravel(tmp[:, 0.5*areashape[0]:, :])

            # global ice
            wice = (thisVar < nodata) * (thisVar > minIce) * (area < nodata)
            total = numpy.sum(area[wice]) * 1.e-6 * 1.e-6 # in millions of km2
            csvData.append([itime.year, itime.month, itime.day, total, model, experiment])

        thisFile.close()

    return csvData
# _______________________________
def do_drawArticArea(filename, relative=True):

    # definition
    if relative==True:
        titleStr='Area relative to 2006'
    else:
        titleStr='Areas (millions km2)'

    # read file
    CSV = []
    f = open(filename, 'r')
    for line in f.readlines():
        CSV.append(line.replace('\n','').split(','))
    f.close()

    # list of models
    fig = matplotlib.pyplot.figure()
    figure = fig.add_subplot(111)

    listPairs=getModelAreas()
    # 1 color per model
    listColors = do_createColors(len(listPairs))

    for iP in listPairs:
        areas = []
        dates = []
        dataList=[]
        
        for ii in CSV:
            if ii[0] == iP[0]: # model, year, month, day, SIT
                #dateSplitted = do_date2float(ii[1])
                #if dateSplitted[1] == 9: # keep only September
                if int(ii[2]) == 9 and int(ii[1])<=2100:
                    dataList.append( (int(ii[1]), float(ii[4]), ii[5]) )
                   # dates.append(int(ii[1]))
                   # areas.append(float(ii[4]))
                   # exper.append(ii[5])

        # now sort by chrono order
        dataList = sorted(dataList, key=lambda x: x[0])
    
        if len(dataList) > 0:
            if relative==True:
                listExp = sorted(set( ii[2] for ii in dataList))
                for ixp in listExp:
                    thisArea = [ ii[1] for ii in dataList if ii[2]==ixp]
                    thisYear = [ ii[0] for ii in dataList if ii[2]==ixp]

                    relareas = numpy.array(thisArea)/thisArea[0]

                    if relareas.max()==relareas.min():
#                        print 'no change', iP, ixp
                        continue
                    else:
                        figure.plot( thisYear, relareas, linestyle='None', marker='.', color=listColors[listPairs.index(iP)])
                        #print '{{name:\'{0}{1}\', id:\'{2}\', data:['.format(iP[0], ixp, (iP[0]+ixp)),
                        print iP[0], ixp,
                        for (idate, ival) in zip(thisYear, relareas):
                            #print '[{0}, {1:.4f}],'.format(idate, ival),
                            print ival,
                        #print '], lineWidth:0, marker:{lineWidth:0, symbol:\'circle\'}'
                        print
                        if ixp != listExp[0]:
                            #print ',linkedTo:\'{0}\''.format((iP[0]+ixp))
                            #print ', visible:false},'
                            continue
            else:
                figure.plot( dates, areas, linestyle='None', marker='.', color=listColors[listPairs.index(iP)] )

#    for ii in listColors:
#        print hex(int(ii[0]*255)), hex(int(ii[1]*255)), hex(int(ii[2]*255))

    figure.set_ylabel(titleStr)
    figure.set_xlabel('date')
    figure.set_title('Artic sea ice surface (RCP=8.5)')
    #figure.axis([2000, 2100, 0, 2])
    fig.savefig('/home/bruno/Documents/matplot/artic.png')

# _____________________________
# go through the list of files
# for each file, output (csv)
# modelname, date, articsurface
if __name__=="__main__":
    sitDir='/data/cmip5/rcp/rcp8.5/new_sit'
    areacelloDir='/data/cmip5/rcp/rcp8.5/areacello'
    csvFilename = '/home/bruno/Documents/tmp/arcticIce.csv'
    variable='sit'

    if 1==0:
        modelsArea = getModelAreas()

        if os.path.exists(csvFilename): os.remove(csvFilename)
        csvFile = open(csvFilename,"w")

        for iMA in modelsArea:
            if not iMA[1]=='':
                dataToWrite = doAreaIce(sitDir, iMA[0], variable, '{0}/{1}'.format(areacelloDir, iMA[1]))
                for ii in dataToWrite:
                    csvFile.write('{4}, {0}, {1}, {2}, {3}, {5}\n'.format(ii[0], ii[1], ii[2], ii[3], ii[4], ii[5]))
        csvFile.close()

    if 1==1:
        do_drawArticArea(csvFilename)
