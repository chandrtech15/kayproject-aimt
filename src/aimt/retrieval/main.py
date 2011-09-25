'''
Created on 31.08.2011

@author: tass
'''


from collections import defaultdict
from optparse import OptionParser
from pickle import PickleError
import cPickle as pickle
import gzip
import logging
import math
import operator
import os
import sys

log = logging.getLogger("retrieval")

"bah. BAH."
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/../../")

from aimt.lexChain.lexchainMain import readConll, _lemmaIfAvailable
from aimt.lexChain.lexicalChain import GalleyMcKeownChainer
from aimt.preprocessing.treetaggerIO import TreeTaggerIO, ttDir

class DocCollection:
            
    def match(self, query):
        raise NotImplementedError("Please implement in subclass")
    
    def readStopwords(self, stopwordFile):
        self.stopWords = {}
        if stopwordFile:
            with open(stopwordFile,"r") as streamIn:
                for getWord in streamIn:
                    self.stopWords[getWord.strip("\n")] = 0
    
class LexChainCollection(DocCollection):
    '''
    classdocs
    '''

    def __init__(self, taggedDocFile, stopwordFile=None, bmThreshold=3.0, lcThreshold=3.0):
        self.docChains = {}
        self.chainer = GalleyMcKeownChainer(wnMaxdist=3)
        self.readStopwords(stopwordFile)
        with open(taggedDocFile, "r") as stream:
            for idLine, sentences in readConll(stream):
                docId = idLine[3:]
                sentences = [[(_lemmaIfAvailable(w), w[4]) for w in sentence] for sentence in sentences]
                sentences = [[w for w in sentence if w not in self.stopWords] for sentence in sentences]
                self.chainer.feedDocument([sentences])
                self.chainer.disambigAll()
                #print sentences
                #print "\n".join([str(ch) for _, ch in self.chainer.chains.iteritems() if len(ch) > 0])
                self.docChains[docId] = set([chId for chId, ch in self.chainer.chains.iteritems() if len(ch) > 0])
        self.bm25 = Bm25Collection(taggedDocFile, stopwordFile=stopwordFile, threshold=bmThreshold)
        self.threshold = lcThreshold
        
    def match(self, query):
        candidateRanking = self.bm25.match(query)
        
        docScores = defaultdict(int)
        for word, tag, lemma in query.docTagged + query.queryTagged:
            word = lemma if lemma != "<unknown>" else word
            if tag and tag[0] == "N" and word not in self.stopWords:
                for wnSense, term, dist, type in self.chainer.expandWord(word):
                    for docId, bmScore in candidateRanking:
                        doc = self.docChains[docId]
                        #docScores[docId] = bmScore
                        if wnSense in doc or term in doc:
                            docScores[docId] += 1
        from numpy import mean, std
        vals = list(docScores.values())
        threshold = mean(vals)
        sd = std(vals)
        threshold = self.threshold#threshold + 0 * sd
        #print threshold
        ranking = sorted([(docId, score) for docId, score in docScores.iteritems() if score > threshold], key=lambda (k,v): v, reverse=True)
        return ranking
    
