#!/usr/bin/env python
import sys
import io
import os

if len(sys.argv) < 2:
	print 'This script is to select one relevant document per topic to be used as the query context.'
	print 'Given a path to a qrels file (such as corpus/ohsu-trec/trec9-test/qrels.ohsu.88-91) as an argument, it will store the selected documents in path.selection and all the others in path.remainder. If highly relevant documents are available, one of those is selected at random, otherwise one of the less relevant documents has to be picked.'	
	sys.exit(0)

input = sys.argv[1]
if not os.path.exists(input):
	print 'the path specified does not seem to lead to an existing file'
	sys.exit(-1)
output_selection, output_remainder = input+'.selection', input+'.remainder'

if (len(sys.argv) < 3 or sys.argv[2] != 'force') and (os.path.exists(output_selection) or os.path.exists(output_remainder)):
	print 'one or both of the output files (below) already exist'
	print '        ' + output_selection
	print '        ' + output_remainder
	print
	print 'pleasy supply "force" as the second parameter to this script in order to overwrite the existing files'
	sys.exit(-2)

rand_seed = 66123
def rand(lim):
	global rand_seed
	rand_seed = (rand_seed * 32719 + 3) % 32749
	return rand_seed % lim

with open(input,'rt') as f: lines = f.readlines()
all, best = {}, {}
ids = []
for line in lines:
	split = line.strip().split('\t') + [line]
	rating = int(split[2])
	id = split[0]
	if not id in all.keys():
		ids.append(id)	
		all[id] = []
		best[id] = []	
	all[id].append(split);
	if rating == 1:
		best[id].append(split)
selection = []
for id in ids:
	opt = all[id]
	if len(best[id]) > 0:
		opt = best[id]
        choice = rand(len(opt))
	selection.append(opt[choice][3])
remainder = [line for line in lines if not line in selection]

with open(output_selection,'wt') as f: f.writelines(selection)
with open(output_remainder,'wt') as f: f.writelines(remainder)

