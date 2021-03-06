#!/bin/bash
# Wrapper for Tadpole, called by CLAM ('blackbox')
# assumes tadpole is installed on the system

STATUSFILE=$1
INPUTDIR=$2
OUTPUTDIR=$3
PARAMETERS=${@:4}


for f in $INPUTDIR*.txt; do
    filename=`basename $f`
    echo "Processing $filename" > $STATUSFILE
    echo "Running Tadpole $PARAMETERS -t $f > ${OUTPUTDIR}$filename.tadpole"
    #note that here the $PARAMETERS are passed just as they were received by CLAM
    Tadpole $PARAMETERS -t $f > ${OUTPUTDIR}$filename.tadpole 
done

