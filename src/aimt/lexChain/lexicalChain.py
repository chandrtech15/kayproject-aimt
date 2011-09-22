#!/usr/bin/python

# Author: Malcolm Augat <maugat1@cs.swarthmore.edu>, 
#   Meggie Ladlow <margarel@cs.swarthmore.edu>

"""
A lexical chain based word sense disambiguator based on the linear time 
algorithm by Galley and McKeown.
Galley, Michel and McKeown, Kathleen. "Improving Word Sense Disambiguation 
In Lexical Chaining." INTERNATIONAL JOINT CONFERENCE ON ARTIFICIAL 
INTELLIGENCE (2003).
"""

from nltk.corpus.reader.wordnet import Synset, WordNetCorpusReader
import logging
import nltk
from collections import defaultdict
N = WordNetCorpusReader(nltk.data.find('corpora/wordnet'))

logging.basicConfig()
log = logging.getLogger("lexchain")
log.setLevel(logging.DEBUG)

class MetaChain:
    """
    mc = MetaChain(lexScorer)

    Stores representations of all possible lexical chains of the words 
    given to it.
    """
    def __init__(self, scoring, additionalTerms={}):
        """
        scoring = a LexScoring object
        
        The maximum wordnet distance used to link two words is equal to the 
        maximum permissible number of WordNext steps as defined in scoring.
        """
        # dict with WordNet offsets or words (strings, edit by tass) as keys and lexical chains (lists) as values
        self.chains = {}
        # dict with strings as keys and lists of LexNodes as values
        # there is one LexNode per sense of the word
        self.words = {}
        # dict of sentence position occurences of a word
        self.sentences = {}
        # dict of paragraph position occurences of a word
        self.paragraphs = {}
        # LexScoring object that computes link weights between LexNodes
        self.scoring = scoring
        # the maximum wordnet distance with which two words can be linked
        # i.e.: a hyperonym is one step, a sibling is two steps (hypernym ->
        # hyponym)
        self.maxdist = self.scoring.maxWNDist()
    
        self.additionalTerms = additionalTerms
    
    def __str__(self):
        """
        Returns a string representation of the class.
        """
        return 'chains: ' + str(self.chains) + "\n" + \
                'words: ' + str(self.words)

    def addChunk(self, chunk, sentpos, parpos):
        word = " ".join(chunk)
        if len(chunk) > 1:
            if N.synsets(word, "n") or word in self.additionalTerms:
                if N.synsets(word, "n"):    log.info("Synsets for "+word)
                self.addWord(word, sentpos, parpos)
            else:
                for word in chunk:
                    self.addWord(word, sentpos, parpos)
        else:
            self.addWord(word, sentpos, parpos)
            

    def addWord(self, word, sentpos, parpos):
        """
        Adds a word to the MetaChain by examining WordNet synsets. Creates 
        links between related words in the MetaChain.

        word = the word to add (a string)
        sentpos = the sentence in which the word occurs, used for text distance
            calculation (int)
        parpos = the paragraph in which the word occurs, used in a similar 
            manner as sentpos (int)
        """
        
        def createLink(lnOld, lnNew, relWeight, type):
            "There is already a link between the two"
            if lnOld.word() == lnNew.word() or lnOld.isLinkedTo(lnNew):
                return
            
            sdist = sentpos-self.sentences[lnNew.word()][-1]
            pdist = parpos-self.paragraphs[lnNew.word()][-1]
            log.debug("added LexLink for "+str(lnOld)+" "+str(lnNew))
            lnOld.linkTo(lnNew, LexLink(relWeight, sdist, pdist, type))
            
            chain = self.chains.get(lnOld.id(), [])
            chain.append(lnNew)
            lnNew.addChain(chain)
            
        def updateWordDist(word):
            # get the nodes for this word
            for ln in self.words[word]:
                # get the links of the LexNode
                for ln2, link in ln.nodeLinks():
                    sdist = sentpos - self.sentences[ln2.word()][-1]
                    if sdist < link.sentDist():
                        pdist = parpos - self.paragraphs[ln2.word()][-1]
                        link.setDist(sdist, pdist)
            
        # add the word to the text position dictionaries
        self.sentences[word] =  self.sentences.get(word, []) + [sentpos]
        self.paragraphs[word] =  self.paragraphs.get(word, []) + [parpos]
        
        wordList = self.words[word] = self.words.get(word, [])
        
        # if the MetaChain has already stored the word, just need to update
        # distances between word occurances
        if wordList:
            updateWordDist(word)
        # else this is a new word
        else:
            for offset, term, dist, type in self.expandWord(word):
                if not offset:
                    if dist == 0:
                        ln = LexNode(word, None)
                        self.chains[word] = [ln]
                        wordList.append(ln)
                    else:
                        if term in self.chains:
                            assert ln
                            createLink(self.chains[term][0], ln, dist, type)
                            log.info("Term connection between "+word+" and "+term)
                else:
                    if dist == 0:
                        # make a LexNode
                        ln = LexNode(word, offset)
                        wordList.append(ln)
                    assert ln
                    # make links to all the synonyms (things in the synset)
                    # of the word
                    if offset in self.chains:
                        for lns in self.chains[offset]:
                            if lns != ln:
                                createLink(ln, lns, dist, type)
                    else:
                        self.chains[offset] = [ln]
                    
    def expandWord(self, word):
        
        def expandLst(lst, alreadySeen, word, dist, type):
            for el in lst:
                if el.offset not in alreadySeen:
                    alreadySeen.add(el.offset)
                    yield el.offset, word, min(dist, self.maxdist-1), type
        
        syns = N.synsets(word, "n")
        if not syns:
            yield None, word, 0, "ident"
            "EDIT by tass: term connections"
            relTerms = self.additionalTerms.get(word, None)
            if relTerms:
                for term in relTerms:
                    if term != word:
                        yield None, term, 1, "term"
        else:
            for syn in syns:
                yield syn.offset, word, 0, "syn"
                alreadySeen = set()
                alreadySeen.add(syn.offset)
                
                hyperBases = [syn]
                hypoBases = [syn]
                for dist in range(1, self.maxdist+1):
                    newHypers = sum([h.hypernyms() for h in hyperBases], [])
                    newHypos = sum([h.hyponyms() for h in hypoBases], [])
                    for el in expandLst(newHypers, alreadySeen, word, dist, "hyper"):
                        yield el
                    for el in expandLst(newHypos, alreadySeen, word, dist, "hypo"):
                        yield el
                    "Do not consider uncles etc"
                    if dist == 1:
                        for el in expandLst(sum([h.hyponyms() for h in newHypers], []), alreadySeen, word, dist, "sibling"):
                            yield el                    
                    hyperBases, hypoBases = newHypers, newHypos
                
                otherRels = [syn.instance_hypernyms, syn.instance_hyponyms, syn.also_sees, syn.member_meronyms, syn.part_meronyms, syn.substance_meronyms, syn.similar_tos, syn.attributes, syn.member_holonyms, syn.part_holonyms, syn.substance_holonyms]
                for rel in otherRels:
                    expandLst(rel(), alreadySeen, word, 1, "unknown")
    
    def disambigAll(self, default=None):
        """
        Returns a dictionary mapping all words in the MetaChain to their best
        WordNet senses.

        default = the sense of the word if it does not appear in wn 
        """
        wsdict = {}
        for word in self.words:
            dis = self.disambig(word)
            wsdict[word] = default if dis == None else dis
        return wsdict
    
    def disambig(self, word):
        """
        Disambiguates a single word by returning the sense with the highest
        total weights on its edges.

        word = the word to disambiguate (string)
        """
        maxscore = -1
        maxsense = None
        if not self.words.has_key(word):
            raise KeyError("%s is not in the MetaChain"%(word))
        for ln in self.words[word]:
            score = self.nodeScore(ln)
            if score > maxscore:
                if maxsense:    maxsense.deleteLinks()
                maxscore = score
                maxsense = ln   # changed by tass: we need lexical node to access the links
            else:
                ln.deleteLinks()
        log.debug("Disambiguating "+str(word)+". Has senses: "+str(self.words[word])+". Chosen: "+str(maxsense))
        return maxsense
                
    def nodeScore(self, ln):
        """
        Computes the score of a LexNode by summing the weights of its edges.

        ln = a LexNode
        """
        score = 0
        for link in ln.links():
            sdist = link.sentDist()
            pdist = link.parDist()
            wndist = link.wnDist()
            score += self.scoring.score(wndist, sdist, pdist)
        return score

