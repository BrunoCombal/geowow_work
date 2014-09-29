#!/bin/bash

## \author Bruno Combal
## \date March 2013

## reads a netcdf(tos), for each of its dates:
## keep only SST>28°C
## generate the contour, for each degree, output in a shp

function mktmpdir(){
    tmpRoot=$HOME/Documents/tmp
    tmpDir=${tmpRoot}/${0##*/}_${RANDOM}_${RANDOM}
    while [ -d ${tmpDir} ]
    do
	tmpDir=${tmpRoot}/${0##*/}_${RANDOM}_${RANDOM}
    done
    mkdir -p ${tmpDir}
    echo ${tmpDir}
}

source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh

variable='tos'
rcp='rcp8.5'
inDir=/data/cmip5/rcp/${rcp}/${variable}
bindir=/home/bruno/Documents/dev/codes/bin
outDir=/data/cmip5/rcp/${rcp}/${variable}_warmpools
mkdir -p ${outDir}
tmpDir=$(mktmpdir)
tosLIM=$(echo "scale=2; 28.75 + 273.15" | bc)

lstFiles=($(find ${inDir} -name ${variable}'*.nc' -type f ! -size 0 -printf '%f\n' ))

for ifile in ${lstFiles[@]}
do
    echo "Processing file "$file
    # set to 0 any temperature lower that the threshold
    echo "detecting warm pools"
    ncap2 -o ${tmpDir}/tmpmask_${ifile} -s 'warmpool = tos * (tos > '${tosLIM}')' ${inDir}/${ifile}
    # and remove tos to save disk space and avoid excessively big files
    echo "removing useless dimensions"
    ncks -x -v tos -o ${tmpDir}/mask_${ifile} ${tmpDir}/tmpmask_${ifile}
    rm -f ${tmpDir}/tmpmask_${ifile}
    # compute min every 12 months
    echo "annual min"
    ncea -y min -o ${tmpDir}/min_mask_${ifile} -d time,,12
    # warmpool definition
    echo "warmpool definition"
    ncap2 -o ${tmpDir}/tmpdef_${ifile} -s 'warmpooldef = warmpool > 0 ' ${tmpDir}/min_mask_${ifile}
    # keep only values where min!=0 (i.e. temperature is never below 301.15)
    
    # regrid
    echo "regridding warmpool definition"
    ${binDir}/regrid.py -o ${outDir}/warmpoolDef_${ifile} -v 'warmpooldef' ${tmpDir}/min_mask_${ifile}
    echo "regridding warmpool min temp"
    ${binDir}/regrid.py -o ${outDir}/warmpoolMinTemp_${ifile} -v 'warmpool' ${tmpDir}/mask_${ifile}
done

# \rm -rf ${tmpDir}

## EOF




exit





# get list of models
modelList=(tos_Omon_CMCC-CM_rcp85_r1i1p1)

for imodel in ${modelList[@]}
do
    subfileList=$(ls ${inDir}/${imodel}*.nc)
    for isubmodel in ${subfileList[@]}
    do
	inputFile=${inDir}/${isubmodel##*/}
	outFile=${outDir}/regrid_${isubmodel##*/}
        ${bindir}/regrid.py -o ${outFile} -v tos  ${inputFile}
   
	

	nbands=1 #$(gdalinfo ${outDir}/filtered_${infile%.nc}.tif | grep Band | wc -l)
	for ((ii=1; ii<=$nbands; ii=ii+1))
	do
	    echo
#	    gdal_contour -b ${ii} -inodata 1.e20 -snodata 1.e20 -i 1  ${outDir}/regrid_${infile%.nc}.tif $outDir/${ii}_${infile%.nc}.shp
	done
    done
done