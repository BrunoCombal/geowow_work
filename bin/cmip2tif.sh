#!/bin/bash
# author, Bruno Combal, IOC/UNESCO
# date, 2013, September

indir=/data/cmip5/rcp/rcp8.5/tos4.5_ensemble
tmpdir=/data/tmp/cmip2tif
mkdir -p ${tmpdir}
outdir=/data/cmip5/rcp/lauretta_rcp4.5_tif
mkdir -p ${outdir}

fileLst=($(find ${indir} -name 'frequ*nc' -type f ! -size 0 -printf '%f\n'))
ncdfType='NETCDF'
dataPath='lvl2_freq'

#fileLst=($(find ${indir} -name 'dhm_*nc' -type f ! -size 0 -printf '%f\n'))
#ncdfType='NETCDF' #could be 'HDF5'
#dataPath='dhm' # could be '//dhm'


for ii in ${fileLst[@]}
do
    thisfile=${indir}/${ii}
    tmpfile=${tmpdir}/cmip2tif_${RANDOM}.nc
    # convert to geotiff
    gdal_translate -of netcdf -co "write_bottomup=no" -co "write_lonlat=yes"  ${ncdfType}':"'${thisfile}'":'${dataPath} ${tmpfile}
    # append srs and bbox
    gdal_translate -of gtiff -co "compress=lzw" -a_srs 'EPSG:4326' -a_ullr 0 85 360 -85 ${tmpfile} ${outdir}/${ii##*/}.tif
    rm ${tmpfile}
done

rm -rf ${tmdir}