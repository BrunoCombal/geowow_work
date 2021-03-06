#!/bin/bash

## \author Bruno Combal
## \date February 2013
## \brief Converts ACE2 tiles into a single mosaic
## date source: http://tethys.eaprs.cse.dmu.ac.uk/ACE2/shared/webdownload_3secs
## hdr reference: http://tethys.eaprs.cse.dmu.ac.uk/ACE2/shared/reading_ace2
## gdal directly support this format: http://www.gdal.org/frmt_various.html

dataDir=/data/dem/ace2
tmpDir=/data/dem/ace2/tmp
rm -rf ${tmpDir}
mkdir -p ${tmpDir}
outDir=/data/dem/ace2/mosaic
mkdir -p ${outDir}
outFile=${outDir}/mosaic_ace2.tif

function dumpHdr(){
    lat=$1
    lon=$2
    ps=$3
    echo "ENVI"
    echo "description = {"
    echo "  File Imported into ENVI.}"
    echo "samples = 18000"
    echo "lines   = 18000"
    echo "bands   = 1"
    echo "header offset = 0"
    echo "file type = ENVI Standard"
    echo "data type = 4"
    echo "interleave = bsq"
    echo "sensor type = Unknown"
    echo "byte order = 0"
    echo "wavelength units = Unknown"
}

for ((ilon=-180; ilon<=180; ilon+=15))
do
    for ((ilat=-90; ilat<=90; ilat+=15))
    do
	if [ ${ilon} -lt 0 ]; then
	    ilonTxt=$(printf "%03dW" $((-ilon)))
	else
	    ilonTxt=$(printf "%03dE" ${ilon})
	fi
	if [ ${ilat} -lt 0 ]; then
	    ilatTxt=$(printf "%02dS" $((-ilat)))
	else
	    ilatTxt=$(printf "%02dN" $((ilat)))
	fi

	fname=${ilatTxt}${ilonTxt}_3S.ACE2.gz
	fnamePath=${dataDir}/${fname}

	if [[ -e ${fnamePath} ]]; then
	    # gunzip
	    gunzip -c ${fnamePath} > ${tmpDir}/${fname%.gz}
	    # create a hdr: don't use: gdal guess coordinates from filename
	    #dumpHdr $ilon $ilat > ${tmpDir}/${fname%.gz}.hdr
	    gdal_translate -of gtiff -co "compress=lzw" ${tmpDir}/${fname%.gz} ${tmpDir}/${fname%.gz}.tif
	    rm -f ${tmpDir}/${fname%.gz}
	    lstfile=(${lstfile[@]} ${tmpDir}/${fname%.gz})
	else
	    echo $fname is missing
	fi

    done
done


gdal_merge.py -o ${outFile} -of gtiff -co "compress=lzw" ${lstfile[@]} 
	    