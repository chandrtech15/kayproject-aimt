#!/bin/sh
awk -v fname='' -v n=0 -v base=$3 '/^.I / {id=$2; if(n >= '$2' || n == 0){close(fname);fname=base"."id;n=0;}n++;next} \
            /^.W$/ {W=1;next} \
            W {print("ID "id) > fname;print > fname;W=0;next}' $1
