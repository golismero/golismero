#!/bin/sh

usage(){
    echo -en "\nhtrdbc 1.0\n"
    echo -en "(c) 2009 by Marc Ruef\n"
    echo -en "http://www.computec.ch/projekte/httprecon/\n"
    if [ "$(1)" ]; then
	echo -en "${1}\n\n"
    fi
    echo -en "Usage:\t${0} <path>\n"
    echo -en "Example:\t${0} database/get_existing\n\n"
}

cleandb(){
    for FILE in `ls ${1}/*.fdb`; do
	echo -en "Cleaning ${FILE} ... "

	cleandb=`cat "${FILE}" | sort | uniq`
	echo "${cleandb}" > "${FILE}"
	echo -en "done!\n"
    done
}

if [ $# -eq 1 ]; then
    cleandb "${1}"
    exit 1;
else
    usage
    exit 2;
fi
