#!/usr/bin/python
from Queue import Queue
from collections import defaultdict, OrderedDict
from nltk.corpus.reader.wordnet import Synset, WordNetCorpusReader
import logging
import nltk
from types import NotImplementedType

N = WordNetCorpusReader(nltk.data.find('corpora/wordnet'))

logging.basicConfig()
log = logging.getLogger("lexchain")
log.setLevel(logging.DEBUG)


class Node:
    """ Base class for nodes in the LexGraph. """
    def __init__(self):
        self.adjacentNodes = {}
    def linkTo(self, target, link):
        """ Creates a undirected edge between this node and some other node.
        
        @param target: the other node
        @param link: LinkData instance containing arbitrary data related to the edge 
        """
        self._typeCheckNode(target)
        self._typeCheckLink(link)
        "What happens when already linked to target? -> ignore, relink"
        self.adjacentNodes[target] = target.adjacentNodes[self] = link
    def unlink(self, target):
        """ Removes edge between this node and other node.
        
        @param: other Node
        """
        self._typeCheckNode(target)
        del target.adjacentNodes[self]
        del self.adjacentNodes[target]
    def unlinkAll(self):
        """ Removes all edges of this node. """
        nodesToUnlink = list(self.getAdjacentNodes())
        for target, _ in nodesToUnlink:
            self.unlink(target)
        assert len(self.adjacentNodes) == 0
    def isLinkedTo(self, target):
        """ @return: True if this node shares an edge with target """
        self._typeCheckNode(target)
        return target in self.adjacentNodes
    def getAdjacentNodes(self):
        """ 
        @return: an iterator over the nodes linked to this one. Elements of the iterable are (Node, LinkData) tuples.
        """
        return self.adjacentNodes.iteritems()
    def getId(self):
        """ @return: int, unique ID of this node. """
        raise NotImplementedError("Please implement in subclass")
    
    def _typeCheckNode(self, obj):
        if not isinstance(obj, Node): raise TypeError 
    def _typeCheckLink(self, obj):
        if not isinstance(obj, LinkData): raise TypeError

class MetaChain(Node):
    """ A type of node representing word senses (roughly).
    
    Is linked to a set of LexNode instances which are lexically related to the sense represented by the MetaChain.
    The nodes are ordered by the time of their insertion into the chain.  
    """ 
    def __init__(self, firstNode, firstLink):
        """
        firstNode = LexNode defining the sense this chain represents
        firstLink = Link data """  
        self.id = firstNode.getId()
        self.adjacentNodes = OrderedDict()
        self.linkTo(firstNode, firstLink)
    def getId(self):
        """ Returns ID which is the sense of this chain """
        return self.id

    """ Alias for getAdjacentNodes() """
    getLexNodes = Node.getAdjacentNodes
    
    def asList(self):
        """ Returns list view on items """
        return self.adjacentNodes.items()
            
    def _typeCheckNode(self, obj):
        if not isinstance(obj, LexNode): raise TypeError
    
    """ Some definitions to use MetaChain like a tuple """
    def __len__(self):
        return len(self.adjacentNodes)
    def __getitem__(self, k):
        return self.adjacentNodes[k]
    def __iter__(self):
        return self.adjacentNodes.iteritems()
    def __hash__(self):
        return self.getId().__hash__()
    def __eq__(self, other):
        return (False if not isinstance(other, MetaChain) else self.getId() == other.getId())
    def __str__(self):
        return str(self.getId())+":"+str([node for node, _ in self.getLexNodes()])+")"
    def __repr__(self):
        return self.__str__()
    
