#!/bin/bash

# \author Bruno Combal, IOC, UNESCO
# \date September 2013

# data source: ftp.emc.ncep.noaa/cmb/sst/oimonth_v2
# web page: www.emc.ncep.noaa.gov/research/cmb/sst_analysis

indir=/data/sst/oimonth_v2
tmpdir=/data/tmp/oimonth_v2
rm -rf ${tmpdir}
mkdir -p ${tmpdir}
bindir=/home/bruno/Documents/dev/codes/bin
rootname=oiv2mon
outdir=/data/sst/oimonth_v2/

# compute std for each month
for imonth in $(seq -w 1 12)
do
    echo "unzipping files for month "${imonth}
    # gunzip to ${tmpdir}
    for ifile in $(find ${indir} -type f ! -size 0 -name "${rootname}.????${imonth}.gz" )
    do
	binfile=$(xx=${ifile##*/}; echo ${xx%.gz})
	cp ${ifile} ${tmpdir}
	gunzip ${tmpdir}/${ifile##*/}
	${bindir}/bin2nc.py -o ${tmpdir}/${binfile}.nc ${tmpdir}/${binfile}
    done

    ${bindir}/nc_rms.py -v 'sst' -p ${tmpdir} -o ${outdir}/'sst_rms_'${imonth}.nc  $(find ${tmpdir} -type f ! -size 0 -name "${rootname}.????${imonth}.nc" -printf '%f ') 

done

# clean up
#rm -rf ${tmpdir}