#!/bin/sh
if [ $# -ne 3 ]
then
	echo "Usage: corpus-file-to-split chunk-size base-file-name-of-splitted-files";
	exit 1;
fi
print $2;
awk -v base=$3 -v fname=$3".1" -v chunkSize=$2 \
	'	BEGIN {n=0;fname = base"."n;print "Writing to "fname}
		/^.U$/ {
			if(text) {print text > fname;}
			if((n % chunkSize) == 0) {fname = base"."n; print "Writing to "fname}
			text = "";readId = 1;n += 1;next
		}
		/^[0-9]/ && readId == 1 {print(".I "$0) > fname;readId=0;next}
		/^.T$/ {T=1;next} 
	     T {text=$0;T=0;next}
	     /^.W$/ {W=1;next}
	     W {text=text" "$0;W=0;next}
		END {print text > fname;}' $1
