install:	corpus/.created ext/.created

# Run with caution
preprocessing: corpus/data/test.tg corpus/data/train.tg corpus/data/dev.tg

corpus/data/test.tg: install
	python src/aimt/preprocessing/treetaggerIO.py ext/tt corpus/data/test corpus/data/test.tg

corpus/data/train.tg: install
	python src/aimt/preprocessing/treetaggerIO.py ext/tt corpus/data/train corpus/data/train.tg

corpus/data/dev.tg: install
	python src/aimt/preprocessing/treetaggerIO.py ext/tt corpus/data/dev corpus/data/dev.tg

preprocessingServer:
	./loadFromServer.sh

corpus/.created:
	make -C corpus .created
ext/.created:
	make -C ext .created
