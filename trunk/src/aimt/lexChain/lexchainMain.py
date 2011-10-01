#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 18.07.2011

@author: tass
'''
from collections import defaultdict
from optparse import OptionParser
import gzip
import logging
import os
import sys
from lexicalChain import GalleyMcKeownChainer

log = logging.getLogger("lexchain")

def _lemmaIfAvailable(word):
    return word[2] if word[2] != "<unknown>" else word[1]

def loadTerms(termFilename):
    termDict = defaultdict(set)
    with open(termFilename, "r") as tFile:
        for line in tFile:
            line = line.strip()
            parts = line.split("|")
            if len(parts) > 1:
                commaPos = parts[0].find(", ") 
                if commaPos > -1:
                    parts[0] = parts[0][commaPos+2] + " " + parts[0][:commaPos]
                parts = [t.lower() for t in parts]
                parts = set(parts)
                for term in parts:
                    termDict[term].update(parts)
    return termDict

def readConll(stream):
    idLine = None
    sentences = []
    sent = []
    for line in stream:
        line = line.strip()
        if not line:
            "new sentence"
            sentences.append(sent)
            sent = []
        elif line.startswith(".I "):
            "When there was no clear sentence delimiter (i.e. empty line):"
            if sent:
                sentences.append(sent)
                sent = []
            "new document"
            if sentences:
                yield idLine,sentences
            idLine = line
            sentences = []
        else:
            "normal token"
            elems = line.split("\t")
            sent.append(elems)
    yield idLine,sentences

def writeConll(stream, sentences, chainDict, idLine):
    stream.write(idLine+"\n")
    for sent in sentences:
        for wordnum, word in enumerate(sent):
            if wordnum > 0: 
                stream.write("\n")
            word[3] = str(chainDict.get(_lemmaIfAvailable(word), 0))
            stream.write("\t".join(word))
        stream.write("\n\n")

def run(algo, streamIn, streamOut):
    termDict = loadTerms("corpus/mesh-terms")
    chainDict = {}
    input = []
    "statistics"
    chainsTotal = 0
    docCounter = 0
    sentCounter = 0
    tokenNgrams = defaultdict(int)
    avgChainLength = 0
    
    for docId, sentences in readConll(streamIn):
        
        docCounter += 1
        sentCounter += len(sentences)
        newSentences = [[(_lemmaIfAvailable(w), w[4]) for w in sentence] for sentence in sentences]
        
        "We assume there is only one paragraph"
        input = [newSentences]
        
        lcAlgo = GalleyMcKeownChainer(additionalTerms=termDict)
        lcAlgo.feedDocument(input)
        
        for chain in [ch for ch in lcAlgo.buildChains() if len(ch) > 1]:
            streamOut.write(str(chain)+"\n")
    
    withoutOrder = defaultdict(int)
    ngrams = defaultdict(int)
    for ch in chainDict.iterkeys():
        avgChainLength += len(ch)
        ngrams[(None, ch[0], ch[1])] += 1
        for ngram in [(ch[k-2], ch[k-1], ch[k]) for k in xrange(2, len(ch))]:
            ngrams[ngram] += 1
        ngrams[(ch[-2], ch[-1], None)] += 1
        ch = set(ch)
        ch = sorted(list(ch))
        withoutOrder[tuple(ch)] += 1
    avgChainLength /= float(len(chainDict))        
    
    
    log.info("Some stats:")
    log.info("Token N-grams with count > 1:")
    selection = sorted([(ngram, count) for ngram, count in tokenNgrams.iteritems() if count > 1], key=lambda i: i[1])
    #log.info(str(selection))
    log.info(str(len(selection))+" vs. "+str(len(tokenNgrams))+" total")
        
    log.info("N-grams with count > 1:")
    selection = sorted([(ngram, count) for ngram, count in ngrams.iteritems() if count > 1], key=lambda i: i[1])
    #log.info(str(selection))
    log.info(str(len(selection))+" vs. "+str(len(ngrams))+" total")
            
#    log.info("Without order with count > 1:")
#    selection = sorted([(ngram, count) for ngram, count in withoutOrder.iteritems() if count > 1], key=lambda i: i[1])
#    log.info(str(selection))
    
    log.info("  Total chains found:    "+str(chainsTotal))
    log.info("  Unique chains found:    "+str(len(chainDict)))
    log.info("  Number docs:    "+str(docCounter))
    log.info("  Number sentences:    "+str(sentCounter))
    log.info("  Chains/Doc:    "+str(float(chainsTotal)/docCounter))
    log.info("  Avg Chain Length:    "+str(avgChainLength))

if __name__ == '__main__':
    
    parser = OptionParser(usage=sys.argv[0]+" [options] <> <file with queries>", description="This script reads in a CONLL file, searches for lexical chains and prints them to stdout. Two LC algorithms are supported currently (see below)")
    parser.add_option("-a", "--lcAlgo",help="LC algorithm to use -- either galley (default) or silber", default="galley")
    parser.add_option("-v","--verbose",help="Verbose output?", default=False, action="store_true")
    #parser.add_option("-q","--queries",help="Name of a query file (queryId \n Query \n DocId \n context) -- if given, will be used as query input. Otherwise the last positional argument(s) are taken to be queries")
    options, args = parser.parse_args()
    
    if options.verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)
    
    try:
        "Input file"
        if args[0].endswith(".gz"):
            streamIn = gzip.open(args[0], "r")
        else:
            streamIn = open(args[0],"r")
        streamOut = sys.stdout
        run(options.lcAlgo, streamIn, streamOut)
        streamIn.close()
        streamOut.close()
    except IndexError:
        parser.print_help()
        exit(1)