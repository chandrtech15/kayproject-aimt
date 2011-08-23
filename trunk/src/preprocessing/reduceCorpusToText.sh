#!/bin/sh
awk '/^.U$/ {if(text) {print text;} text="";readId=1;next} \
	/^[0-9]/ && readId == 1 {print(".I "$0);readId=0;next} \
	/^.T$/ {T=1;next} \
     T {text=$0;T=0;next} \
     /^.W$/ {W=1;next} \
     W {text=text" "$0;W=0;next}
	END {print text;}' $1
