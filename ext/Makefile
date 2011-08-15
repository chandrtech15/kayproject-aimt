created: tt
	touch created

tt: 
	mkdir tt && cd tt && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tree-tagger-linux-3.2.tar.gz && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tagger-scripts.tar.gz && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/install-tagger.sh && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/english-par-linux-3.1.bin.gz && \
	sh install-tagger.sh && \
	rm -f ./*.tar.gz
