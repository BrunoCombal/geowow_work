#!/usr/bin/env python

# author: Bruno COMBAL, JRC, European Commission
# date: 2009/03/20
# simulate operator. The number of operand depend on the operator

try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *
try:
    import numpy as N
    N.arrayrange = N.arange
except ImportError:
    import Numeric as N

try:
    from osgeo import gdal_array as gdalnumeric
except ImportError:
    import gdalnumeric

import sys
import os.path
import operator

# ________________________________________
def Usage(message):
    print message
    print "myMorphologyOperator.py -op operator [-param paramValue] -o outfile file"
    print "Applies a geometry operator to an image."
    print "operator can be:"
    print "dilate: dilate by paramValue pixels. paramValue default is 1."
    print

    sys.exit(-1)
# ________________________________________
def dist_manhattan(imageIN):
    # computes Manhattan distance of a matrix
    # see http://ostermiller.org/dilate_and_erode.html
    image = imageIN
    shape = imageIN.shape
    # go from top left to bottom right
    for jj in range(shape[0]):
        for ii in range(shape[1]):
            if image[jj][ii] == 1:
                image[jj][ii] = 0
            else:
                image[jj][ii] = shape[0] + shape[1]
                if (ii>0):
                    image[jj][ii] = min( (image[jj][ii], image[jj][ii-1]+1) )
                if (jj>0):
                    image[jj][ii] = min( (image[jj][ii], image[jj-1][ii]+1) )

        gdal.TermProgress(0.5*(jj+1)/float(shape[0]))

    # go from bottom right to top left
    for jj in range(shape[0]-1, 0, -1):
        for ii in range(shape[1]-1, 0, -1):
            if (ii+1)<shape[1]:
                image[jj][ii] = min( (image[jj][ii], image[jj][ii+1]+1) )
            if (jj+1)<shape[0]:
                image[jj][ii] = min( (image[jj][ii], image[jj+1][ii] + 1) )
        gdal.TermProgress(0.5+0.5*(jj-shape[0]+1)/float(shape[0]))

    return image

# ________________________________________
def op_geom_dilate(file, fileout, options, format, paramIn):
    # reference:
    #http://ostermiller.org/dilate_and_erode.html
    # dilates an image by param pixels
    param = int(paramIn)
 
    # open image, read everything in memory
    fid = gdal.Open(file, GA_ReadOnly)
    ns = fid.RasterXSize
    nl = fid.RasterYSize
    nb = fid.RasterCount
    
    outDrv = gdal.GetDriverByName( format )
    outDS = outDrv.Create( fileout, ns, nl, nb, GDT_Byte, options )
    outDS.SetProjection( fid.GetProjection() )
    outDS.SetGeoTransform( fid.GetGeoTransform() )

    # read in memory
    # process single band
    ib = 0
    dataIn = fid.GetRasterBand(ib+1).ReadAsArray(0,0,ns,nl)
    # data shape is nl, ns
    # ensure we have 0 and 1
    data = N.zeros((nl,ns))
    data[dataIn != 0] = 1
    dataIn = 0

    # dilate
    # note: it would be more efficient to have a Manhattan distance predictor
    rangeX=range(ns)
    rangeY=range(nl)
    
    if param <10:
        for idilate in range(param):
            for jj in rangeY:
                for ii in rangeX:
                    
                    if data[jj][ii] == 1:
                        if ( ( ii > 0) and (data[jj][ii-1]==0 ) ):
                            data[jj][ii-1] = 2
                            
                        if ( ( jj > 0 ) and (data[jj-1][ii]==0 ) ):
                            data[jj-1][ii] = 2
                                
                        if ( ( (ii+1) < ns ) and (data[jj][ii+1]==0) ):
                            data[jj][ii+1] = 2

                        if ( ( (jj+1) < nl ) and (data[jj+1][ii]==0) ):
                            data[jj+1][ii] = 2

                gdal.TermProgress((idilate*nl + jj) / float(nl*param))

            wt1 = (data != 0)
            data[wt1] = 1
            wt1 = 0
    
            # write output
            outDS.GetRasterBand(ib+1).WriteArray(data,0,0)

    else:
        print 'using Manhattan estimator'
        image = dist_manhattan(data)
        data[image <= param] = 1
        data[image > param] = 0
        outDS.GetRasterBand(ib+1).WriteArray(data,0,0)
                

    gdal.TermProgress(1)
    print
