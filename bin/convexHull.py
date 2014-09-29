#!/usr/bin/env python
## \author Bruno Combal
## \date January 2013

import sys
import os
import string
from osgeo import ogr

##
def usage(message):
    print message
    print 'Usage: convexHull.py inputFile.shp outputFile.shp'
    sys.exit(1)

##
def doConvexHull(infile, outfile):
    inH = ogr.Open(infile, 0)
    if inH is None:
        usage("Could not open file {0}. Exit.".format(infile))
    layer = inH.GetLayer()

    # get all polygons
    thisGeometry = ogr.Geometry(ogr.wkbGeometryCollection)
    for index in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(index)
        thisGeometry.AddGeometry(feature.GetGeometryRef())

    convexHull = thisGeometry.ConvexHull()
    #convexHull.forceToPolygon()
    
    drv = ogr.GetDriverByName( "ESRI Shapefile" )
    if os.path.exists(outfile):
        drv.DeleteDataSource(outfile)
    ds = drv.CreateDataSource( outfile )
    if ds is None:
        usage("Could not create file {0}".format( outfile) )

    # fields
    fldDfn = ogr.FieldDefn('id', ogr.OFTInteger)
    fldDfn.SetWidth(4)

    lyrname = "convexHull_${0}".format( layer.GetName() )
    lyr = ds.CreateLayer( lyrname, layer.GetSpatialRef(), ogr.wkbPolygon )
    lyr.CreateField(fldDfn)
    
    thisFeature = ogr.Feature( lyr.GetLayerDefn() )
    thisFeature.SetGeometry( convexHull )
    thisFeature.SetField('id',1)
    lyr.CreateFeature( thisFeature )

    ds.Destroy()

## \brief main reads input parameters
if __name__=="__main__":

    files=[]

    ii=1
    while ii<len(sys.argv):
        arg=sys.argv[ii]
        files.append(sys.argv[ii])
        ii = ii +1


    if len(files)!=2:
        usage('Wrong number of arguments. Exit.')

    doConvexHull(files[0], files[1])
