#!/bin/bash

ls outdata/mydiff_diff*.tif | while read line
do
    ../bin/colorize.py -o outdata/color_${line} -l ../bin/zos.lut -bck 128 128 128
done