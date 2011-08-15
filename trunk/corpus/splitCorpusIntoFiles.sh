#!/bin/sh
awk -v n=0 '/^.I / {close("corpus"n);n++;next} \
            /^.W$/ {W=1;next} \
            W {print > "corpus"n;W=0;next}' $1
