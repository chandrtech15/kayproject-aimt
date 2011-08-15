created: test train
	touch created

test: ohsu-trec
	mkdir test && chmod +x splitCorpusIntoFiles.sh &&	./splitCorpusIntoFiles.sh ohsu-trec/trec9-test/ohsumed.88-91 100 test/test

train: ohsu-trec
	mkdir train && chmod +x splitCorpusIntoFiles.sh && ./splitCorpusIntoFiles.sh ohsu-trec/trec9-train/ohsumed.87 100 train/train

ohsu-trec: corpus.tar.gz
	tar -xvf corpus.tar.gz && rm -f corpus.tar.gz
	
corpus.tar.gz:
	wget -O corpus.tar.gz http://trec.nist.gov/data/filtering/t9.filtering.tar.gz