class LexNode(Node):
    
    """ Representation of a word token, its position in the document and its (supposed) sense.
    
    Will be linked to MetaChains.
    
    Thanks to: 
    @author: Malcolm Augat
    @author: Margaret Ladlow
    and their Galley/McKeown implementation for inspiration.
    """
    def __init__(self, wordIndex, word, sensenum, spos=0, ppos=0):
        """
        @param wordIndex: position of the word in the document
        @param word: the word string
        @param sensenum: some sense id
        @param spos: number of the sentence this token is in
        @param ppos: number of the paragraph this token is in
        """
        Node.__init__(self)
        
        self.word = word
        self.sensenum = sensenum
        self.wordIndex = wordIndex
        
        self.spos = spos
        self.ppos = ppos
    
    def _typeCheckNode(self, obj):
        if not isinstance(obj, MetaChain): raise TypeError
    
    
    def __str__(self):
        return '%s_%s_%d'%(self.word,self.sensenum,self.wordIndex)
    def __repr__(self):
        return self.__str__()
    def __hash__(self):
        return (self.sensenum, self.word, self.wordIndex).__hash__()
    def __eq__(self, other):
        if not isinstance(other, LexNode):  return False
        return other.word == self.word and other.sensenum == self.sensenum and other.wordIndex == self.wordIndex
    def getWord(self):
        """ @return: word string """
        return self.word
    def getSense(self):
        """ @return: sense ID, int """
        return self.sensenum
    def getId(self):
        """ @return: sense ID, int """
        return self.sensenum if self.sensenum else self.word
    def getWordIndex(self):
        """ @return: Word index, int """
        return self.wordIndex
    def copy(self):
        """ Makes a copy of this node and all of its chain memberships. 
        Will insert the copy into each chain this node is a member of.
        
        @return: The new LexNode instance """
        lnNew = LexNode(self.wordIndex, self.word, self.sensenum, self.spos, self.ppos)
        for target, link in self.getAdjacentNodes():
            lnNew.linkTo(target, link)
        return lnNew
    """ Alias for getAdjacentNodes() """
    getMetaChains = Node.getAdjacentNodes
    
    def getPos(self):
        """ @return: Tuple of sentence and paragraph number of this node """
        return self.spos, self.ppos
    def getDist(self, other):
        """
        @param other: LexNode to which the distance is computed  
        @return: Tuple of distances between sentence and paragraph positions of this and another node. """
        return abs(self.spos - other.spos), abs(self.ppos - other.spos)

class LinkData:
    
    class Type:
        """ Simple enum-like class """
        count = 7
        IDENT, SYN, HYPER, HYPO, SIBLING, TERM, OTHER  = xrange(count)
        @classmethod
        def validate(cls, val):  
            if not 0 <= val <= cls.count:   raise TypeError(str(val)+" is not a valid LinkData.Type")
            
    """  Container object storing information about a link (edge) between two Nodes
        (i.e. LexNode and MetaChain)
    """
    def __init__(self, lexDist=0, type=Type.OTHER):
        '''
        @param lexDist: the lexical distance between the nodes (usually WordNet tree distance)
        @param type: Type of the relation
        '''
        LinkData.Type.validate(type)
        
        self.lexDist = lexDist
        self.type = type
        
    def getLexDist(self):
        """
        @return: the lexical distance between the nodes
        """
        return self.lexDist
    
    def getType(self):
        """
        @return: Type of the relation
        """
        return self.type
    
