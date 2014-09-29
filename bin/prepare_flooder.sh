#!/bin/bash

## \author Bruno Combal
## \date february 2013

# inputs:
# ACE2 tiles
# MSL image
# shoreline (polygon)
demDir=/path/to/ace2tiles
demTiles=$(find ${demDir} -name "*.ace2")
demDirOut=/path/to/newtiles

mslDir=/path/to/msl
msl=MSL_blabla.tif
mslDirOut=/path/to/msl/out
mslOut=MSL_filled.tif

shorelineDir=/path/to/shoreline
shorline=ghss.shp
shorelineDirOut=/path/to/new/shoreline
shorlineOut=shoreline_asline.shp

tmpDir=/path/to/tmp

#1./ fill gaps in MSL (there are gaps along the coast)
# ensure that nodata is set for MSL (do it with QGIS)
gdal_fillnodata -md 10 -o ${mslDirOut}/${mslOut} ${mslDir}/${msl}

#2./ convert shoreline from polygons to line
ogr2ogr -f 'ESRI shapefile' ${shorelineDirOut}/${shorelineOut} ${shorelineDir}/${shoreline} -nlt 1

#3./ burn the shoreline in ace2 tiles
for iDem in ${demTiles[@]}
do
    gdal_calc.py --overwrite -A ${demDir}/${iDem} --calc 'A*0' --format 'geotiff' --outfile ${demDirOut}/shore_${iDem} --type Byte
    gdal_rasterize -burn 1 -of 'gtiff' -co 'compress=lzw' ${shorlineDirOut}/${shorelineOut} ${demDirOut}/shore_${iDem}
    # resample MSL to ace2
    gdalwarp -r bilinear -tr XXXX XXXX -srcnodata -500 -dstnodata -500 -te xmin ymin xmax ymax ${mslDir}/${msl} ${tmpDir}/tmpFile.tif
    # capture MSL values into shore_${idem}
    
done
