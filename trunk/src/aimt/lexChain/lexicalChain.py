#!/usr/bin/python
from Queue import Queue
from collections import defaultdict, OrderedDict
from nltk.corpus.reader.wordnet import Synset, WordNetCorpusReader
import logging
import nltk

# Author: Malcolm Augat <maugat1@cs.swarthmore.edu>, 
#   Meggie Ladlow <margarel@cs.swarthmore.edu>

"""
A lexical chain based getWord getSense disambiguator based on the linear time 
algorithm by Galley and McKeown.
Galley, Michel and McKeown, Kathleen. "Improving Word Sense Disambiguation 
In Lexical Chaining." INTERNATIONAL JOINT CONFERENCE ON ARTIFICIAL 
INTELLIGENCE (2003).
"""

N = WordNetCorpusReader(nltk.data.find('corpora/wordnet'))

logging.basicConfig()
log = logging.getLogger("lexchain")
log.setLevel(logging.DEBUG)

class LexGraph:
    """
    mc = LexGraph(lexScorer)

    Stores representations of all possible lexical chains of the words 
    given to it.
    """
    def __init__(self, data=None, additionalTerms={}):
        """
        scoring = a LexScoring object
        
        The maximum wordnet distance used to link two words is equal to the 
        maximum permissible number of WordNext steps as defined in scoring.
        """
        # dict with WordNet offsets or words (strings, edit by tass) as keys and lexical chains (lists) as values
        self.chains = {}
        # dict with strings as keys and lists of LexNodes as values
        # there is one LexNode per getSense of the getWord
        self.words = defaultdict(set)
        # the maximum wordnet distance with which two words can be linked
        # i.e.: a hyperonym is one step, a sibling is two steps (hypernym ->
        # hyponym)
        self.maxdist = self.scoring.maxWNDist()
    
        self.additionalTerms = additionalTerms
        
        self.sentpos = self.parapos = 0
        
        if data:
            self.feedDocument(data)
    
    def __str__(self):
        """
        Returns a string representation of the class.
        """
        return 'chains: ' + str(self.chains) + "\n" + \
                'words: ' + str(self.words)
    
    def feedDocument(self, paragraphs):
        for para in paragraphs:
            self.feedParagraph(para)
    
    def feedParagraph(self, sentences):
        self.parapos += 1
        for sent in sentences:
            self.feedSentence(sent)
    
    def feedSentence(self, taggedWords):
        self.sentpos += 1
        chunk = []
        chunks = []
        for word, pos in taggedWords:
            if pos and pos[0] == 'N':
                chunk.append(word)
            else:
                chunks.append(chunk)
                chunk = []
        for chunk in chunks:
            self.addChunk(chunk)
            
    def addToChain(self, ln, senseOrToken=None, relWeight=0, type="ident"):
        senseOrToken = ln.getId() if not senseOrToken else senseOrToken
        link = LexLink(relWeight, type)
        try:
            chain = self.chains[senseOrToken]
            chain.linkTo(ln, link)
            log.debug("added "+str(ln)+" to chain")
        except KeyError:
            self.chains[senseOrToken] = chain = MetaChain(ln, link)
            log.debug("NEW chain for "+str(ln)+" and "+str(senseOrToken))
            
    def addChunk(self, chunk):
        word = " ".join(chunk)
        "TODO: why's that?"
        if not word:    return
        if len(chunk) > 1:
            if N.synsets(word, "n") or word in self.additionalTerms:
                self.addWord(word)
            else:
                for word in chunk:
                    self.addWord(word)
        else:
            self.addWord(word)
            

    def addWord(self, word):
        log.debug("Adding "+str(word))
        wordSet = self.words[word]
        
        if wordSet:
            """
            If only one sense per discourse, each word has to be considered only once
            (will get only one set of LexNodes).
            Otherwise, just copy the nodes which are already there and their chain memberships
            (correct?)
            Nope -- copy always. We will handle this later, when building the actual chains
            """
            newWordSet = set()
            for ln in wordSet:
                "This will also copy all chain memberships"
                lnNew = ln.copy()
                newWordSet.add(lnNew)
            self.words[word] = wordSet = newWordSet
        else:
            "expandWord assumption: senses / terms of the word as such are discovered first and returned with dist 0"
            for wnSense, term, dist, type in self.expandWord(word):
                if not wnSense:
                    if dist == 0:
                        ln = LexNode(word, None, self.sentpos, self.parapos)
                        self.addToChain(ln)
                        wordSet.add(ln)
                    else:
                        if term in self.chains:
                            assert ln
                            self.addToChain(ln, term, dist, type)
                            log.info("Term connection between "+word+" and "+term)
                else:
                    if dist == 0:
                        # make a LexNode
                        ln = LexNode(word, wnSense, self.sentpos, self.parapos)
                        wordSet.add(ln)
                        self.addToChain(ln)
                    else:
                        assert ln
                        if wnSense in self.chains:
                            self.addToChain(ln, wnSense, dist, type) 
                    
                    
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
    
    def buildChains(self):
        lexChains = []
        alreadyAdded = set()
        maxDepth = None
        
        "first occurrence of getWord"
        for word in self.words:
            ln = self.words[word][0]
            if ln in alreadyAdded:  continue
            depth = 0
            q = Queue()
            q.put(ln)
            lexChain = []
            while not q.empty() and (not maxDepth or depth <= maxDepth):
                n = q.get()
                if n in alreadyAdded:   continue
                alreadyAdded.add(n)
                lexChain.append(n)
                for other in n.adjacentNodes():
                    q.put(other)
                depth += 1
            lexChains.append(sorted(lexChain, key=lambda ln: self.sentences[ln.getWord()][0]))
        return lexChains


