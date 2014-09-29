#!/bin/bash
# \author Bruno Combal, IOC, UNESCO
# \date July 2013

inDir='/data/cmip3/TWAP_Aimee_sea_level_rise_data/sumall/'
outDir='/data/tmp/'

ps=0.7031

for ifile in SUMALL_mean_A1B SUMALL_mean_A2 SUMALL_mean_B1 std_SUMALL_A1B std_SUMALL_A2 std_SUMALL_B1
do
    # create ascii file: remove NaN and reformat
    layername=slr_${ifile}
    outfile=${outDir}/slr_${ifile}.csv
    echo "longitude , latitude , slr" > ${outfile}
    awk '{if ($1 > 180) {print $1-360,",", $2,",", $3} else {print $1,",",$2,",",$3}}' ${inDir}/${ifile} | grep -v NaN >> ${outfile}
    
    # create vrt file
    outvrt=${outfile%.*}.vrt
    echo '<OGRVRTDataSource>' > ${outvrt}
    echo '  <OGRVRTLayer name="'${layername}'">' >> ${outvrt}
    echo '    <SrcDataSource relativeToVRT="1">'${outfile##*/}'</SrcDataSource>' >> ${outvrt}
    echo '    <GeometryType>wkbPoint</GeometryType>'  >> ${outvrt}
    echo '    <LayerSRS>WGS84</LayerSRS>' >> ${outvrt}
    echo '    <GeometryField encoding="PointFromColumns" x="longitude" y="latitude"/>' >> ${outvrt}
    echo '    <Field name="slr" type="Real" src="slr" />' >> ${outvrt}
    echo '    <Field name="latitude" type="Real" src="latitude" />' >> ${outvrt}
    echo '    <Field name="longitude" type="Real" src="longitude" />' >> ${outvrt}
    echo '  </OGRVRTLayer>' >> ${outvrt}
    echo '</OGRVRTDataSource>' >> ${outvrt}
    
    # burn to raster
    outraster=${outDir}/raster_${ifile}.tif
    rm -f ${outraster}
    gdal_rasterize -a 'slr' -l ${layername} -a_nodata 1000 -init 1000 -of gtiff -co "compress=lzw" -a_srs 'EPSG:4326' -te -180 -90 180 90 -tr ${ps} ${ps} -tap ${outvrt} ${outraster}
done