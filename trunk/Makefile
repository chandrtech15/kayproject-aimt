install:	corpus/.created ext/.created

# Run with caution
preprocessing: corpus/test/*.tagged corpus/train/*.tagged

corpus/test/*.tagged: install
	python src/preprocessing/treetaggerBatch.py corpus/test

corpus/train/*.tagged: install
	python src/preprocessing/treetaggerBatch.py corpus/train

corpus/.created:
	make -C corpus
ext/.created:
	make -C ext