class GalleyMcKeownChainer(LexGraph):
    def __init__(self, scoring=None, data=None, additionalTerms={}):
        """
        scoring = a LexScoring object
        
        The maximum wordnet distance used to link two words is equal to the 
        maximum permissible number of WordNext steps as defined in scoring.
        """
        # LexScoring object that computes link weights between LexNodes
        self.scoring = scoring if scoring else LexScoring([1, 3], [1], [[1, 1, .5, .5], [1, .5, .3, .3]])
        # the maximum wordnet distance with which two words can be linked
        # i.e.: a hyperonym is one step, a sibling is two steps (hypernym ->
        # hyponym)
        self.maxdist = self.scoring.maxWNDist()
        
        LexGraph.__init__(self, data, additionalTerms)
    
    def disambigAll(self, default=None):
        """
        Returns a dictionary mapping all words in the LexGraph to their best
        WordNet senses.
        Deletes redundant links.

        default = the getSense of the getWord if it does not appear in wn 
        """
        wsdict = {}
        for word in self.words:
            dis = self.disambig(word)
            wsdict[word] = default if dis == None else dis
        "Now remove all other LNs from all their lexical chains"
        for word, lns in self.words.iteritems():
            for ln in lns:
                if wsdict[word] != ln:
                    log.debug("Unlink "+str(ln))
                    ln.unlinkAll()
            self.words[word] = [wsdict[word]]
        return wsdict
    
    def disambig(self, word):
        """
        Disambiguates a single getWord by returning the getSense with the highest
        total weights on its edges.

        getWord = the getWord to disambiguate (string)
        """
        
        def updateWordDist(word):
            # get the nodes for this getWord
            for ln in self.words[word]:
                # get the links of the LexNode
                for ln2, link in ln.nodeLinks():
                    sdist = self.sentpos - self.sentences[ln2.getWord()][-1]
                    if sdist < link.sentDist():
                        pdist = self.parapos - self.paragraphs[ln2.getWord()][-1]
                        link.setDist(sdist, pdist)
        
        maxscore = -1
        maxsense = None
        log.debug("Disambiguating "+str(word)+". Has senses: "+str(self.words[word]))
        for ln in self.words[word]:
            score = self.nodeScore(ln)
            if score > maxscore:
                maxscore, maxsense = score, ln
        log.debug("    Chosen: "+str(maxsense))
        return maxsense
                
    def nodeScore(self, ln):
        """
        Computes the score of a LexNode by summing the weights of its edges.

        ln = a LexNode
        """
        score = 0
        "For each meta chain this node is in:"
        for chain, link in ln.getMetaChains():
            "For each LN in that chain"
            for otherLn, _ in chain.getLexNodes():
                "i.e. Same word - one word per discourse, so ignore?"
                "Other possibility: Give points for identity.."
                if otherLn == ln:    continue
                sdist, pdist = ln.getDist(otherLn)
                wndist = link.getWnDist()
                score += self.scoring.score(wndist, sdist, pdist)
        return score
    
    def buildChains(self):
        lexChains = []
        alreadyAdded = set()
        maxDepth = None
        
        "first occurrence of word"
#        for word in self.words:
#            ln = self.words[word][0]
#            if ln in alreadyAdded:  continue
#            depth = 0
#            q = Queue()
#            q.put(ln)
#            lexChain = []
#            while not q.empty() and (not maxDepth or depth <= maxDepth):
#                n = q.get()
#                if n in alreadyAdded:   continue
#                alreadyAdded.add(n)
#                lexChain.append(n)
#                log.debug(n)
#                for other, _ in n.get():
#                    q.put(other)
#                depth += 1
#            lexChains.append(sorted(lexChain, key=lambda ln: ln.getPos()[0]))
        
        return [[ln for ln, _ in ch.getAdjacentNodes()] for ch in self.chains.itervalues()]


