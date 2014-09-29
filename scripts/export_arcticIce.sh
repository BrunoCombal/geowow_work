#!/bin/bash

# extract data from articIce.csv to html for insertion in highcharts.

inCSV='/home/bruno/Documents/tmp/arcticIce.csv'

# get list of models
listModels=($(cat ${inCSV} | cut -d ',' -f 1 | uniq | sort |uniq))

for im in ${listModels[@]}
do
    # get all rips
    lstRIP=($(awk -F ',' '{if ($1=="'${im}'") print $6;}' ${inCSV} | uniq | sort | uniq))
    linkTo=''
    for irip in ${lstRIP[@]}
    do
	id=${im#sit_OImon_}${irip}
	echo "{{name:'${im#sit_OImon_} ${irip}', id:'${id}', data:["
	cat ${inCSV} | grep ${im} | grep ${irip} | awk -F ',' '{if ($1=="'${im}'" && $3==9 && $2 <= 2100) printf "[%s, %6.4f], ",$2,$5;}' ${inCSV}
	echo "], lineWidth:0, marker:{{lineWidth:0, symbol:'circle'}}}},"
	if [ -z "${linkTo}" ] ; then
	    linkTo=${id}
	else
	    echo "linkedTo:'${id}', visible:true},"
	fi

    done
done