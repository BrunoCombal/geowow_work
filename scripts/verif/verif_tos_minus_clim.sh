#!/bin/bash

# we test here model ensemble mean minus its climato

modelClimatoRootName=climato_tos_1971_2000_
climatoDir=/data/cmip5/rcp/rcp8.5/toshist_ensemble/
inhist=/data/cmip5/rcp/rcp8.5/toshist_ensemble/
#inhist=/data/cmip5/rcp/rcp8.5/tos_ensemble
tmpdir=/data/tmp/verif
mkdir -p $tmpdir
bindir=/home/bruno/Documents/dev/codes/bin
rootTestFile=dif_model_modelClim_
startYear=1971
endYear=2005

finalFile=${tmpdir}/stack_model_climato_${startYear}_${endYear}.nc

# compute in separate YYYYMM
lstFile=()
for iyear in $(seq $startYear $endYear)
do
    for imonth in $(seq -w 1 12)
    do
	thisSST=${tmpdir}/tmpmodelmean_tos_${iyear}${imonth}.nc
	thisSSTin=${inhist}/modelmean_tos_${iyear}${imonth}.nc
	gdal_translate -a_nodata 1.e20 -of netcdf -co "write_bottomup=no" -co "WRITE_LONLAT=YES"  HDF5:${thisSSTin}://tos ${thisSST}


	thisClimato=${climatoDir}/${modelClimatoRootName}${imonth}.nc

	outfile=${tmpdir}/${rootTestFile}${iyear}${imonth}.nc

	# thisSST - climatoSameMonth
	if [ -e ${outfile} ]; then
	    \rm ${outfile}
	fi
	ncbo -o ${outfile} -y diff ${thisSST} ${thisClimato}
	lstFile=(${lstFile[@]} ${outfile##*/})
	
    done
done

# layer stack the result
ncecat -o ${finalFile} -p ${tmpdir} ${lstFile[@]}

# clean tmp file