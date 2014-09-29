#!/bin/bash

## 
function containsElement () {
    for e in "Australia" "Fidji" "France" "Kiribati" "Madagascar" "United States" "Tuvalu" "Saudi Arabia" ; do
	if [[ "$e" == "$1" ]] ; then
	    echo 0
	    return 0
	fi
    done
    echo 1
    return 1
}

##
function recodeName(){
    echo ${@:1} | sed 's/ /_/g' | sed 's/\//_/g' | sed 's/[:(),\.]//g'
}

# 1./ get countries names:
tmpfile=countries_tmp${RANDOM}.txt
tmpFileForConvexhull=exploded_countries_tmp${RANDOM}.txt
sortUniqCountries=sortUniqCountries_tmp${RANDOM}.txt
outDir=/Users/bruno/Desktop/UNESCO/geowow/showcases/coralreefs/data/reefbase.org/
binDir=/Users/bruno/Desktop/UNESCO/geowow/codes/bin
mkdir -p ${outDir}
srcFile=${outDir}/coralreef2010/coralreef2010.shp

# note that the file contains repeated values for NICARAGUA and HONDURAS: to be discarded
ogrinfo -al -geom=NO ${srcFile} | grep COUNTRY | grep -v NICARAGUA | grep -v HONDURAS | sed '/COUNTRY_1: String/d' | sed 's/.*=//g' | sed 's/^ //g' > ${tmpfile}
if [ $? -ne 0 ]; then
  echo "Error: ogrinfo could not get information. Exit."
  rm $tmpfile
  exit 1
fi

sort ${tmpfile} | uniq > ${sortUniqCountries}
rm ${tmpfile}

# 2./ explode countries in separated files and compute the corresponding convex hull
cat ${sortUniqCountries} | while read country
do
    #cntry=$(echo ${country} | sed 's/ /_/g' | sed 's/\//_/g' | sed 's/[:(),\.]//g' )
    cntry=$(recodeName ${country})
    if [[ $(containsElement "${country}") -eq 0 ]] ; then
	echo "let's process that "$country
	# get list of Islands
	ogrinfo -al -geom=NO -where "COUNTRY_1 = \"${country}\"" ${srcFile} | grep REEF_NAM_1 | sort | uniq | sed 's/.*REEF.*=//g' | sed 's/^ //g' | while read ireef
	do
	    reefname=$(recodeName ${ireef})
	    echo "Exploding "$cntry" for reef "$ireef" known as "$reefname
	    outname=${outDir}/explodedCountries/exploded_${cntry}_${reefname}.shp
	    echo ${cntry}_${reefname} >> ${tmpFileForConvexhull}
	    ogr2ogr -overwrite -f "ESRI Shapefile" -where "COUNTRY_1 = \"${country}\" AND REEF_NAM_1 = \"${ireef}\"" ${outname} ${srcFile}
	done
    else
	echo ${cntry} >> ${tmpFileForConvexhull}
	ogr2ogr -overwrite -f "ESRI Shapefile" -where "COUNTRY_1 = \"${country}\"" ${outDir}/explodedCountries/exploded_${cntry}.shp ${srcFile}
    fi
done

rm ${sortUniqCountries}

# compute convex hull
echo "Computing convex hulls"
cat ${tmpFileForConvexhull} | while read object
do
    echo "Convex hull for "$object
    $binDir/convexHull.py ${outDir}/explodedCountries/exploded_${object}.shp ${outDir}/convex/convex_${object}.shp
done


rm ${tmpFileForConvexhull}
