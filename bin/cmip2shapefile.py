#!/usr/bin/env python
# \author Bruno Combal
# \date February 2013
# CMIP5 data are netcdf files, with variables stored as 3D variables (time, y, x)
# Grids are not consistently projected images: each cell as its own coordinates, usually lat/lon bounding values.
# This program creates a reference shapefile of polygones, each polygone delineating a gridcell, and
# having the cell (x,y) references in its dbf.
# The generated shapefile is used to cross the CMIP5 data with other kind of georeferenced data.

import sys
import os
from scipy.io import netcdf
from osgeo import ogr

## \brief message displayed on exit
def messageOnExit(message=None, exitCode=1):
    if message is not None:
        print message
        print

    print 'Usage: cmip2shapefile -o outfile infile'
    print 'Outfile is deleted first.'
    
    sys.exit(exitCode)

## \brief if one of the candidates is found in the file's variables, return the first matching variable name.
def searchVar(fh, candidates):
    found=None
    for ii in candidates:
        if ii in fh.variables.keys():
            found=ii
            break
    return found

## \brief create a shapefile of polygons
def writeShapefile(filename, format, cells, indexes, layerName):
    drv = ogr.GetDriverByName(format)
    if os.path.exists(filename):
        drv.DeleteDataSource(filename)
    shpH = drv.CreateDataSource(filename)
    if shpH is None:
        messageOnExit("Could not create file {0}. Exit(8)".format(filename), 8)

    # create fields
    fldIPOS = ogr.FieldDefn('ipos', ogr.OFTInteger)
    fldIPOS.SetWidth(8)
    fldII = ogr.FieldDefn('ii', ogr.OFTInteger)
    fldII.SetWidth(4)
    fldJJ = ogr.FieldDefn('jj',ogr.OFTInteger)
    fldJJ.SetWidth(4)
    
    # create spatial reference
    srs = ogr.osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # create layers
    layer = shpH.CreateLayer(layerName, srs, ogr.wkbPolygon)
    layer.CreateField(fldIPOS)
    layer.CreateField(fldII)
    layer.CreateField(fldJJ)

    for celldef, thisIndices in zip(cells, indexes):
        edge = ogr.Geometry(ogr.wkbLinearRing)
        for ipoint in celldef:
            edge.AddPoint(ipoint[0], ipoint[1])
        edge.CloseRings()
        cell = ogr.Geometry(ogr.wkbPolygon)
        cell.AddGeometry(edge)

        feature = ogr.Feature( layer.GetLayerDefn() )
        feature.SetField( "ipos", thisIndices[2] )
        feature.SetField( "ii", thisIndices[0] )
        feature.SetField( "jj", thisIndices[1] )
        feature.SetGeometry(cell)
        layer.CreateFeature(feature)

        cell.Destroy()
        feature.Destroy()
        
    shpH = None
    
## \brief create a grid shapefile (polygons) on the basis of the data in the netcdf file
def doCMIP2Shapefile(infile, outfile, format, layerName, lonModulo180):

    print "opening ",infile
    fh = netcdf.netcdf_file(infile, "r")
    if fh is None:
        messageOnExit("Could not open file {0}. Exit(3).".format(infile))

    latVar = searchVar(fh, ('lat_bnds', 'lat_vertices') )
    lonVar = searchVar(fh, ('lon_bnds', 'lon_vertices') )
    if latVar is None:
        messageOnExit('Could not find a variable describing latitute. Exit(4).', 4)
    if lonVar is None:
        messageOnExit('Could not find a variable describing longitude. Exit(5).', 5)

    latVar = fh.variables[latVar][:]
    lonVar = fh.variables[lonVar][:].copy() # allows editing the array

    cells = []
    ijTab = []
    if len(latVar.shape) == 2:
        if lonModulo180:
            wtc = (lonVar[:, 1] >180.0)
            if wtc.any():
                lonVar[wtc, 0] = lonVar[wtc, 0] - 360.0
                lonVar[wtc, 1] = lonVar[wtc, 1] - 360.0
        
        for ii in range(len(lonVar)):
            for jj in range(len(latVar)):
                cells.append( ( (lonVar[ii, 0], latVar[jj, 0]), (lonVar[ii, 0], latVar[jj, 1]),
                                (lonVar[ii, 1], latVar[jj, 1]), (lonVar[ii, 1], latVar[jj, 0]) ) )
                ijTab.append( (ii, jj, ii+jj*len(lonVar) ) )
    elif len(latVar.shape)==4:

        if lonModulo180:
            wtc = (loVar[:, 1] > 180.0)
            if wtc.any():
                for icorner in range(4):
                    lonVar[wtc, icorner] = lonVar[wtc, icorner] - 360.0
        
        for ii in range(len(lonVar)):
            for jj in range(len(latVar)):
                cells.append( ( (lonVar[ii, 0], latVar[jj, 0]), (lonVar[ii, 1], latVar[jj, 1]),
                                (lonVar[ii, 2], latVar[jj, 2]), (lonVar[ii, 3], latVar[jj, 3]) ) )
                ijTab.append( (ii, jj, ii+jj*len(lonVar) ) )
    else:
        messageOnExit('Unknown lat/lon type of variables. Exit(6)', 6)

    if layerName is None:
        layerName = os.path.basename(infile)
        if layerName is None:
            messageOnExit("Could not extract filename from path {0}. Exit(7).".format(infile))

    writeShapefile(outfile, format, cells, ijTab, layerName)

## \brief main reads the input parameter line
if __name__=="__main__":
    outfile=None
    format='ESRI Shapefile'
    infile=None
    layerName = None
    lonModulo180 = False

    ii=1
    while ii<len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-o':
            ii = ii + 1
            outfile = sys.argv[ii]
        elif arg == '-l':
            ii = ii + 1
            layerName = sys.argv[ii]
        elif arg == '-lon_modulo_180':
            lonModulo180 = True
        else:
            infile = arg
        ii = ii + 1

    if infile is None:
        messageOnExit('Input file is not defined. Exit(1).', 1)
    if outfile is None:
        messageOnExit('Output file is not defined. Exit(2)', 2)

    doCMIP2Shapefile(infile, outfile, format, layerName, lonModulo180)