class Bm25Collection(DocCollection):
    def __init__(self, taggedDocFile, B=.75 , K1=2.0, stopwordFile=None, threshold=-1):
        self.B = B
        self.K1 = K1
        self.readStopwords(stopwordFile)
        
        self.threshold = threshold
        
        self.docStats, self.N, self.indexOfDocs, self.lenOfDocs, self.avegD = self.readIntaggedFile(taggedDocFile)
    
    def printDocStats(self):
        print "DOCUMENT STATISTICS"
        print "#####"
        print "Print getWord frequencies"
        for getWord in self.docStats:
            print getWord,"|",
            for docId in self.docStats[getWord]:
                print docId,":",self.docStats[getWord][docId],", ",
            print 
        return
        
                 
    def Tf(self, getWord, docId):
        if not self.docStats.has_key(getWord):
            return 0
        if not self.docStats[getWord].has_key(docId):
            return 0
        return self.docStats[getWord][docId]
    
    def Idf(self, getWord):
        if not self.docStats.has_key(getWord):
            n = 0
        else:
            n = len(self.docStats[getWord].keys())
            
        return math.log((self.N-n+0.5)/(n+0.5))
    
    def readIntaggedFile(self, taggedDocFile):
        docStats = {}
        N = 0
        indexOfDocs = {}
        lenOfDocs = {}
        firstDoc = 1
        docId = None
        docTokens = 0
        " Open file depending on ending"
        if taggedDocFile.endswith(".gz"):
            streamIn = gzip.open(taggedDocFile, "r")
        else:
            streamIn = open(taggedDocFile,"r")
        try:
            "read line by line file"
            for line in streamIn:
                line = line.strip()
                "Beginning of document"
                if line.startswith(".I"):
                    if firstDoc == 0:
                        lenOfDocs[docId] = docTokens
                    docTokens = 0
                    firstDoc = 0
                    docId = line[3:]
                    indexOfDocs[docId] = 0.0
                    N += 1
                    continue
                "empty line"
                if not line:
                    continue
                sent = line.split('\t')
                getWord = sent[1+(sent[2]!="<unknown>")]
                if self.stopWords.has_key(getWord):
                    continue
                "line containing a token"
                docTokens +=1
                if not docStats.has_key(getWord):
                    docStats[getWord] = {}
                if not docStats[getWord].has_key(docId):
                    docStats[getWord][docId] = 0
                docStats[getWord][docId] +=1
        finally:
            streamIn.close()
        "for last document keep tokens"
        lenOfDocs[docId] = docTokens
        
        return docStats,N, indexOfDocs, lenOfDocs, sum([lenOfDocs[d] for d in lenOfDocs.keys()])/float(N)   
        
    def match(self, query):
        counts = {}
        for getWord, _, lemma in query.getTagged():
            token = lemma if lemma != "<unknown>" else getWord
            if token in self.stopWords:
                continue
            counts[token] = counts.get(token, 0) + 1
        ranking = [(docId, score) for docId, score in self.scoreDocs(counts) if score > self.threshold]
        return ranking
        
    def scoreDocs(self, queryTf):
        "Angeliki: Start here with iterating over all docs in the collection"
        "This function should return an ordered list of document IDs (maybe along with their scores)"
        for docId in self.indexOfDocs.keys():
            self.indexOfDocs[docId] = self.score(docId,queryTf)
            
        return sorted(self.indexOfDocs.iteritems(), key=operator.itemgetter(1),reverse=True)
        
    
    def score(self, docId, queryTf):
        def bm25(idf, tf, fl, avgfl, B, K1):
            # idf - inverse document frequency
            # tf - term frequency in the current document
            # fl - field length in the current document
            # avgfl - average field length across documents in collection
            # B, K1 - free paramters
            return idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + B * (fl / avgfl))))
        s = 0;
        for getWord in queryTf.keys():
            s+= ((1.0)*queryTf[getWord]) * bm25(self.Idf(getWord),self.Tf(getWord, docId), self.lenOfDocs[docId], self.avegD, self.B, self.K1)
        return s
        
        
        
class Retriever:
    
    def __init__(self, queryFile, docCollection, qrelFile, queryCache=None):
        self.queries = self.readQueries(queryFile, queryCache)
        self.collection = docCollection
        self.qrels = self.readQrels(qrelFile)
        
    def retrieve(self, q):
        q.preprocess()
        
        '''
        Currently, this evaluation does not consider the rank. 
        So we either need to find a score threshold or a fixed number of max docs.
        I'd prefer a threshold, implemented in match.
        '''
        matches = self.collection.match(q)
        matches = [m for m in matches if m[0] != q.dId]
        
        rel = self.qrels[q.qId]
        
        found = float(sum([1 if m in rel else 0 for m, _ in matches]))
        precQuery = 0.0 if not matches else found / len(matches)
        recQuery = 0.0 if not matches else found / len(rel)
                        
        return matches, precQuery, recQuery
    
    def retrieveBatch(self):
        results = {}
        
        prec = 0.0
        recall = 0.0
        
        for q in self.queries:
            log.info("Retrieving query "+q.qId)
            
            result = self.retrieve(q)
            prec += result[1]
            recall += result[2]
            results[q.qId] = result
        
        return results, prec / len(self.queries), recall / len(self.queries)
    
    def isRelevant(self, qId, docId):
        return docId in self.qrels[qId]
                        
    def readQrels(self, qrelFile):
        qrels = defaultdict(set) 
        if qrelFile:
            with open(qrelFile, "r") as qF:
                for l in qF:
                    qId, docId, _ = l.strip().split("\t")
                    qrels[qId].add(docId)
        return qrels
    
    def readQueries(self, queryFile, cacheFile):
        queries = self.loadQueriesFromCache(cacheFile)
        if queries:
            log.info("Loaded queries from cache") 
            return queries
        with open(queryFile, "r") as qF:
            lines = [l.strip() for l in qF.readlines()]
            lNumber = 0
            while lNumber < len(lines):
                if lines[lNumber].startswith(".Q"):
                    q = Query(lines[lNumber][3:], lines[lNumber+1], lines[lNumber+2][3:], lines[lNumber+3])
                    queries.append(q)
                    lNumber += 4 
                elif not lines[lNumber]:
                    lNumber += 1
                    continue
                else:
                    raise ValueError("Query file has incorrect format (unexpected line: "+str(lNumber)+": "+lines[lNumber]+") - expected .Q or empty") 
        return queries
    
    def loadQueriesFromCache(self, cacheFile):
        if not cacheFile:   return []
        try:
            with open(cacheFile) as f:
                return pickle.load(f)
        except EOFError:
            return []
        except IOError, PickleError:
            return []
        
    def saveQueriesToCache(self, cacheFile):
        if not cacheFile:   return
        with open(cacheFile,"w") as f:
            pickle.dump(self.queries, f)
    
    
