#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 18.07.2011

@author: tass
'''
from lexicalChain import lexChainWSD, finalizeLexChains
import sys

if __name__ == '__main__':
    
    def readConll(stream):
        sentences = []
        sent = []
        for line in stream:
            line = line.strip()
            "new sentence?"
            if not line:
                sentences.append(sent)
                sent = []
            elems = line.split("\t")
            sent.append(elems)
        return sentences
    
    def writeConll(stream, sentences, chainDict):
        for sentnum, sent in enumerate(sentences):
            if sentnum > 0:
                stream.write("\n\n")
            for wordnum, word in enumerate(sent):
                if wordnum > 0: 
                    stream.write("\n")
                word[3] = chainDict.get(word, 0)
                stream.write("\t".join(word))
    
    def run(streamIn, streamOut):
        sentences = readConll(streamIn)
            
        newSentences = [[(w[2] if w[2] != "<unknown>" else w[1], w[4]) for w in sentence] for sentence in sentences]
        "We assume there is only one paragraph"
        input = [newSentences]
        senses = lexChainWSD(input, deplural=False)
        
        chainDict = {}
        for chainNum, chain in enumerate(finalizeLexChains(senses)):
            if len(chain) == 1: continue
            for word in chain:
                chainDict[word] = chainNum + 1
                
        writeConll(streamOut, sentences, chainDict)
            
run(sys.stdin, sys.stdout)