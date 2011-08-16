'''
Created on Aug 10, 2011

@author: Iliana

Usage:
#initialize tagger
aTagger = TreeTaggerIO(TREETAGGER_DIR)
    
#tag a file
aTagger.process(INPUT_FILE, OUTPUT_FILE)

Command line usage:
treetaggerIO.py treetaggerDir inputFile outFile
'''
import treetaggerwrapper
import sys

class TreeTaggerIO:
    
    def __init__(self, ttdir):
        '''
        Build a TreeTagger wrapper
        '''
        self.tagger = treetaggerwrapper.TreeTagger(TAGLANG='en',TAGDIR=ttdir)

    def process(self, inFile, outFile):
        '''
        Tag the text in inFile using TreeTagger
        and write output to outFile
        '''
        input = open(inFile, 'r')
        ttoutput = self.tagger.TagText(input.read()) #, notagurl=True,
                #notagemail=True,notagip=True,notagdns=True) 
                #uncommented opts do not work properly
        input.close()
    
        #output
        self.write_file(ttoutput, outFile)
        
    def write_file(self, ttoutput, outFile):
        '''
        Write the output of TreeTagger to a file in
        a format similar to Conll2009 format
        '''
        outF = open(outFile, 'w')
        sep = '\t'
        none = '_'
        id = 1
        
        for entry in ttoutput:
            if not entry.startswith("<rep"):
                w, t, l = entry.split()
                outF.write(str(id) + #id
                           sep + w + #word
                           sep + l + #lemma
                           sep + none + #plemma=none
                           sep + t + #pos
                           "\n")
            
                if t == 'SENT':
                    outF.write("\n")
                    id = 1
                else: id+=1
            
        print "done"    
        outF.close()

def main(args):
    #handling of command line args
    if len(args) != 3:
        print("Usage: treetaggerIO.py treetaggerDir inputFile outFile")
    else:
        #initialize tagger once
        tagger = TreeTaggerIO(args[0])
    
        #tag text
        tagger.process(args[1], args[2])

if __name__ == "__main__":
    main(sys.argv[1:])
    