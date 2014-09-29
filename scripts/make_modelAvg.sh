#!/bin/bash

# to run the script with the correct version of uvcdat:
#  source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh


# compute model climato (average), as using ncea resulted in wrong result (all months had same values)

bindir=/home/bruno/Documents/dev/codes/bin
indir=/data/cmip5/rcp/rcp8.5/toshist_ensemble/
outdir=/data/cmip5/rcp/rcp8.5/toshist_ensemble/
yearStart=1981
yearEnd=2000

list=''
for imonth in $(seq -w 1 12)
do
    # average files for this month
    # find files with dates between 1981 and 2000
    list=()
    for iyear in $(seq ${yearStart} ${yearEnd})
    do
	thisfile=modelmean_tos_${iyear}${imonth}.nc
	if [ -e ${indir}/${thisfile} ]; then
	    list=(${list[@]} ${thisfile})
	fi
	
    done
    ${bindir}/nc_avg.py -o ${outdir}/climato_tos_${imonth}.nc -v 'tos' -p ${indir} ${list[@]}
done