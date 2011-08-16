'''
Created on Aug 16, 2011

@author: tass

Command line usage:
treetaggerBatch.py <Directory with corpus files>
'''
from treetaggerIO import TreeTaggerIO, ttDir
import os, sys

def main(args):
    #handling of command line args
    if len(args) != 1:
        print("Usage: treetaggerBatch.py directory")
    else:
        corpusDir = args[0]

        #initialize tagger once
        tagger = TreeTaggerIO(ttDir)
        
        for f in os.listdir(corpusDir):
            f = corpusDir+"/"+f
            #tag text
            print "Tagging "+f
            tagger.process(f, f+".tagged")

if __name__ == "__main__":
    main(sys.argv[1:])
