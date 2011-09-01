'''
Created on 31.08.2011

@author: tass
'''
import sys
import re
import math
import operator
import gzip

from treetaggerIO import TreeTaggerIO, ttDir

class DocCollection:
            
    def match(self, query):
        raise NotImplementedError("Please implement in subclass")
    
class Bm25Collection(DocCollection):
    def __init__(self, taggedDocFile, B , K1):
        self.docStats, self.N, self.indexOfDocs, self.lenOfDocs, self.avegD = self.readIntaggedFile(taggedDocFile)
        self.B = B
        self.K1 = K1
    
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
    def readIntaggedFile(self, taggedDocFile, stopWordFile=None):
        "Read in stop word list if given"
        useStopWordList = 0
        if stopWordFile!=None:
            streamIn = open(stopWordFile,"r")
            stopWords = {}
            for word in streamIn:
                stopWords[word.strip("\n")] = 0
                useStopWordList = 1
        
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
        "read line by line file"
        for line in streamIn:
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
            "empty line (\n etc)"
            if not line or line == '\n':
                continue
            sent = line.split('\t')
            word = sent[1+(sent[2]!="<unknown>")] 
            if useStopWordList == 1 and stopWords.has_key(word):
                continue
            "line containing a token"
            docTokens +=1
            if not docStats.has_key(word):
                docStats[word] = {}
            if not docStats[word].has_key(docId):
                docStats[word][docId] = 0
            docStats[word][docId] +=1
        "for last document keep tokens"
        lenOfDocs[docId] = docTokens
        
        return docStats,N, indexOfDocs, lenOfDocs, sum([lenOfDocs[d] for d in lenOfDocs.keys()])/float(N)   
        
    def match(self, query):
        counts = {}
        for word, _, lemma in query.getTagged():
            token = lemma if lemma != "<unknown>" else word
            counts[token] = counts.get(token, 0) + 1
        ranking = self.scoreDocs(counts)
        
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
    
    def __init__(self, queryFile, docCollection, qrelFile):
        self.queries = self.readQueries(queryFile)
        self.collection = docCollection
        self.qrels = self.readQrels(qrelFile)
        
    def retrieve(self, q):
        precQuery, recQuery = 0.0, 0.0
        found = 0
        
        q.preprocess()
        
        matches = self.collection.match(q)
        rel = self.qrels[q.qId]
        
        found = float(sum([1 if m in rel else 0 for m in matches]))
        precQuery = found / len(matches)
        recQuery = found / len(rel)
                        
        return matches, precQuery, recQuery
    
    def retrieveBatch(self):
        results = {}
        
        prec = 0.0
        recall = 0.0
        
        for q in self.queries:
            result = self.retrieve(q)
            prec += result[1]
            recall += result[2]
            results[q.qId] = result
        
        return results, prec / len(self.queries), recall / len(self.queries)
    
    def isRelevant(self, qId, docId):
        return docId in self.qrels[qId]
                        
    def readQrels(self, qrelFile):
        qrels = {}
        with open(qrelFile, "r") as qF:
            for l in qF:
                qId, docId, rel = l.strip().split("\t")
                qrels[qId] = qrels.get(qId, set()).add(docId)
        return qrels
    
    def readQueries(self, queryFile):
        queries = []
        with open(queryFile, "r") as qF:
            lines = [l.strip() for l in qF.readLines()]
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
    
class Query:
    tagger = TreeTaggerIO(ttDir)
    
    def __init__(self, qId=0, query="", dId=0, doc=""):
        self.qId = qId
        self.query = query
        self.dId = dId
        self.doc = doc
        
        self.docTagged = None
        self.queryTagged = None
        
    def preprocess(self):
        if not self.queryTagged:    self.queryTagged = Query.tagger.tagger.TagText(self.query)
        if not self.docTagged:  self.docTagged = Query.tagger.tagger.TagText(self.doc)
        
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
    
    args = sys.argv[1:]
    
    indexFile = args[0]
    queryFile = args[1]
    qrelFile = args[2]
    
    collection = DocCollection(indexFile)
    
    retriever = Retriever(queryFile, collection, qrelFile)
    '''
    For testing it:
    testq = {"diagnosis":1, "design":1, "stool":1}
    rank = Bm25Collection("dev.tg.gz",0.1,0.2)
    rank.printDocStats()
    print rank.scoreDocs(testq)[0] #should be equal to 87196565
    '''
    
    _, prec, recall = retriever.retrieveBatch()
    print prec, recall