class LexScoring:
    """
    sentbins = [1, 3] # sentence distance thresholds for scores
    parbins = [1] # paragraph distance thresholds for scores
    stepscores = [[1.0, 1.0, 0.5, 0.5], \\
                  [1.0, 0.5, 0.3, 0.3]] # a matrix of scores
    scoring = LexScoring(sentbins, parbins, stepscores)

    Used for calculating weights between linked LexNodes.
    In effect LexScoring is a matrix with a number of rows equal to
    the maximum persmissible WordNet distance between two words and a
    number of columns equal to the len(sentbins)+len(parbins)+1. The
    text and WordNet distances for a word are discretized by comparison with
    the thresholds and uniquely determine an index into the stepscores matrix.
    """
    def __init__(self, sentbins, parbins, stepscores):
        """
        sentbins = defines sentence distance thresholds for weights between two 
            words (list of ints)
        parbins = same as the sentbins for paragraphs
        stepscores = each element is a list of weights such that the ith element
            of stepscores corresponds to a list of weights for words with wn 
            distance i (i.e. the first 'row' is for synonyms, second 'row' is 
            for hyperonyms, etc).

            Each row contains a list of numerical weights corresponding to the 
            sentence and paragraph text distance thresholds. Text distances
            greater than the maximum parbins use the weight at index
            len(sentbins)+len(parbins)+1, or 0 if each row is only as long
            as len(sentbins)+len(parbins).
        """
        # sentbins and parbins are lists of bin edges
        self.sbins = sentbins
        self.pbins = parbins
        # stepscores is a list of lists with the ith row representing the
        # weights for words i steps away. Each row should be big enough to
        # fill the bins.
        if not stepscores:
            raise Exception("Scores needed")
        rowlen = len(stepscores[0])
        for row in stepscores:
            if len(row) != rowlen:
                raise Exception("Scores must all be the same length")
        if rowlen < len(sentbins)+len(parbins) or \
                rowlen > len(sentbins)+len(parbins)+1:
            raise Exception("Number of scores does not match number of bins")
        elif rowlen == len(sentbins)+len(parbins):
            self.scores = [row+[0] for row in self.scores]
        else:
            # lists are dangerously referential! make a copy
            self.scores = [row[:] for row in stepscores]

    def score(self, wndist, sdist, pdist):
        """
        Computes and returns the score for a word with the given WordNet 
        distance and text distance (sentence and paragraph distance). Of the
        two text distance measure, the sentence distance is used first, and the
        paragraph distance only considered if the sentence distance is larger
        than the largest sentence threshold. 

        For example, say you had a LexScoring object with sentbins of [1 5] and
        parbins of [1] and gave it distances from two words from a text with 
        really short paragraphs such that their paragraph distance was 2, but 
        the sentence distance was only 4. The sentence thresholds would be 
        applied first and the score would be as for words within 5 sentences, 
        even though the paragraoh distance is greater than the maximum 
        paragraph threshold.
        
        wndist = the WordNet distance (int)
        sdist, pdist = the sentence and paragraph distance respectively (ints)
        """
        # get the row from which the scores will come
        row = self.scores[wndist]
        binned = False
        i = 0
        # see the sentence distance falls into one of the sentence bins
        for sbin in self.sbins:
            if sdist <= sbin:
                binned = True
                break
            i += 1
        # if it doesn't, check the paragraph bins
        if not binned:
            for pbin in self.pbins:
                if pdist <= pbin:
                    binned = True
                    break
                i += 1
        # i will now correspond to the correct bin, which will be the last bin
        # (the default bin) if no bin has been applicable
        score = row[i]
        return score

    def maxWNDist(self):
        """
        Returns the max WordNet distance acceptable between two words. This 
        distance is equal to the number of rows in the scoring matrix.
        """
        return len(self.scores)

