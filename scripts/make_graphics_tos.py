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
import matplotlib.pyplot as plt

def figureTOS(type='single'):

    excludePattern=re.compile('._BNU-ESM_*')
    listModels=('ACCESS1-0_rcp85_r1i1p1', 'ACCESS1-3_rcp85_r1i1p1', 'bcc-csm1-1-m_rcp85_r1i1p1',\
                    'bcc-csm1-1_rcp85_r1i1p1', 'CanESM2_rcp85_r1i1p1',\
                    'CanESM2_rcp85_r2i1p1', 'CanESM2_rcp85_r3i1p1', 'CanESM2_rcp85_r4i1p1',\
                    'CanESM2_rcp85_r5i1p1', 'CCSM4_rcp85_r1i1p1', 'CCSM4_rcp85_r2i1p1', 'CCSM4_rcp85_r3i1p1',\
                    'CCSM4_rcp85_r4i1p1', 'CCSM4_rcp85_r5i1p1', 'CCSM4_rcp85_r6i1p1', 'CESM1-BGC_rcp85_r1i1p1',\
                    'CESM1-CAM5_rcp85_r1i1p1', 'CESM1-CAM5_rcp85_r2i1p1', 'CESM1-CAM5_rcp85_r3i1p1',\
                    'CESM1-WACCM_rcp85_r2i1p1', 'CESM1-WACCM_rcp85_r3i1p1', 'CESM1-WACCM_rcp85_r4i1p1',\
                    'CMCC-CESM_rcp85_r1i1p1', 'CMCC-CM_rcp85_r1i1p1', 'CMCC-CMS_rcp85_r1i1p1', 'CNRM-CM5_rcp85_r10i1p1',\
                    'CNRM-CM5_rcp85_r1i1p1', 'CNRM-CM5_rcp85_r2i1p1', 'CNRM-CM5_rcp85_r4i1p1',\
                    'CNRM-CM5_rcp85_r6i1p1', 'CSIRO-Mk3-6-0_rcp85_r10i1p1', 'CSIRO-Mk3-6-0_rcp85_r1i1p1',\
                    'CSIRO-Mk3-6-0_rcp85_r2i1p1', 'CSIRO-Mk3-6-0_rcp85_r3i1p1', 'CSIRO-Mk3-6-0_rcp85_r4i1p1',\
                    'CSIRO-Mk3-6-0_rcp85_r5i1p1', 'CSIRO-Mk3-6-0_rcp85_r6i1p1', 'CSIRO-Mk3-6-0_rcp85_r7i1p1',\
                    'CSIRO-Mk3-6-0_rcp85_r8i1p1', 'CSIRO-Mk3-6-0_rcp85_r9i1p1', 'EC-EARTH_rcp85_r10i1p1',\
                    'EC-EARTH_rcp85_r11i1p1', 'EC-EARTH_rcp85_r12i1p1', 'EC-EARTH_rcp85_r14i1p1',\
                    'EC-EARTH_rcp85_r1i1p1', 'EC-EARTH_rcp85_r2i1p1', 'EC-EARTH_rcp85_r3i1p1', 'EC-EARTH_rcp85_r6i1p1',\
                    'EC-EARTH_rcp85_r7i1p1', 'EC-EARTH_rcp85_r8i1p1', 'EC-EARTH_rcp85_r9i1p1', 'FIO-ESM_rcp85_r1i1p1',\
                    'FIO-ESM_rcp85_r2i1p1', 'FIO-ESM_rcp85_r3i1p1', 'GFDL-CM3_rcp85_r1i1p1', 'GFDL-ESM2G_rcp85_r1i1p1',\
                    'GFDL-ESM2M_rcp85_r1i1p1', 'GISS-E2-H_rcp85_r1i1p1', 'GISS-E2-H_rcp85_r1i1p2', 'GISS-E2-H_rcp85_r1i1p3',\
                    'GISS-E2-R_rcp85_r1i1p1', 'GISS-E2-R_rcp85_r1i1p2', 'GISS-E2-R_rcp85_r1i1p3', 'HadGEM2-AO_rcp85_r1i1p1',\
                    'HadGEM2-CC_rcp85_r1i1p1', 'HadGEM2-CC_rcp85_r2i1p1', 'HadGEM2-CC_rcp85_r3i1p1', 'HadGEM2-ES_rcp85_r1i1p1',\
                    'HadGEM2-ES_rcp85_r2i1p1', 'HadGEM2-ES_rcp85_r3i1p1', 'HadGEM2-ES_rcp85_r4i1p1', 'inmcm4_rcp85_r1i1p1',\
                    'IPSL-CM5A-LR_rcp85_r1i1p1', 'IPSL-CM5A-LR_rcp85_r2i1p1', 'IPSL-CM5A-LR_rcp85_r3i1p1',\
                    'IPSL-CM5A-LR_rcp85_r4i1p1', 'IPSL-CM5A-MR_rcp85_r1i1p1', 'IPSL-CM5B-LR_rcp85_r1i1p1', 'MIROC5_rcp85_r1i1p1',\
                    'MIROC5_rcp85_r2i1p1', 'MIROC5_rcp85_r3i1p1', 'MPI-ESM-LR_rcp85_r1i1p1', 'MPI-ESM-LR_rcp85_r2i1p1',\
                    'MPI-ESM-LR_rcp85_r3i1p1', 'MPI-ESM-MR_rcp85_r1i1p1', 'MRI-CGCM3_rcp85_r1i1p1', \
                    'NorESM1-ME_rcp85_r1i1p1', 'NorESM1-M_rcp85_r1i1p1')

    indir='/data/cmip5/rcp/rcp8.5/tos_ensemble'
    filerootname='modelmean'
    variable='tos'
    pickMonth=6
    monthName=['January','February','March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    yx=(150,380) # tropical, pacific
    yx=(254, 302) # Western subartic gyre (above Kuroshio extension)
    yx=(227, 350) # away from Kuroshio, 175E, 66.5N
    #yx=( (85-54)*2, 50*2) # south pacific, close to artic
    #yx=((48+85)*2, 335*2) # North atlantic gyre
    yx=((85-40)*2, 20*2) # Agulhas
    latitude=yx[0]/2. - 85
    latSN='N'
    if latitude<0: latSN='S'
    lonEW='E'
    longitude=yx[1]/2
    if longitude<0: lonEW='W'
    title=u'{4} SST, ({0}\N{DEGREE SIGN}{1}, {2}\N{DEGREE SIGN}{3})'.format(longitude, lonEW,\
                                                                                latitude,\
                                                                                latSN, monthName[pickMonth-1])

    dateList=[]
    xpos=[]
    for year in range(2010,2050+1):
        for month in range(pickMonth,12+1,12):
            dateList.append('{0}{1:02}'.format(year, month))
            xpos.append(year + (month-1)/12.)

    tosSeries=[]
    tosMaxSeries=[]
    tosMinSeries=[]
    tosStdSeries=[]
    for idate in dateList:
        thisFile=cdms2.open('{0}/{1}_{2}_{3}.nc'.format(indir, filerootname, variable, idate))
        tosSeries.append(thisFile[variable][:][yx])
        tosMaxSeries.append(thisFile['max tos'][:][yx])
        tosMinSeries.append(thisFile['min tos'][:][yx])
        tosStdSeries.append(thisFile['std_tos'][:][yx])
        thisFile.close()

    # initialise figure
    fig = plt.figure()
    figure = fig.add_subplot(111)
  
    if type=='all':
        for imod in listModels:
            print imod
            data=[]
            for idate in dateList:
                filename = '/home/bruno/Documents/tmp/tos_monthly/tos_Omon_{0}_{1}.nc'.format(imod,idate)
            
                if not excludePattern.match(filename):
                    thisFile = cdms2.open(filename)
                    var =  thisFile[variable][:].data[:]
                    data.append( var[0, yx[0], yx[1]] )
                    thisFile.close()
#            print numpy.array(data).max(), numpy.array(data).min(), numpy.array(data).sum()/float(len(data))
            thisxpos= numpy.array(xpos)+ 2/12.0
            figure.plot(thisxpos, data, linestyle='None', color='0.8', linewidth=0.5, marker='x')


    # overlay average
    figure.plot(xpos, tosSeries, color='blue', linestyle='-', linewidth=1)
    figure.plot(xpos, tosMaxSeries, color='red')
    figure.plot(xpos, tosMinSeries, color='green')
    # standard deviation
    for ii in range(len(tosSeries)):
        figure.plot( (xpos[ii], xpos[ii]), (tosSeries[ii]-tosStdSeries[ii], tosSeries[ii]+tosStdSeries[ii]) , color='red', linestyle='-', linewidth=2)

  # once everything is plotted, update the celsius range
    y1, y2 = figure.get_ylim()
    x1, x2=figure.get_xlim()
    ax2=figure.twinx()
    ax2.set_ylim(y1-273.15, y2-273.15)
    ax2.set_yticks(range(int(y1-273.15), int(y2-273.15)+1), 2)
    ax2.set_ylabel('Celsius')
    ax2.set_xlim(x1,x2)

    figure.set_title(title)
    figure.set_ylabel('Surface temperature (K)')
    figure.set_xlabel('date')
    plt.savefig('/home/bruno/Documents/matplot/tos.png')

    print 'A total of {0} models.'.format(len(listModels))

# _______________________________
def figureDHM():
    
    pass
# _______________________________
if __name__=="__main__":
    
    figureTOS('all')

    #figureDHM()
