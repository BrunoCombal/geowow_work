#!/bin/bash

## \author Bruno Combal
## \date April 2013

demDir=/data/dem/ace2/
tmpRoot=/home/bruno/Documents/tmp
codesDir=/home/bruno/Documents/dev/codes/
binDir=${codesDir}/bin
indicDir=${codesDir}/indicators
countryShapes=/data/gis/general_data/TM_WORLD_BORDERS-0.3.shp
urbanRuralShapes=/data/socioeconomic/population/glurextents/twapedit_glurextents.shp

source ${binDir}/library.sh
tmpDir=$(makeTmpDir ${tmpRoot})

demVRT=mosaicDEM.vrt
blankDEMGrid=${tmpRoot}/ace2blank.tif
popCSV=/data/socioeconomic/population/lecz-urban-rural-population-land-area-estimates-preliminary/TWAPEDIT_lecz-pop_1990_2000_2010_2050.csv

makeDEMVRT=0
regridPopulation=1

if [[ $makeDEMVRT -eq 1 ]]; then

    # make the DEM 
    lstACE=$(find ${demDir} \( -name '??[NS]????_3S.ACE2.gz' ! -name '90S????_3S.ACE2.gz'  \) -type f ! -size 0 -printf '%f\n' )
    #lstACE=$(find ${demDir} -name '[6789]?[NS]????_3S.ACE2.gz' -type f ! -size 0 -printf '%f\n' )

    listDEMTif=''
    for ifile in ${lstACE[@]}
    do
        # gunzip 
	aceName=${ifile%.gz}
	gunzip -c ${demDir}/${ifile} > ${tmpRoot}/${aceName}
	
        #operations
        #maskFile=${aceName%.ACE2}_0_10m.tif
        #maskBinFile=${aceName%.ACE2}_classes_0_10m.tif
        #${indicDir}/slr_lclz.py --demInFile ${tmpDir}/${aceName} --type 'value' --minmax 0 10 --maskOutFile ${tmpDir}/${maskFile}
        #${indicDir}/slr_lclz.py --demInFile ${tmpDir}/${aceName} --type 'classes' --minmax 0 10 --maskOutFile ${tmpDir}/${maskBinFile}
	
	classFile=${aceName%.ACE2}_classes.tif
	echo "class file="${classFile}
	${binDir}/filterDEM.py -o ${tmpDir}/${classFile} -of gtiff -co 'compress=lzw'  ${tmpDir}/${aceName}
	listDEMTif=(${listDEMTif[@]} ${tmpDir}/${aceName} )
        #clean tmpdir
	rm -f ${tmpDir}/${aceName}
    done

    echo ${listDEMTif[@]} | sed 's/ /\n/g' > ${tmpDir}/listOfDEMTiles.txt
    
    gdalbuildvrt -inpuyt_file_list${tmpDir}/listOfDEMTiles.txt -overwrite -vrtnodata 255 ${tmpDir}/${demVRT}
fi

if [[ $regridPopulation -eq 1 ]]; then
    dos2unix ${popCSV}

    # let's process by countries: skip the first line
    lstCountries=($(tail -n +2 ${popCSV} | cut -d ";" -f 1  | sort | uniq))

    for cntry in ${lstCountries[@]}
    do
	echo "Processing country "$cntry
	rm -f ${tmpDir}/popdata.csv
	grep ${cntry} ${popCSV} | while read line
	do
	    countryISO=$(echo $line | cut -d ";" -f 1)
	    if [[ $countryISO = $cntry ]]; then
		classElev=$(echo $line | cut -d ";" -f 5)
		ruralUrban=$(echo $line | cut -d ";" -f 6)
		pop1990=$(echo $line | cut -d ";" -f 7)
		pop2000=$(echo $line | cut -d ";" -f 8)
		pop2010=$(echo $line | cut -d ";" -f 9)
		pop2030=$(echo $line | cut -d ";" -f 10)
		pop2050=$(echo $line | cut -d ";" -f 11)
		pop2100=$(echo $line | cut -d ";" -f 12)
		area=$(echo $line | cut -d ";" -f 13)
		echo $countryISO ${classElev} ${ruralUrban} ${pop1990} ${pop2000} ${pop2010} ${pop2030} ${pop2050} ${pop2100} ${area} >> ${tmpDir}/popdata.csv
	    fi
	done
	# make a temporary copy of the blankdem
	cp -f ${blankDEMGrid} ${tmpDir}/urbanrural.tif
	if [[ $? -ne 0 ]]; then
	    echo "Could not create a copy of ${blankDEMGrid} in directory ${tmpDir}"
	    exit 120
	fi
	# crop the urbanmask with the country, DN=2 corresponds to urban areas
	ogr2ogr -clipsrc ${countryShapes} -clipsrcwhere "ISO3 = '${cntry}'" ${tmpDir}/urbanrural_${cntry}.shp ${urbanRuralShapes}
	if [[ $? -ne 0 ]] ; then
	    echo "Command ogr2ogr failed!"
	    echo ogr2ogr -clipsrc ${countryShapes} -clipsrcwhere "ISO3 = '${cntry}'"  ${tmpDir}/urbanrural_${cntry}.shp ${urbanRuralShapes}
	    rm -rf ${tmpDir}
	    exit 100
	fi
	#ogr2ogr -where "DN='1'" -clipsrc ${cntry} -clipsrcwhere "ISO3 = '${countryISO}'" ${tmpDir}/rural_${countryISO}.shp ${urban}
	# burn the cropped urbanmask to the blankdem, the value being the pop/pixel count
	gdal_rasterize  -a "DN" ${tmpDir}/urbanrural_${cntry}.shp ${tmpDir}/urbanrural.tif
	if [[ $? -ne 0 ]] ; then
	    echo "Command gdal_rasterize failed!"
	    echo gdal_rasterize  ${tmpDir}/urbanrural_${cntry}.shp ${tmpDir}/urbanrural.tif
	    rm -rf ${tmpDir}
	    exit 101
	fi

	tmpPopProj=${tmpDir}/popProj_${RANDOM}.tif
	${binDir}/regridPop.py -elevClasses ${tmpRoot}/mosaicDem.vrt -urbanMask ${tmpDir}/urbanrural.tif -dataCsv ${tmpDir}/popdata.csv ${tmpPopProj}
	if [[ $? -ne 0 ]] ; then
	    echo ${binDir}/regridPop.py -elevClasses ${tmpRoot}/mosaicDem.vrt -urbanMask ${tmpDir}/urbanrural.tif -dataCsv ${tmpDir}/popdata.csv ${tmpPopProj}
	   rm -rf ${tmpDir}
	   exit 102
	fi

	# now accumulate the result into a general map
	if [[ -e ${tmpDir}/popProj.tif ]] ; then
	    gdal_merge.py -o ${tmpDir}/popProj.tif -of GTIFF -co "compress=LZW" ${tmpDir}/popProj.tif ${tmpPopProj}
	    rm -f ${tmpPopProj}
	else
	    mv ${tmpPopProj} ${tmpDir}/popProj.tif
	fi
    done
fi