class LexNode:
    """
    ln = LexNode('dog', 0)

    Stores the word and a WordNet sense number for that word, the chains in
    which that word appears, and links to related LexNodes.
    """
    def __init__(self, word, sensenum, chains=None):
        """
        word = the word (string)
        sensenum = the wn sense number (int or None)
        chains = list of lexical chains, which are each a list of LexNodes
            (see MetaChain.chains)
        rellinks = list of LexLinks
        """
        # a word (str)
        self.wrd = word
        # the sense of the word this node represents (int)
        self.sensenum = sensenum
        # list of lexical chains
        self.lchains = [] if chains==None else chains
        # list of LexLinks
        self.rellinks = {}
    def __str__(self):
        return 'LexNode('+str(self.wrd)+','+str(self.sensenum)+')'
    def __repr__(self):
        return self.wrd+'_'+str(self.sensenum)
    def __hash__(self):
        return self.sensenum if self.sensenum else self.wrd.__hash__()
    def __eq__(self, other):
        if not isinstance(other, LexNode):  return False
        return other.__hash__() == self.__hash__()
    def word(self):
        """
        Returns the word stored in the LexNode.
        """
        return self.wrd
    def sense(self):
        """
        Returns the wn sense number stored in the LexNode.
        """
        return self.sensenum
    def id(self):
        return self.sensenum if self.sensenum else self.wrd
    def addChain(self, chain):
        """
        Adds a lexical chain to the chains stored in the LexNode.

        chain = the lexical chain to add (a list of LexNodes)
        """
        self.lchains.append(chain)
    def chains(self):
        """
        Returns the lexical chains stored in the LexNode.
        """
        return self.lchains
    def linkTo(self, otherLn, lnkData):
        """
        Adds a link to the links stored in the LexNode.

        link = the LexLink to add
        """
        self.rellinks[otherLn] = lnkData
        otherLn.rellinks[self] = lnkData
    def nodeLinks(self):
        return self.rellinks.iteritems()
    def links(self):
        """
        Returns the LexLinks stored in the LexNode.
        """
        return self.rellinks.itervalues()
    def adjacentNodes(self):
        return self.rellinks.iterkeys()
    def isLinkedTo(self, otherLn):
        return otherLn in self.rellinks
    def deleteLinks(self):
        for node in self.adjacentNodes():
            node.rellinks.pop(self)
        self.rellinks = {}

