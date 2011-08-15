#!/bin/sh
awk -v fname='' '/^.I / {close(fname);id=$2;fname=FILENAME"."id;next} \
            /^.W$/ {W=1;next} \
            W {print("ID "id) > fname;print > fname;W=0;next}' $1
