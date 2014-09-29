#!/usr/bin/env python
# \author Bruno Combal
# \date April 2013

import sys
import os
import cdms2
import MV2
import numpy

## \brief Message displayed on exit.
def exitMessage(message='', errorCode=1):
    if message!='':
        print message
    print 'Usage: mynNcea.py - variable var -outDir dir -outName name -path file1.nc file2.nc ...'
    print
    exit(errorCode)

##
def doMyNcea(variable, dataMin, dataMax, path, infile, outdir, outfile):
    
    # initialise
    thisfile=cdms2.open(path+infile[0],'r')
    if not (variable in thisfile.variables.keys()):
        exitMessage('Key {0} not found in keys list: {1}. Exit(20).'.format(variable, thisfile.variables.keys()), 20)
    dimensions=thisfile.variables[variable][:].shape
    accum = numpy.zeros( (dimensions[0], dimensions[1]*dimensions[2] ))
    counter = numpy.zeros( (dimensions[1] * dimensions[2]) )
    minimum = numpy.ones((dimensions[0], dimensions[1]*dimensions[2] ) ) * dataMax
    maximum = numpy.ones((dimensions[0], dimensions[1]*dimensions[2] ) ) * dataMin

    refGrid=thisfile.variables[variable].getGrid()
    refAxis=thisfile.variables[variable].getAxisList()
    thisfile = None

    for ii in range(0,1): #range(0, len(infile)):
        print 'processing file {0}'.format(ii)
        thisfile = cdms2.open(path+infile[ii],'r')
        data = numpy.array(thisfile.variables[variable][:])
        print '\tmask'
        wtk = numpy.ravel( ( numpy.ravel(data[0,:]) > dataMin ) * ( numpy.ravel(data[0,:]) < dataMax ))
        if wtk.any():
            print '\tsumming'
            data = numpy.reshape(data, (dimensions[0], dimensions[1]*dimensions[2] )) 
            accum[ :, wtk ] = accum[ :, wtk ] + data[ :, wtk ]
            print '\tcounting'
            counter[ wtk ] = counter[ wtk ] + 1
            print '\tminimum detection'
            minimum[ :, wtk ] = numpy.minimum( minimum[:, wtk], data[:, wtk] )
            print '\tmaximum detection'
            maximum[ :, wtk ] = numpy.maximum( maximum[:, wtk], data[:, wtk] )
        thisfile=None
        

    wta = counter>0
    if wta.any():
        print accum.shape,counter.shape, wta.shape
        for ii in range(dimensions[0]):
            accum[ii, wta] = accum[ii, wta] / counter[wta]

        outfile = cdms2.open(outdir+'avg_'+outfile,'w')
        accum = accum.reshape(dimensions)
 
        myvar=MV2.array(accum).astype(numpy.float32)
        myvar.id='avg_{0}'.format(variable)
        myvar.setAxisList((refAxis,))
        outfile.write(myvar)

        
        outfile.close()

## \brief main reads the input parameter line
if __name__=="__main__":
    outfile=None
    outdir=''
    infile=[]
    path=''
    variable=None
    dataMin = 0
    dataMax = 273.15+50

    ii=1
    while ii<len(sys.argv):
        arg = sys.argv[ii]
        if arg == '-outDir':
            ii=ii+1
            outdir=sys.argv[ii]
        elif arg=='-outFile':
            ii = ii + 1
            outfile=sys.argv[ii]
        elif arg=='-path':
            ii = ii + 1
            path=sys.argv[ii]
        elif arg=='-variable' or arg=='-v':
            ii=ii+1
            variable=sys.argv[ii]
        elif arg=='-dataRange':
            ii=ii+1
            dataMin=float(sys.argv[ii])
            ii=ii+1
            dataMax=float(sys.argv[ii])
        else:
            infile.append(sys.argv[ii])
            
        ii=ii+1

    if outfile is None:
        exitMessage('Output file name is not defined. Use option -outFile. Exit(10).',10)
    if len(infile)==0: 
        exitMessage('No input file defined. Exit(11)',11)
    if variable is None:
        exitMessage('No variable defined. Use option -variable. Exit(12).', 12)

    doMyNcea(variable, dataMin, dataMax, path, infile, outdir, outfile)
