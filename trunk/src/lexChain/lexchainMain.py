#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 18.07.2011

@author: tass
'''
from lexicalChain import lexChainWSD, finalizeLexChains
import os
import sys

def readConll(stream):
    idLine = None
    sentences = []
    sent = []
    for line in stream:
        line = line.strip()
        "New document?"
        if line.startswith(".I "):
            if sentences:
                yield idLine,sentences
            idLine = line
            sentences = []
        "new sentence?"
        if not line:
            sentences.append(sent)
            sent = []
        elems = line.split("\t")
        sent.append(elems)
    yield idLine,sentences

def writeConll(stream, sentences, chainDict, idLine):
    stream.write(idLine)
    for sentnum, sent in enumerate(sentences):
        if sentnum > 0:
            stream.write("\n\n")
        for wordnum, word in enumerate(sent):
            if wordnum > 0: 
                stream.write("\n")
            word[3] = chainDict.get(word, 0)
            stream.write("\t".join(word))

def run(streamIn, streamOut):
    for docId, sentences in readConll(streamIn):    
        newSentences = [[(w[2] if w[2] != "<unknown>" else w[1], w[4]) for w in sentence] for sentence in sentences]
        "We assume there is only one paragraph"
        input = [newSentences]
        senses = lexChainWSD(input, deplural=False)
        
        chainDict = {}
        for chainNum, chain in enumerate(finalizeLexChains(senses)):
            if len(chain) == 1: continue
            for word in chain:
                chainDict[word] = chainNum + 1
        writeConll(streamOut, sentences, chainDict, docId)

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 0 and len(args) < 3:
        sameFile = False
        "Input file"
        streamIn = open(args[0],"r")
        if len(args) == 2:
            if args[1] == args[0]:
                args[1] += ".tmp"
                sameFile = True
            streamOut = open(args[1],"w")
        else:
            streamOut = sys.stdout
        run(streamIn, streamOut)
        streamIn.close()
        streamOut.close()
        if sameFile:
            os.rename(args[1], args[0])
    else:
        print "Usage: lexchainMain.py conllfile [outputfile]"
        exit(1)