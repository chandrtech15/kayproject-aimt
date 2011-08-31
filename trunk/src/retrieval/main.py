'''
Created on 31.08.2011

@author: tass
'''
import sys
from treetaggerIO import TreeTaggerIO, ttDir

class DocCollection:
            
    def match(self, query):
        raise NotImplementedError("Please implement in subclass")
    
class Bm25Collection(DocCollection):
    def __init__(self, taggedDocFile):
        pass
    
    def match(self, query):
        counts = {}
        for word, _, lemma in query.getTagged():
            token = lemma if lemma != "<unknown>" else word
            counts[token] = counts.get(token, 0) + 1
        ranking = self.scoreDocs(counts)
        
    def scoreDocs(self, queryTf):
        "Angeliki: Start here with iterating over all docs in the collection"
        "This function should return an ordered list of document IDs (maybe along with their scores)"
        pass
    
    def score(self, docId, queryTf):
        "Copied from Whoosh"
        def bm25(idf, tf, fl, avgfl, B, K1):
            # idf - inverse document frequency
            # tf - term frequency in the current document
            # fl - field length in the current document
            # avgfl - average field length across documents in collection
            # B, K1 - free paramters
            return idf * ((tf * (K1 + 1)) / (tf + K1 * (1 - B + B * (fl / avgfl))))
        
        
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
    
    _, prec, recall = retriever.retrieveBatch()
    print prec, recall
    
    
            
            