class LexGraph:
    """
    Base class for lexical chaining algorithms. 
    Comprises a collection of intermediate chain representations (MetaChains) and methods to iterate over / expand word tokens.
    Handles the creation of a "lexical graph", a set of interconnected lexical items.
    It is up to the subclasses to implement the scoring and final chaining components.
    
    @invariant: All senses of the word seen before the current one are represented as their own MetaChain, i.e. each word 'owns' a MetaChain
    @postcondition: If there is a lexical relationship between two words, the word positioned further in the text is linked to the MetaChain of the first word  
    """
    def __init__(self, data=None, additionalTerms={}, wnMaxdist=3):
        self.reset()
        
        self.maxdist = wnMaxdist
    
        self.additionalTerms = additionalTerms
        
        if data:
            self.feedDocument(data)
    
    def reset(self):
        """ (Re-)Initializes all instance vars. """
        
        """ @ivar chains: Dict mapping MetaChain IDs onto MetaChain instances """ 
        self.chains = {}
        """ @ivar words: Dict mapping word strings onto sets of LexNode instances -- there should be one LexNode for each word instance and possible sense"""
        self.words = defaultdict(set)
        self.wordInstances = []
        """ @ivar sentpos: Sentence number """
        """ @ivar parapos: Paragraph number """ 
        self.sentpos = self.parapos = self.wordpos = 0
        
        """ Unknown lemmas: Mapping them onto integer IDs TODO """
        self.unknownLemmas = {}
    
    def __str__(self):
        return 'chains: ' + str(self.chains) + "\n" + \
                'words: ' + str(self.words)
    
    def feedDocument(self, paragraphs):
        self.reset()
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
            
    def makeLink(self, ln, type, chain=None, lexDist=0):
        '''
        To be overridden by subclasses wishing to implement specific linking behaviour
        (such as additional scoring)
        '''
        return LinkData(lexDist, type)
    
    def idForUnknownLemma(self, lemma):
        id = self.unknownLemmas.get(lemma)
        if not id:
            id = len(self.unknownLemmas)
            self.unknownLemmas[lemma] = id
        return id 
    
    def addToChain(self, ln, senseOrToken=None, lexDist=0, type=LinkData.Type.IDENT):
        senseOrToken = ln.getId() if not senseOrToken else senseOrToken
        try:
            chain = self.chains[senseOrToken]
            link = self.makeLink(ln, type, chain, lexDist)
            chain.linkTo(ln, link)
            log.debug("added "+str(ln)+" to chain "+str(chain))
        except KeyError:
            link = self.makeLink(ln, type, None, lexDist)
            self.chains[senseOrToken] = chain = MetaChain(ln, link)
            
    def addChunk(self, chunk):
        word = " ".join(chunk)
        word = word.lower()
        
        if not word:    return
        if len(chunk) > 1:
            if N.synsets(word, "n") or word in self.additionalTerms:
                "If whole chunk available as term or in WN"
                self.addWord(word)
            else:
                "Else: Headword acc to heuristic"
                self.addWord(chunk[-1])
        else:
            self.addWord(word)
            

    def addWord(self, word):
        self.wordpos += 1
        
        log.debug("Adding "+str(word)+" at "+str(self.wordpos))
        wordSet = set()
        self.wordInstances.append(wordSet)
    
        "expandWord assumption: senses / terms of the word as such are discovered first and returned with dist 0"
        for wnSense, term, dist, type in self.expandWord(word):
            if not wnSense:
                id = self.idForUnknownLemma(term)
                if dist == 0:
                    ln = LexNode(self.wordpos, word, None, self.sentpos, self.parapos)
                    self.addToChain(ln)
                    wordSet.add(ln)
                else:
                    if term in self.chains:
                        assert ln
                        self.addToChain(ln, term, dist, type)
                        log.info("Term connection between "+word+" and "+term)
            else:
                if dist == 0:
                    ln = LexNode(self.wordpos, word, wnSense, self.sentpos, self.parapos)
                    wordSet.add(ln)
                    self.addToChain(ln)
                else:
                    assert ln
                    if wnSense in self.chains:
                        self.addToChain(ln, wnSense, dist, type)
        
        self.words[word].update(wordSet)
                    
                    
    def expandWord(self, word, maxDist=None, inclOtherRels=False):
        
        maxDist = maxDist if maxDist else self.maxdist
        
        def expandLst(lst, alreadySeen, word, dist, type):
            for el in lst:
                if el.offset not in alreadySeen:
                    alreadySeen.add(el.offset)
                    yield el.offset, word, dist, type
        
        syns = N.synsets(word, "n")
        if not syns:
            yield None, word, 0, LinkData.Type.IDENT
            relTerms = self.additionalTerms.get(word, None)
            if relTerms:
                for term in relTerms:
                    if term != word:
                        yield None, term, 1, LinkData.Type.TERM
        else:
            for syn in syns:
                yield syn.offset, word, 0, LinkData.Type.SYN
                alreadySeen = set()
                alreadySeen.add(syn.offset)
                
                hyperBases = [syn]
                hypoBases = [syn]
                for dist in range(1, maxDist):
                    newHypers = sum([h.hypernyms() for h in hyperBases], [])
                    newHypos = sum([h.hyponyms() for h in hypoBases], [])
                    for el in expandLst(newHypers, alreadySeen, word, dist, LinkData.Type.HYPER):
                        yield el
                    for el in expandLst(newHypos, alreadySeen, word, dist, LinkData.Type.HYPO):
                        yield el
                    "Do not consider uncles etc"
                    if dist == 1:
                        for el in expandLst(sum([h.hyponyms() for h in newHypers], []), alreadySeen, word, dist, LinkData.Type.SIBLING):
                            yield el                    
                    hyperBases, hypoBases = newHypers, newHypos
                
                if inclOtherRels:
                    otherRels = [syn.instance_hypernyms, syn.instance_hyponyms, syn.also_sees, syn.member_meronyms, syn.part_meronyms, syn.substance_meronyms, syn.similar_tos, syn.attributes, syn.member_holonyms, syn.part_holonyms, syn.substance_holonyms]
                    for rel in otherRels:
                        expandLst(rel(), alreadySeen, word, 1, LinkData.Type.OTHER)
    
    def getRelBetweenNodes(self, ln1, ln2):
        """ Assuming that both, ln1 and ln2, have been processed and added to their respective MetaChain,
        this method will determine the reason (i.e. relation type) why ln2 has been added to ln1. This is the relation between the two nodes.
        If ln2 is not in ln1's MetaChain, there is no relation. 
        
        @param ln1: LexNode
        @param ln2: LexNode
        """  
        if ln1.getWord() == ln2.getWord():    return LinkData.Type.IDENT
        if ln1.getSense() == ln2.getSense():    return LinkData.Type.SYN
        assert ln1.getId() in self.chains and ln2.getId() in self.chains
        ln1Chain = self.chains[ln1.getId()]
        ln2Chain = self.chains[ln2.getId()]
        "We might need to try both, depending on which LN has been processed first"
        try:    return ln1Chain[ln2].getType()
        except KeyError:
            try:    return ln2Chain[ln1].getType()
            except KeyError:    return None
    
    def buildChains(self):
        raise NotImplementedError("To be implemented by subclasses")

