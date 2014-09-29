#!/bin/bash

## \author Bruno COMBAL
## \date February 2013

function messageOnExit(){
    echo $1
    echo "Usage: make_slrcr.sh [options]"
    echo "Options:"
    echo "   -c config.xml"
    echo "      a configuration file. Default is config/make_slrcr.xml."
    exit 1
}

# default values
xmlConfig="/Users/bruno/Desktop/UNESCO/geowow/codes/config/make_slrcr.xml"

# getopt
ARGS=`getopt abch: $*`
if [ $? -ne 0 ]; then
    exit 1
fi

set -- $ARGS

for i
do
    case "$i"
	in
	-a|b)
	    echo flag $i set
	    sflags="${i#-}$sflags"
	    shift;;
	-c)
	    xmlConfig="$2"

	    oarg="$2"
	    shift
	    shift;;
	--)
	    shift; break;;
    esac
done
echo single-char flags: "'"$sflags"'"
echo oarg is "'"$oarg"'"


# loop over the list of experiements
nExperiments=$(xpath ${xmlConfig} "count(//config/experiment)" 2>/dev/null )

lstIdExp=($(xpath ${xmlConfig} "//config/experiment/@id" 2>/dev/null ))

echo "parsing the xml configuration file"
for iExp in ${lstIdExp[@]}
do
    echo "experiment: " $iExp
    zos=$(xpath ${xmlConfig} "//config/experiment[attribute::${iExp}]/zos/text()" 2>/dev/null)
    ph=$(xpath ${xmlConfig} "//config/experiment[attribute::${iExp}]/ph/text()" 2>/dev/null)
    echo $zos
    echo $ph
done