class LexLink:
    
    linkTypes = set(["hyper", "hypo", "sibling", "syn", "ident", "term", "unknown"])
    
    """
    ll = LexLink(lexNode1, lexNode2, wndist, sentdist, paradist)

    Connects two LexNodes. Stores pointers to each LexNode and stores their 
    text and wn distances.
    """
    def __init__(self, wndist, sdist, pdist, type="unknown"):
        """
        wndist = the wordnet distance between ln1 and ln2 (int)
        sdist, pdist = the shortest text distance between the words stored in 
            ln1 and ln2 (int)
        """
        
        assert type in LexLink.linkTypes
        
        # the wn distance
        self.wndist = wndist
        # the text distances
        self.sdist = sdist
        self.pdist = pdist
        
        self.type = type
    def wnDist(self):
        """
        Returns the WordNet distance between the LexNodes. The wn distance 
        never changes, so there is no corresponding set function.
        """
        return self.wndist
    def sentDist(self):
        """
        Returns the sentence distance between the LexNodes.
        """
        return self.sdist
    def parDist(self):
        """
        Returns the paragraph distance between the LexNodes.
        """
        return self.pdist
    def setDist(self, sdist, pdist):
        """
        Sets the sentence and paragraph distances between the LexNodes.

        sdist = the new sentence distance (int)
        pdist = the new paragraph distance (int)
        """
        self.sdist = sdist
        self.pdist = pdist


def lexChainWSD(taggedText, noWN=None, \
        scoring = LexScoring([1, 3], [1], [[1, 1, .5, .5], [1, .5, .3, .3]]), \
        deplural = False, additionalTerms={}):
    """
    disambigedWords = lexChainWSD(nltk.corpus.brown.tagged_paras(filename))

    Disambiguates a text. Returns a dictionary of words (represented with 
    strings) as keys and integer sense numbers as values. For words that do not
    appear in WordNet, the value stored in the noWN variable will be the sense
    number.

    taggedText = a part of speech tagged text organized as an iterable
        object with each element being a paragraph's text. Each of these 
        paragraphs is an iterable object with sentences as elements. The
        sentences are in turn represented by iterable objects of lists
        or tuples of words and their senses (both strings). Take, for example
        the following sentence:

        [[[('Needless', 'JJ'), ('to', 'TO'), ('say', 'VB'), (',', ','), 
        ('I', 'PPSS'), ('was', 'BEDZ'), ('furious', 'JJ')]]]

    noWN = the sense number for words that do not appear in WordNet. This value
        is not limited to ints. Defaults to None.

    scoring = an optional LexScoring object that defines some parameters
        for the lexical chains. See lexicalChain.LexScoring for more
        information. A default with empirically determined, reasonable values is
        provided.

    deplural = an optional argument (False by default) that does some crude
        noun stemming. If True, then for every word not in WordNet that ends 
        in 's', if the 's'-less version is in WordNet then use that word
        as well.
    """
    mc = MetaChain(scoring, additionalTerms=additionalTerms)
    
    def runOverText():
        sentpos = 0
        parpos = 0
        for para in taggedText:
            for sent in para:
                chunk = []
                chunks = []
                for word, pos in sent:
                    if pos and pos[0] == 'N':
                        chunk.append(word)
                    else:
                        chunks.append(chunk)
                        chunk = []
                for chunk in chunks:
                    mc.addChunk(chunk, sentpos, parpos)
                sentpos += 1
            parpos += 1
            
    runOverText()
    
    disambiged = mc.disambigAll(noWN)
    return disambiged

def finalizeLexChains(disambiged):
    lexChains = []
    alreadyAdded = set()
    for word, ln in disambiged.iteritems():
        if ln in alreadyAdded:  continue
        alreadyAdded.add(ln)
        log.debug(word + " " + str(ln))
        lexChain = [ln]
        for other in ln.adjacentNodes():
            if other == ln or other.sense() != disambiged[other.word()].sense():
                continue
            lexChain.append(other)#.word())
        lexChains.append(lexChain)
    return lexChains 