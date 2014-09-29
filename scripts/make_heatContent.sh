#!/bin/bash

## \author Bruno Combal
## \date March 2013

srcDir=/home/bruno/Documents/dev/codes/
binDir=${srcDir}/bin
dataDir=/data/cmip5/rcp/rcp8.5/thetao/
rhoDir=/data/cmip5/rcp/rcp8.5/rhopoto
rootfile=thetao_Omon_CCSM4_rcp85_r1i1p1_
rhorootfile=rhopoto_Omon_CCSM4_rcp85_r1i1p1_
outDir=/data/tmp/

years=(2006 2010 2020 2030 2040 2050 2060 2070 2080 2090)
years=(2010 2020 2030 2040 2050 2060 2070 2080 2090)

for iy in ${years[@]}
do
    infile=$(find ${dataDir} -type f ! -size 0 -name "${rootfile}${iy}*nc")
    rhofile=$(find ${rhoDir} -type f ! -size 0 -name "${rhorootfile}${iy}*nc")
    timeFrame=$(echo ${infile##*/} | sed "s/${rootfile}//" | sed 's/\.nc//')
    echo "Time Frame: "${timeFrame}
    ${srcDir}/indicators/heatContent.py -o ${outDir}/${timeFrame}_HC.tif -of gtiff -co "compress=lzw" -v thetao -frho ${rhofile} -ftheta ${infile}
    if [[ $? -ne 0 ]]; then
	echo "processing tchp.py failed; Exit."
	exit
    fi
    ${binDir}/max_yearly.py -o ${outDir}/${timeFrame}_max_HC.tif ${outDir}/${timeFrame}_HC.tif
done