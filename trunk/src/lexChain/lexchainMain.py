#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 18.07.2011

@author: tass
'''
from lexicalChain import lexChainWSD, finalizeLexChains
import os
import sys
import gzip

import logging
from collections import defaultdict

log = logging.getLogger("lexchain")
log.setLevel(logging.INFO)

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
            "When there was no clear sentence delimiter:"
            if sent:
                sentences.append(sent)
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
    for sentnum, sent in enumerate(sentences):
        if sentnum > 0:
            stream.write("\n\n")
        for wordnum, word in enumerate(sent):
            if wordnum > 0: 
                stream.write("\n")
            word[3] = str(chainDict.get(_lemmaIfAvailable(word), 0))
            stream.write("\t".join(word))
    stream.write("\n")

def run(streamIn, streamOut, chainOutFile):
    termDict = loadTerms("corpus/mesh-terms")
    chainDict = {}
    "statistics"
    chainsTotal = 0
    docCounter = 0
    
    if chainOutFile:
        chainOutStream = open(chainOutFile, "w")
            
    for docId, sentences in readConll(streamIn):
        docCounter += 1
        newSentences = [[(_lemmaIfAvailable(w), w[4]) for w in sentence] for sentence in sentences]
        "We assume there is only one paragraph"
        input = [newSentences]
        senses = lexChainWSD(input, deplural=False, additionalTerms=termDict)
        
        chainWordDict = {}
        for chain in [ch for ch in finalizeLexChains(senses) if len(ch) > 1]:
            chainsTotal += 1
            chainKey = tuple(chain)
            chainId = chainDict[chainKey] = chainDict.get(chainKey, len(chainDict))
            for word in chain:
                chainWordDict[word] = chainId
            if chainOutStream:
                chainOutStream.write(str(chainId) + "|" + str(chainKey)+"\n")
        writeConll(streamOut, sentences, chainWordDict, docId)
        
    if chainOutStream:
        chainOutStream.close()
                
    log.info("Some stats:")
    log.info("  Total chains found:    "+str(chainsTotal))
    log.info("  Unique chains found:    "+str(len(chainDict)))
    log.info("  Number docs:    "+str(docCounter))
    log.info("  Chains/Doc:    "+str(float(chainsTotal)/docCounter))

if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        chainOutStream = None
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