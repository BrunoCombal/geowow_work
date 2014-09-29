#!/bin/bash

# Bruno Combal, UNESCO/IOC
# 2013/06/10
source /usr/local/uvcdat/1.2.0/bin/setup_cdat.sh
bindir=/home/bruno/Documents/dev/codes/scripts
tmpdir=/home/bruno/Documents/tmp/tos
outdir=/data/cmip5/rcp/rcp8.5/tos_ensemble/
var=tos

 #${bindir}/make_ensembleMean_TOS.py

 lstYear=($(find ${tmpdir} -type f ! -size 0 -name avg_*nc | sed 's/.*\///' | sed 's/.*_//' | sed 's/\.nc//' | sort | uniq))


 for iyear in ${lstYear[@]}
 do
     echo "Processing year "${iyear}
     thislist=($(find ${tmpdir} -type f ! -size 0 -name avg_*_${iyear}.nc | sed 's/.*\///' ))
     for iop in avg min max
     do
	 outavg=${outdir}/${iop}_${var}_${iyear}.nc
	 echo "    making "${iop}" (${outavg##*/})"
	 ncea -o ${outavg} -y ${iop} --path ${tmpdir} ${thislist[@]}
    done
done