""" A lexical chain based word sense disambiguator based on the linear time 
algorithm by Galley and McKeown.
Galley, Michel and McKeown, Kathleen. "Improving Word Sense Disambiguation 
In Lexical Chaining." INTERNATIONAL JOINT CONFERENCE ON ARTIFICIAL 
INTELLIGENCE (2003).

This implementation is inspired (and the LexScoring component was written) by:
@author: Malcolm Augat <maugat1@cs.swarthmore.edu>,
@author: Meggie Ladlow <margarel@cs.swarthmore.edu> 
"""
class GalleyMcKeownChainer(LexGraph):
    
    def __init__(self, scoring=None, data=None, additionalTerms={}, wnMaxdist=3):
        LexGraph.__init__(self, data=data, additionalTerms=additionalTerms, wnMaxdist=wnMaxdist)
    
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
                if wsdict[word].getSense() != ln.getSense():
                    log.debug("Unlink "+str(ln))
                    ln.unlinkAll()
            self.words[word] = [wsdict[word]]
        return wsdict
    
    def disambig(self, word):
        """
        Disambiguates a single word by returning the sense with the highest
        total weights on its edges.

        @param word: the word to disambiguate (string)
        """
        maxscore = -1
        maxsense = None
        log.debug("Disambiguating "+str(word)+". Has senses: "+str(self.words[word]))
        for ln in self.words[word]:
            score = self.calcNodeScore(ln)
            if score > maxscore:
                maxscore, maxsense = score, ln
        log.debug("    Chosen: "+str(maxsense))
        return maxsense
                
    def calcNodeScore(self, ln):
        """
        Computes the score of a LexNode by summing the weights of its edges.

        @param ln: LexNode
        """
        score = 0
        "For each meta chain this node is in:"
        for chain, _ in ln.getMetaChains():
            "For each LN in that chain"
            for otherLn, _ in chain.getLexNodes():
                "Do not score nodes belonging to the same word token!"
                if otherLn.getWordIndex() == ln.getWordIndex():    continue
                sdist, pdist = ln.getDist(otherLn)
                score += self.score(self.getRelBetweenNodes(ln, otherLn), sdist, pdist)
        return score
    
    def score(self, rel, sd, pd):
        '''  Implementation of scoring matrix given by Galley & McKeown 2003
        @param rel: relation type
        @param sd: sentence dist
        @param pd: paragraph dist 
        @return: float, score
        '''
        if rel == LinkData.Type.IDENT or rel == LinkData.Type.SYN:
            if sd <= 3: return 1
            return .5
        if rel == LinkData.Type.HYPER or rel == LinkData.Type.HYPO:
            if sd <= 1: return 1
            if sd <= 3: return .5
            return .3
        if rel == LinkData.Type.SIBLING:
            if sd <= 1: return 1
            if sd <= 3: return .3
            if pd <= 1: return .2
            return 0
        return 0
    
    def buildChains(self):
        self.disambigAll()
        return [[ln for ln, _ in ch.getAdjacentNodes()] for ch in self.chains.itervalues()]
    
