.created: tt tt-wrapper
	touch .created

tt: 
	mkdir tt && cd tt && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tree-tagger-linux-3.2.tar.gz && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/tagger-scripts.tar.gz && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/install-tagger.sh && \
	wget ftp://ftp.ims.uni-stuttgart.de/pub/corpora/english-par-linux-3.1.bin.gz && \
	sh install-tagger.sh && \
	rm -f ./*.tar.gz

tt-wrapper:
	mkdir tt-wrapper && cd tt-wrapper && \
	svn export -r 19 https://subversion.cru.fr/ttpw/trunk/treetaggerwrapper.py
