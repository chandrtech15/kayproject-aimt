'''
Created on 31.08.2011

@author: tass
'''

import os
import sys
from pickle import PickleError

"bah. BAH."
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/../../")

from aimt.preprocessing.treetaggerIO import TreeTaggerIO, ttDir
from optparse import OptionParser
import gzip
import math
import operator
from collections import defaultdict
import cPickle as pickle 

class DocCollection:
            
    def match(self, query):
        raise NotImplementedError("Please implement in subclass")
    
class Bm25Collection(DocCollection):
    def __init__(self, taggedDocFile, B=.75 , K1=2.0, stopwordFile=None, threshold=-1):
        self.B = B
        self.K1 = K1
        self.readStopwords(stopwordFile)
        
        self.threshold = threshold
        
        self.docStats, self.N, self.indexOfDocs, self.lenOfDocs, self.avegD = self.readIntaggedFile(taggedDocFile)
    
    def readStopwords(self, stopwordFile):
        self.stopWords = {}
        if stopwordFile:
            with open(stopwordFile,"r") as streamIn:
                for word in streamIn:
                    self.stopWords[word.strip("\n")] = 0
    
    def printDocStats(self):
        print "DOCUMENT STATISTICS"
        print "#####"
        print "Print word frequencies"
        for word in self.docStats:
            print word,"|",
            for docId in self.docStats[word]:
                print docId,":",self.docStats[word][docId],", ",
            print 
        return
        
                 
    def Tf(self, word, docId):
        if not self.docStats.has_key(word):
            return 0
        if not self.docStats[word].has_key(docId):
            return 0
        return self.docStats[word][docId]
    
    def Idf(self, word):
        if not self.docStats.has_key(word):
            n = 0
        else:
            n = len(self.docStats[word].keys())
            
        return math.log((self.N-n+0.5)/(n+0.5))
    
    "stopWordFile: file that has a word in every new line"
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
                word = sent[1+(sent[2]!="<unknown>")]
                if self.stopWords.has_key(word):
                    continue
                "line containing a token"
                docTokens +=1
                if not docStats.has_key(word):
                    docStats[word] = {}
                if not docStats[word].has_key(docId):
                    docStats[word][docId] = 0
                docStats[word][docId] +=1
        finally:
            streamIn.close()
        "for last document keep tokens"
        lenOfDocs[docId] = docTokens
        
        return docStats,N, indexOfDocs, lenOfDocs, sum([lenOfDocs[d] for d in lenOfDocs.keys()])/float(N)   
        
    def match(self, query):
        counts = {}
        for word, _, lemma in query.getTagged():
            token = lemma if lemma != "<unknown>" else word
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
        for word in queryTf.keys():
            s+= ((1.0)*queryTf[word]) * bm25(self.Idf(word),self.Tf(word, docId), self.lenOfDocs[docId], self.avegD, self.B, self.K1)
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
        rel = self.qrels[q.qId]
        
        found = float(sum([1 if m in rel else 0 for m, _ in matches]))
        precQuery = 0.0 if not rel else found / len(matches)
        recQuery = 0.0 if not rel else found / len(rel)
                        
        return matches, precQuery, recQuery
    
    def retrieveBatch(self):
        results = {}
        
        prec = 0.0
        recall = 0.0
        
        for q in self.queries:
            print "Retrieving query "+q.qId
            
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
            print "Loaded queries from cache" 
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
    parser.add_option("-s","--stopwords",help="Name of a stopword file (one word per line) -- words therein will be filtered out from queries and documents")
    parser.add_option("--qrels",help="Name of a qrels file (queryId \t docId \t relevance) -- if given, retrieval results will be evaluated. Otherwise the script will only return the docIds")
    parser.add_option("--K1",help="K1 param of BM25. Default = 2.0", default=2.0, type="float")
    parser.add_option("--B",help="B param of BM25. Default = .75", default=.75, type="float")
    parser.add_option("--threshold",help="Min value of BM25 score to include document in retrieval set. Default: 3.0", default=3.0, type="float")
    parser.add_option("--queryCache",help="Completely processed query file will be stored on disk under given path as pickled python object. Subsequent runs will use it from there.", default=None)
    #parser.add_option("-q","--queries",help="Name of a query file (queryId \n Query \n DocId \n context) -- if given, will be used as query input. Otherwise the last positional argument(s) are taken to be queries")
    options, args = parser.parse_args()
    
    try:
        docFile = args[0]
        queryFile = args[1]
    except IndexError:
        parser.print_help()
        exit(1)
    
    collection = Bm25Collection(docFile, B=options.B, K1=options.K1, stopwordFile=options.stopwords, threshold=options.threshold)
    
    retriever = Retriever(queryFile, collection, options.qrels, queryCache=options.queryCache)
    results, prec, recall = retriever.retrieveBatch()
    f = 0 if prec == 0 or recall == 0 else (2* prec * recall) / (prec + recall)
    print "Results: \t %s \nPrecision, Recall, F1: \t %f %f %f" % (str(results), prec, recall, f)
    
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
