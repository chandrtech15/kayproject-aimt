'''
Created on Aug 16, 2011

@author: tass

Command line usage:
treetaggerBatch.py <Directory with corpus files>
'''
from treetaggerIO import TreeTaggerIO, ttDir
import os, sys

tagger = TreeTaggerIO(ttDir)

import fileinput
for line in fileinput.input():
	line = line.strip()
	if line.startswith("<title"):
		title = line[8:]
	elif line and not line.startswith("<"):
		entries = tagger.tagger.TagText(line)
		terms = [title]
		term = []
		for entry in entries:
			w, t, l = entry.split()
			if t.startswith("N"):
				term.append( l if l != "<unknown>" else w )
			else:
				if len(term) > 1:
					terms.append(" ".join(term))
				term = []

		if len(term) > 1:
			terms.append(" ".join(term))
		print "|".join(terms)