# ________________________________________
def op_geom_erode(file, fileout, options, format, paramIn):
    # reference:
    param = int(paramIn)
 
    # open image, read everything in memory
    fid = gdal.Open(file, GA_ReadOnly)
    ns = fid.RasterXSize
    nl = fid.RasterYSize
    nb = fid.RasterCount
    
    outDrv = gdal.GetDriverByName( format )
    outDS = outDrv.Create( fileout, ns, nl, nb, GDT_Byte, options )
    outDS.SetProjection( fid.GetProjection() )
    outDS.SetGeoTransform( fid.GetGeoTransform() )

    # read in memory
    # process single band
    ib = 0
    dataIn = fid.GetRasterBand(ib+1).ReadAsArray(0,0,ns,nl)
    # data shape is nl, ns
    # ensure we have 0 and 1
    data = N.zeros((nl,ns))
    data[dataIn != 0] = 1
    dataIn = 0

    # dilate
    # note: it would be more efficient to have a Manhattan distance predictor
    rangeX=range(ns)
    rangeY=range(nl)

    dataOut = data    
    for ierode in range(param):
        for jj in rangeY:
            for ii in rangeX:

                val = data[jj][ii]
                if val == 1:
                    # there is always at least 2 tests performed
                    # so test can be initialized to True
                    test=True
                    if ii > 0 :
                        test = test  & (data[jj][ii-1] == val)
                    if (ii+1) < ns :
                        test = test  & (data[jj][ii+1] == val)
                    if jj > 0 :
                        test = test  & (data[jj-1][ii] == val)
                    if (jj+1) < nl :
                        test = test  & (data[jj+1][ii] == val)
                    if test==True:
                        dataOut[jj][ii] = 0

            gdal.TermProgress((ierode*nl + jj) / float(nl*param))
        data = dataOut
    
        # write output
        outDS.GetRasterBand(ib+1).WriteArray(data,0,0)

    gdal.TermProgress(1)
    print
# ________________________________________
if __name__=="__main__":
    file=[]
    outfile=[]
    format='gtiff'
    options=[]
    opT = None
    param = None
    defaultParam=None

    # optList: 'name', number of files, accept parameters: False: no, True:yes, default parameter
    opTDef = (('dilate',1,True,1), ('erode',1,True,1))
    opTList = map(operator.itemgetter(0),opTDef)

    ii = 1
    while ii < len(sys.argv):
        arg = sys.argv[ii]
        
        if arg == '-of':
            ii = ii + 1
            format = sys.argv[ii]
        elif arg == '-co':
            ii = ii + 1
            options.append(sys.argv[ii])
        elif arg == '-op':
            ii = ii + 1
            opT = sys.argv[ii]
        elif arg == '-param':
            ii = ii + 1
            param = sys.argv[ii]
        elif arg == '-o':
            ii = ii +1
            outfile=sys.argv[ii]
        else :
            file.append(sys.argv[ii])

        ii = ii +1


    # check the command line
    if opT is None:
        Usage('missing operator, use -op option')

    for ifile in file:
        if (os.path.isfile(ifile)):
            pass
        else:
            Usage('Input file does not exist: ' + ifile)

    if opT in opTList:
        pass
    else:
        Usage('Unknown operator '+str(opT))

    # do we need and have parameters?
    try:
        iop = map(operator.itemgetter(0), opTDef).index(opT)
        nfiles = map(operator.itemgetter(1), opTDef)[iop]
        acceptParam = map(operator.itemgetter(2), opTDef)[iop]
        defaultParam = map(operator.itemgetter(3), opTDef)[iop]
        
        if len(file) != nfiles:
            Usage ('Unconsistent number of files in input for this operator, operator requires '+str(nfiles))
            
        

    except ValueError:
        Usage('Operator or operator parameter(s) not supported: '+str(opT))

    # call the operator
    if opT=='dilate':
        if param is None:
            param=defaultParam

        op_geom_dilate(file[0],outfile,options,format, param);