class Node:
    def __init__(self):
        self.adjacentNodes = {}
    def linkTo(self, target, link):
        self._typeCheckNode(target)
        self._typeCheckLink(link)
        "What happens when already linked to target? -> ignore, relink"
        self.adjacentNodes[target] = target.adjacentNodes[self] = link
    def unlink(self, target):
        self._typeCheckNode(target)
        del target.adjacentNodes[self]
        del self.adjacentNodes[target]
    def unlinkAll(self):
        nodesToUnlink = list(self.getAdjacentNodes())
        for target, _ in nodesToUnlink:
            self.unlink(target)
        assert len(self.adjacentNodes) == 0
    def isLinkedTo(self, target):
        self._typeCheckNode(target)
        return target in self.adjacentNodes
    def getAdjacentNodes(self):
        """
        Will return an iterator over (node, link) pairs
        """
        return self.adjacentNodes.iteritems()
    def getId(self):
        raise NotImplementedError("Please implement in subclass")
    def _typeCheckNode(self, obj):
        if not isinstance(obj, Node): raise TypeError 
    def _typeCheckLink(self, obj):
        if not isinstance(obj, LexLink): raise TypeError

class MetaChain(Node):
    def __init__(self, firstNode, firstLink):
        self.id = firstNode.getId()
        self.adjacentNodes = OrderedDict()
        self.linkTo(firstNode, firstLink)
    def getId(self):
        return self.id
    def getLexNodes(self):
        return self.getAdjacentNodes()
    def _typeCheckNode(self, obj):
        if not isinstance(obj, LexNode): raise TypeError
    
    def __len__(self):
        return len(self.lst)
    def __getitem__(self, k):
        return self.lst[k]
    def __iter__(self):
        return self.lst.__iter__()
    def __hash__(self):
        return self.getId().__hash__()
    def __eq__(self, other):
        return (False if not isinstance(other, MetaChain) else self.getId() == other.getId())
    def __str__(self):
        return "MetaChain with ID "+str(self.getId())
    def __repr__(self):
        return self.__str__()
    
class LexNode(Node):
    """
    ln = LexNode('dog', 0)

    Stores the getWord and a WordNet getSense number for that getWord, the chains in
    which that getWord appears, and links to related LexNodes.
    """
    def __init__(self, word, sensenum, spos=0, ppos=0):
        Node.__init__(self)
        
        self.word = word
        self.sensenum = sensenum
        
        self.spos = spos
        self.ppos = ppos
    
    def _typeCheckNode(self, obj):
        if not isinstance(obj, MetaChain): raise TypeError
    
    
    def __str__(self):
        return 'LexNode('+str(self.word)+','+str(self.sensenum)+')'
    def __repr__(self):
        return self.word+'_'+str(self.sensenum)
    def __hash__(self):
        return (self.sensenum, self.word).__hash__()
    def __eq__(self, other):
        if not isinstance(other, LexNode):  return False
        return other.word == self.word and other.sensenum == self.sensenum
    def getWord(self):
        """
        Returns the word stored in the LexNode.
        """
        return self.word
    def getSense(self):
        """
        Returns the wn getSense number stored in the LexNode.
        """
        return self.sensenum
    def getId(self):
        return self.sensenum if self.sensenum else self.word
    def copy(self):
        lnNew = LexNode(self.word, self.sensenum, self.spos, self.ppos)
        for target, link in self.getAdjacentNodes():
            lnNew.linkTo(target, link)
        return lnNew
    def getMetaChains(self):
        return self.getAdjacentNodes()
    def getPos(self):
        return self.spos, self.ppos
    def getDist(self, other):
        return abs(self.spos - other.spos), abs(self.ppos - other.spos)

class LexLink:
    
    linkTypes = set(["hyper", "hypo", "sibling", "syn", "ident", "term", "unknown"])
    
    """
    ll = LexLink(lexNode1, lexNode2, wndist, sentdist, paradist)

    Connects two LexNodes. Stores pointers to each LexNode and stores their 
    text and wn distances.
    """
    def __init__(self, wndist=0, type="unknown"):
        """
        wndist = the wordnet distance between ln1 and ln2 (int)
        sdist, pdist = the shortest text distance between the words stored in 
            ln1 and ln2 (int)
        """
        
        assert type in LexLink.linkTypes
        
        # the wn distance
        self.wndist = wndist
        self.type = type
        
    def getWnDist(self):
        """
        Returns the WordNet distance between the LexNodes. The wn distance 
        never changes, so there is no corresponding set function.
        """
        return self.wndist

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
    text and WordNet distances for a getWord are discretized by comparison with
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
        Computes and returns the score for a getWord with the given WordNet 
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
