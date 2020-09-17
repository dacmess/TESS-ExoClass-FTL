#!/bin/bash

OLD_NAME="sector14-26_20200825"
NEW_NAME="sector27_20200905"

OLD1="SECTOR = -1"
NEW1="SECTOR = 27"

OLD2="SECTOR1 = 14"
NEW2="SECTOR1 = 27"

OLD3="SECTOR2 = 26"
NEW3="SECTOR2 = 27"

# This replaces my local directory
OLD4="sector14-26"
NEW4="sector27"

# This replaces SPOC data directory
OLD5="sector-014-026"
NEW5="sector-027"

# DV report prefix
OLD6="tess2019199201929-"
NEW6="tess2020187183116-"
# DV report postfix
OLD7="-00353_dvr.pdf"
NEW7="-00362_dvr.pdf"

#LC prefix
OLD8="tess2020160202036-s0026-"
NEW8="tess2020186164531-s0027-"
OLD9="-0188-s"
NEW9="-0189-s"

for name in `ls *py`; do
  echo $name
  cp -f ${name} temp.foo
  sed -e "s/${OLD_NAME}/${NEW_NAME}/g; s/${OLD1}/${NEW1}/g; s/${OLD2}/${NEW2}/g; s/${OLD3}/${NEW3}/g; s/${OLD4}/${NEW4}/g; s/${OLD5}/${NEW5}/g; s/${OLD6}/${NEW6}/g; s/${OLD7}/${NEW7}/g;  s/${OLD8}/${NEW8}/g;  s/${OLD9}/${NEW9}/g" temp.foo > ${name}
done

