'''
Created on 22.09.2011

@author: tass
'''
from aimt.lexChain.lexicalChain import GalleyMcKeownChainer, LexNode
from collections import defaultdict
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize
import unittest

class TestGalleyMcKeown(unittest.TestCase):
    
    def buildChains(self):
        input = '''
        Some patients converted from ventricular fibrillation to organized rhythms by defibrillation-trained ambula13314936nce technicians (EMT-Ds) will refibrillate before
        hospital arrival. The authors analyzed 271 cases of ventricular fibrillation managed by EMT-Ds working without paramedic back-up. Of 111 patients initially converted to organized rhythms, 19 (17%) refibrillated, 11 (58%) of whom were reconverted to perfusing rhythms, including nine of 11 (82%) who had spontaneous pulses prior to refibrillation. Among patients initially converted to organized rhythms, hospital admission rates were lower for patients who refibrillated than for patients who did not (53% versus 76%, P = NS), although discharge rates were virtually identical (37% and 35%, respectively). Scene-to-hospital transport times were not predictively associated with either the frequency of refibrillation or patient outcome. Defibrillation-trained EMTs can effectively manage refibrillation with additional shocks and are not at a significant disadvantage when paramedic back-up is not available.
        '''
        input = input.replace("-\n","")
        input = sent_tokenize(input)
        input = [[pos_tag(word_tokenize(sent)) for sent in input]]
        mc = GalleyMcKeownChainer(data=input)
        return [ch for ch in mc.buildChains() if len(ch) > 1]

    def testUniqueSense(self):
        chains = self.buildChains()
        senses = defaultdict()
        for chain in chains:
            for ln in chain:
                if not ln.getWord() in senses:
                    senses[ln.getWord()] = ln.getSense()
                else:#
                    self.assertEqual(ln.getSense(), senses[ln.getWord()], "One Sense Per Discourse assumption violated: "+str(ln)+" vs. "+str(senses[ln.getWord()]))
    
    def testLexNodeIdentity(self):
        l1 = LexNode(0, "test", 1, 0, 0)
        l2 = LexNode(0, "test", 1, 0, 0)
        l3 = LexNode(1, "test", 1, 0, 0)
        self.assertTrue(l1 == l2)
        self.assertFalse(l1 == l3)
        
    def testEachWordOccursOnlyOnceInChain(self):
        chains = self.buildChains()
        for chain in chains:
            wordIndices = set()
            for ln in chain:
                self.assertTrue(ln.getWordIndex() not in wordIndices)
                wordIndices.add(ln.getWordIndex())
                    
    def testExpandWord(self):
#        mc = GalleyMcKeownChainer()
#        for ln in mc.expandWord("patient",3):
#            print ln
        pass            

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()