class SilberMcCoyChainer(LexGraph):
    class LinkData(LinkData):
        def __init__(self, prevNode, type):
            self.prevNode = prevNode
            LinkData.__init__(self, 0, type)
    
    def __init__(self, data=None, additionalTerms={}):
        LexGraph.__init__(self, data, additionalTerms, wnMaxdist=30)
        
    def makeLink(self, ln, type, chain=None, lexDist=0):
        """ Set pointer to previous node in chain, create linkdata object.
        @param ln: lex node to be linked
        @param type: relation type
        @param chain: lexical chain ln is to be linked to. Default None: ln is first node in chain.
        @param lexDist: lexical distance between node and chain
        @return: LinkData instance   
        """
        lnPre = None
        if chain:
            "If not -> first node in chain"
            chainLst = chain.asList()
            lnPre = None
            for pos in xrange(-1, -len(chainLst)):
                lnPre, _ = chainLst[pos]
                if lnPre.getWordIndex() != ln.getWordIndex():
                    "We have found a predecessor which is not the same occurrence"
                    break
            
        lnk = SilberMcCoyChainer.LinkData(lnPre, type)
        return lnk
    
    def score(self, rel, sd, pd):
        '''  Implementation of scoring matrix given by Silber & McCoy 2000
        @param rel: relation type
        @param sd: sentence dist
        @param pd: paragraph dist 
        @return: float, score
        '''
        if rel == LinkData.Type.IDENT or rel == LinkData.Type.SYN:  return 1
        if rel in (LinkData.Type.HYPER, LinkData.Type.HYPO):
            if sd <= 1: return 1
            return .5
        if rel == LinkData.Type.SIBLING:
            if sd <= 1: return 1
            if sd <= 3: return .3
            if pd == 0: return .2
            return 0
        return 0
        
    def buildChains(self):
        """ Restrict each lex node to the chain it contributes to most - 
        the resulting chains are the final ones.
        
        @return: list of chains - list of lists of LexNodes"""
        chainScores = defaultdict(float)
        toUnlink = []
        for lns in self.wordInstances:
            score = 0.0
            maxScore, maxChain, maxLn = -1, None, None
            for ln in lns:
                for chain, link in ln.getMetaChains():
                    if link.prevNode:
                        relType = self.getRelBetweenNodes(ln, link.prevNode)
                        sd, pd = ln.getDist(link.prevNode)
                        score = self.score(relType, sd, pd)
                    else:
                        score = self.score(LinkData.Type.IDENT, 0, 0)
                    if score >= maxScore:
                        "Handle ties -- prefer lower WN offsets"
                        if not maxChain or score > maxScore or isinstance(chain.getId(), str) or chain.getId() < maxChain.getId():
                            if maxChain:
                                "Old maxChain"
                                toUnlink.append((maxChain, maxLn))
                            maxScore, maxChain, maxLn = score, chain, ln
                        else:
                            toUnlink.append((chain, ln))
                    else:
                        toUnlink.append((chain, ln))
            log.debug("Picked "+str(maxLn)+" in "+str(maxChain)+" with "+str(maxScore))
            chainScores[chain] += maxScore
        
        for chain, ln in toUnlink:
            log.debug("Unlinking "+str(ln)+" from "+str(chain))
            chain.unlink(ln)
                
        chainsScored = [ch for ch, _ in sorted(chainScores.iteritems(), key=lambda (k,v): v)] 
        
        return [[ln for ln, _ in ch.getAdjacentNodes()] for ch in chainsScored]
    
    def buildChainsAlternative(self):
        '''
        According to Hollingsworth/Teufel 2005:
        Compute total score for each chain, rank chains, remove nodes in strongest chain from all other chains, repeat
        
        TODO
        '''
        chainsToConsider = list(self.chains.itervalues())
        
        maxScore, maxChain = -1, None
        for chain in chainsToConsider:
            score = 0
            for _, lnk in chain:
                score += lnk.score
            "Handle ties -- prefer lower WN offsets"
            if score >= maxScore:
                if not maxChain or score > maxScore or isinstance(chain.getId(), str) or chain.getId() < maxChain.getId():
                    maxScore, maxChain = score, chain
        return [maxChain]
#        for node, _ in maxChain:
#            for otherChain, _ in node.getMetaChains():
#                if otherChain != maxChain:
#                    node.unlink(otherChain)
            
        
        
        
        
        