## \brief shell functions library
## \author Bruno Combal
## \date April 2013

function makeTmpDir(){
    # $1 contains the path
    if [[ -z "$1" ]]; then
	rootdir='.'
    else
	rootDir=$1
    fi

    # initialize file name
    tmpDir=${rootDir}/$RANDOM$RANDOM

    # if this file name already exists, regenerate a new one
    while [ -d ${tmpDir} ]; do
	tmpDir=${rootDir}/$RANDOM$RANDOM
    done

    mkdir -p ${tmpDir}

    echo ${tmpDir}
}