class Query:
    tagger = TreeTaggerIO(ttDir)
    
    def __init__(self, qId=0, query="", dId=0, doc=""):
        self.qId = qId
        self.query = query
        self.dId = dId
        self.doc = doc
        
        self.docTagged = None
        self.queryTagged = None
        
    def tag(self, txt):
        return [entry.split("\t") for entry in Query.tagger.tagger.TagText(txt)]
        
    def preprocess(self):
        if not self.queryTagged:
            self.queryTagged = self.tag(self.query) 
        if not self.docTagged:  
            self.docTagged = self.tag(self.doc)
        
    def getTagged(self):
        return self.docTagged + self.queryTagged



if __name__ == '__main__':
    '''
        Input: 
            - Document Collection (consisting of an index structure, mapping features onto Doc IDs)
            - List of queries (query + context)
        Processing:
            - Apply preprocessing on Query, get intermediate representation
            - Match query on index, get document id
        Output:
            - Lists of relevant document IDs for all queries
    '''
    
    parser = OptionParser(usage=sys.argv[0]+" [options] <document collection> <file with queries>")
    parser.add_option("-s","--stopwords",help="Name of a stopword file (one getWord per line) -- words therein will be filtered out from queries and documents")
    parser.add_option("--qrels",help="Name of a qrels file (queryId \t docId \t relevance) -- if given, retrieval results will be evaluated. Otherwise the script will only return the docIds")
    parser.add_option("--K1",help="K1 param of BM25. Default = 2.0", default=2.0, type="float")
    parser.add_option("--B",help="B param of BM25. Default = .75", default=.75, type="float")
    parser.add_option("--bmThreshold",help="Min value of BM25 score to include document in retrieval set. Default: 3.0 for bm25, -16 for lexchain", type="float")
    parser.add_option("--lcThreshold",help="Min value of LexChain score to include document in retrieval set. Default: 11", default=11.0, type="float")
    parser.add_option("--queryCache",help="Completely processed query file will be stored on disk under given path as pickled python object. Subsequent runs will use it from there.", default=None)
    parser.add_option("--retrModel",help="Retrieval model to use -- either bm25 (default) or lexchain", default="bm25")
    parser.add_option("-v","--verbose",help="Verbose output?", default=False, action="store_true")
    #parser.add_option("-q","--queries",help="Name of a query file (queryId \n Query \n DocId \n context) -- if given, will be used as query input. Otherwise the last positional argument(s) are taken to be queries")
    options, args = parser.parse_args()
    
    try:
        docFile = args[0]
        queryFile = args[1]
    except IndexError:
        parser.print_help()
        exit(1)
        
    if options.verbose:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logging.getLogger("lexchain").setLevel(loglevel)
    logging.getLogger("retrieval").setLevel(loglevel)
    
    if options.retrModel == "bm25":
        collection = Bm25Collection(docFile, B=options.B, K1=options.K1, stopwordFile=options.stopwords, threshold=options.bmThreshold if options.bmThreshold else 3)
    elif options.retrModel == "lexchain":
        collection = LexChainCollection(docFile, stopwordFile=options.stopwords, bmThreshold=options.bmThreshold if options.bmThreshold else -16, lcThreshold=options.lcThreshold)
    
    retriever = Retriever(queryFile, collection, options.qrels, queryCache=options.queryCache)
#    for t in xrange(-1,20):
#        for b in xrange(-20, 20, 2):
#            collection.bm25.threshold = b
#            collection.threshold = t
#            results, prec, recall = retriever.retrieveBatch()
#            f = 0 if prec == 0 or recall == 0 else (2* prec * recall) / (prec + recall)
#            print "%d,%d,%.3f,%.3f,%.3f"%(b,t,prec,recall,f)
#            #print "Results: Precision, Recall, F1: \t %f %f %f" % (prec, recall, f)
    
    results, prec, recall = retriever.retrieveBatch()
    f = 0 if prec == 0 or recall == 0 else (2* prec * recall) / (prec + recall)
    print "Prec, Recall, F for "+options.retrModel+":"
    print "%.3f,%.3f,%.3f"%(prec,recall,f)
    
    retriever.saveQueriesToCache(options.queryCache)
    
#    args = sys.argv[1:]
#    
#    indexFile = args[0]
#    queryFile = args[1]
#    qrelFile = args[2]
#    
#    collection = DocCollection(indexFile)
#    

    '''
    For testing it:
    '''
#    testq = {"diagnosis":1, "design":1, "stool":1}
#    rank = Bm25Collection("corpus/data/dev.tg",0.1,0.2)
#    rank.printDocStats()
#    print rank.scoreDocs(testq)[0] #should be equal to 87196565
