#!/bin/sh
awk '/^.I / {id=$2;next} \
            /^.W$/ {W=1;next} \
            W {print("ID "id);print;W=0;next}' $1
