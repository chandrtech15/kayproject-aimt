created:	corpus/created ext/created
preprocessed: created corpus/test/*.tagged corpus/train/*.tagged

corpus/test/*.tagged: created
	python src/preprocessing/treetaggerBatch.py corpus/test

corpus/train/*.tagged: created
	python src/preprocessing/treetaggerBatch.py corpus/train

corpus/created:
	make -C corpus
ext/created:
	make -C ext

