.created: data/test data/train data/dev data/dev.query
	touch .created
data/test: ohsu-trec
	mkdir -p data && chmod +x ../src/preprocessing/reduceCorpusToText.sh && ../src/preprocessing/reduceCorpusToText.sh ohsu-trec/trec9-test/ohsumed.88-91 > data/test
data/train: ohsu-trec
	mkdir -p data && chmod +x ../src/preprocessing/reduceCorpusToText.sh && ../src/preprocessing/reduceCorpusToText.sh ohsu-trec/trec9-train/ohsumed.87 > data/train
data/dev:  data/train data/test
	python ../src/preprocessing/createDev.py < data/train > data/dev && \
	python ../src/preprocessing/createDev.py < data/test >> data/dev
data/dev.query:	data/dev ohsu-trec
	python ../src/preprocessing/instantiateContext.py ohsu-trec/pre-test/qrels.ohsu.test.87.selection ohsu-trec/pre-test/query.ohsu.test.1-43 data/dev > data/dev.queries

ohsu-trec: corpus.tar.gz
	tar -xvf corpus.tar.gz && rm -f corpus.tar.gz
	
corpus.tar.gz:
	wget -O corpus.tar.gz http://trec.nist.gov/data/filtering/t9.filtering.tar.gz
