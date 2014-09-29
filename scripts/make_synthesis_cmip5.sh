#!/bin/bash

## \author Bruno Combal
## \date February 2013
## compute mean, max, min and std profiles of a file list of time series[time, lon, lat].
## The result is a profile [time, lon, lat]

srcDir=/home/bruno/Documents/dev/codes/
binDir=${srcDir}/bin

timeFrame='200601-210012'
rcp=8.5
variable='zos'

dataDir=/data/cmip5/rcp/rcp${rcp}/${variable}
tmpDir=/data/tmp
mkdir -p ${tmpDir}
operators=('avg') # operators for ncea
singleoperators=('avg') # in case of a single file, some operators like rms would make no sense here


lstGroup=($(find ${dataDir} -name "${variable}*${timeFrame}*.nc" | sed 's/r[0-9]\{1,2\}i[0-9]\{1,2\}p[0-9]\{1,2\}.*nc//g' | sed 's/.*\///g' | sed 's/_$//' | sort | uniq))

# first operation: reduce the total amount of data
# grouping by families or r{}l{}p{}
for ii in ${lstGroup[@]}
do
    # get files for this group
    lstFile=($(find ${dataDir} -name "$ii*${timeFrame}*nc"))
    echo "found ${#lstFile[@]} files for $ii"
    if [[ ${#lstFile[@]} -eq 1 ]]; then

	for iop in ${singleoperators[@]}
	do
	    opresult=${tmpDir}/${iop}_${ii}_${timeFrame}.nc # result of the operator
	    resample=${tmpDir}/resample_${iop}_${ii}_${timeFrame}.tif
	    echo "${iop} :: copy single file --> " ${opresult}
	    cp -f ${lstFile[@]} ${opresult}
	    echo ${lstFile[0]} > ${opresult}.txt
	    ${binDir}/regrid.py -nodata 1.e20 -of hfa -co "compress=yes" -v ${variable} -o ${resample} ${opresult}
	    # rm -f ${opresult}
	done
	
    else

	for iop in ${operators[@]}
	do
	    opresult=${tmpDir}/${iop}_${ii}_${timeFrame}.nc # result of the operator
	    resample=${tmpDir}/resample_${iop}_${ii}_${timeFrame}.img
	    echo "${iop} --> " ${opresult}
	    rm -f ${opresult} #delete preceding result, if any
	    ncea -y ${iop} -o ${opresult} ${lstFile[@]} # compute the result for this operator
	    rm -f ${opresult}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${opresult}.txt; done
	    ${binDir}/regrid.py -nodata 1.e20 -of hfa -co "compress=yes" -v ${variable} -o ${resample} ${opresult}
	    # rm -f ${opresult}
	done

#	meanFile=${tmpDir}/mean_${ii}_${timeFrame}.nc
#	maxFile=${tmpDir}/max_${ii}_${timeFrame}.nc
#	minFile=${tmpDir}/min_${ii}_${timeFrame}.nc
#	rmsFile=${tmpDir}/rms_${ii}_${timeFrame}.nc
#	ttlFile=${tmpDir}/ttl_${ii}_${timeFrame}.nc

	# dans le cas MIRC, il faut que les series '0' (ou les constantes) soient mises à nodata
	# test: si pas de 1.e20 -> rechercher les series constantes, et les mettre à 1.e20
	# A faire avant toute interpolation

#	echo "mean --> " ${meanFile}
#	rm -f ${meanFile}
#	ncea -o ${meanFile}  ${lstFile[@]}
#	rm -f ${meanFile}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${meanFile}.txt; done
#	${binDir}/regrid.py -v ${variable} -o ${meanFile%/*}/resample_${meanFile##*/}.tif ${meanFile}

#	echo "max --> " ${maxFile}
#	rm -f ${maxFile}
#	ncea -y max -o ${maxFile} ${lstFile[@]}
#	rm -f ${maxFile}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${maxFile}.txt; done
#	${binDir}/regrid.py -v ${variable} -o ${maxFile%/*}/resample_${maxFile##*/}.tif ${maxFile}

#	echo "min --> " ${minFile}
#	rm -f ${minFile}
#	ncea -y min -o ${minFile} ${lstFile[@]}
#	rm -f ${minFile}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${minFile}.txt; done
#	${binDir}/regrid.py -v ${variable} -o ${minFile%/*}/resample_${minFile##*/}.tif ${minFile}

#	echo "rms --> " ${rmsFile}
#	rm -f ${rmsFile}
#	ncea -y rms -o ${rmsFile} ${lstFile[@]}
#	rm -f ${rmsFile}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${rmsFile}.txt; done
#	${binDir}/regrid.py -v ${variable} -o ${rmsFile%/*}/resample_${rmsFile##*/}.tif ${rmsFile}

#	echo "ttl --> " ${ttlFile}
#	ncea -o ${ttlFile}  ${lstFile[@]}
#	rm -f ${ttlFile}.txt; for jj in ${lstFile[@]}; do echo $jj >> ${ttlFile}.txt; done
#	${binDir}/regrid.py -v ${variable} -o ${ttlFile%/*}/resample_${ttlFile##*/}.tif ${ttlFile}

    fi
done