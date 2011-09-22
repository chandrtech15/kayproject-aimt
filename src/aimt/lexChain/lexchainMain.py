#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 18.07.2011

@author: tass
'''
from lexicalChain import constructMc, buildChains
import os
import sys
import gzip

import logging
from collections import defaultdict

log = logging.getLogger("lexchain")
log.setLevel(logging.INFO)

def _lemmaIfAvailable(getWord):
    return getWord[2] if getWord[2] != "<unknown>" else getWord[1]

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
        for wordnum, getWord in enumerate(sent):
            if wordnum > 0: 
                stream.write("\n")
            getWord[3] = str(chainDict.get(_lemmaIfAvailable(getWord), 0))
            stream.write("\t".join(getWord))
        stream.write("\n\n")

def run(streamIn, streamOut, chainOutFile):
    termDict = loadTerms("corpus/mesh-terms")
    chainDict = {}
    input = []
    "statistics"
    chainsTotal = 0
    docCounter = 0
    sentCounter = 0
    tokenNgrams = defaultdict(int)
    tokensTotal = 0
    avgChainLength = 0
    
    chainOutStream = None
    if chainOutFile:
        chainOutStream = open(chainOutFile, "w")
            
    for docId, sentences in readConll(streamIn):
        
        docCounter += 1
        sentCounter += len(sentences)
        newSentences = [[(_lemmaIfAvailable(w), w[4]) for w in sentence] for sentence in sentences]
        
        for ch in newSentences:
            ch = [w for w,_ in ch]
#            tokenNgrams[(None, ch[0], ch[1])] += 1
#            for ngram in [(ch[k-2], ch[k-1], ch[k]) for k in xrange(2, len(ch))]:
#                tokenNgrams[ngram] += 1
#            tokenNgrams[(ch[-2], ch[-1], None)] += 1
            tokensTotal += len(ch)
        
        "We assume there is only one paragraph"
        input = [newSentences]
        
        senses = constructMc(input, deplural=False, additionalTerms=termDict)
        
        chainWordDict = {}
        for chain in [ch for ch in buildChains(senses) if len(ch) > 1]:
            chainsTotal += 1
            chainKey = tuple(chain)
            chainId = chainDict[chainKey] = chainDict.get(chainKey, len(chainDict))
            for getWord in chain:
                chainWordDict[getWord] = chainId
            if chainOutStream:
                chainOutStream.write(str(chainId) + "|" + str(chainKey)+"\n")
    
        writeConll(streamOut, sentences, chainWordDict, docId)
        
    if chainOutStream:
        chainOutStream.close()
        
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
    try:
        args = sys.argv[1:]
        chainOutStream = None
        chainOutFile = None
        if args[0] == "-chainout":
            chainOutFile = args[1]
            args = args[2:]
        if len(args) > 0 and len(args) < 3:
            sameFile = False
            "Input file"
            if args[0].endswith(".gz"):
                streamIn = gzip.open(args[0], "r")
            else:
                streamIn = open(args[0],"r")
            if len(args) == 2:
                if args[1] == args[0]:
                    args[1] += ".tmp"
                    sameFile = True
                if args[1].endswith(".gz"):
                    streamOut = gzip.open(args[1],"w")
                else:
                    streamOut = open(args[1],"w")
            else:
                streamOut = sys.stdout
            run(streamIn, streamOut, chainOutFile)
            streamIn.close()
            streamOut.close()
            if sameFile:
                os.rename(args[1], args[0])
        else:
            raise IndexError
    except IndexError:
        print "Usage: lexchainMain.py [-chainout <file>] conllfile [outputfile]"
        exit(1)