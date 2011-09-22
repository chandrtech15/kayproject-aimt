#!/usr/bin/env python
import sys
import io
import os
import re

if len(sys.argv) < 4:
	print '\tusage: instantiateContext.py <qrels file> <query file> <data file>'
	print '\texample: ./src/preprocessing/instantiateContext.py corpus/ohsu-trec/pre-test/qrels.ohsu.test.87 corpus/ohsu-trec/pre-test/query.ohsu.test.1-43 corpus/data/dev'
	sys.exit(0)

try:
	qrelsFile = sys.argv[1]
	queryFile = sys.argv[2]
	docFile = sys.argv[3]
	for file in [qrelsFile, queryFile, docFile]:
		if not os.path.exists(file):
			raise Exception('file "' + file + '" not found')

	with open(qrelsFile,'rt') as f: 
		qrels = [line.strip().split('\t') for line in f.readlines()]
	
	queries = {}
	with open(queryFile,'rt') as f:
		query = None 
		modeDesc = False
		for line in f.readlines():
			line = line.strip()
			if re.match('<top>', line):
				query = {}
				modeDesc = False
			elif re.match('</top>', line):
				queries[query['num']] = query
				query = None
				modeDesc = False
			elif re.match('<num>', line):
				query['num'] = line.split()[-1]
				modeDesc = False
			elif re.match('<title>', line):
				query['title'] = line[8:]
				modeDesc = False
			elif re.match('<desc>', line):
				modeDesc = True
			elif modeDesc:
				query['desc'] = line
			elif len(line) > 0:
				raise Exception('query file format invalid')

	docs = {}
	with open(docFile,'rt') as f:
		getId = None
		for line in f.readlines():
			line = line.strip()
			if re.match('\\.I', line):
				getId = line[3:]
			elif getId:
				docs[getId] = line
				getId = None
			elif len(line) > 0:
				raise Exception('data file format invalid')
	
	for rel in qrels:
		queryId, docId, rank = rel
		print '.Q ' + queryId
		print queries[queryId]['desc']
		print '.I ' + docId
		print docs[docId]
		print
except:
	raise
