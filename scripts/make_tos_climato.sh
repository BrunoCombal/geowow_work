#!/bin/bash

# \author Bruno Combal
# \date August 2013


indir=/data/cmip5/rcp/rcp8.5/toshist_ensemble
tmpdir=/data/tmp/make_tos_climato
rm -rf ${tmpdir}
mkdir -p ${tmpdir}

outdir=${indir}
rootName=modelmean_tos_
yearStart=1971 #1961
yearEnd=2000 #1990

for imonth in $(seq -w 1 12)
do
    lstFile=() # to empty the list
    for iyear in $(seq ${yearStart} ${yearEnd})
    do
	thisfile=${rootName}${iyear}${imonth}.nc
	lstFile=(${lstFile[@]} ${thisfile})
	# ncea accepts only netcdf3... let's transform the format
	gdal_translate -a_nodata 1.e20 -of netcdf -co "write_bottomup=no" -co "WRITE_LONLAT=YES"  HDF5:${indir}/${thisfile}://tos ${tmpdir}/${thisfile}
    done
    echo ${lstFile[@]}
    rm -f ${outdir}/climato_tos_${yearStart}_${yearEnd}_${imonth}.nc
    ncea -p ${tmpdir} ${lstFile[@]} ${outdir}/climato_tos_${yearStart}_${yearEnd}_${imonth}.nc
done