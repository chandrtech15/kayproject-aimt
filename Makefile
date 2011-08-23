install:	corpus/.created ext/.created

# Run with caution
preprocessing: corpus/data/test.tg corpus/data/train.tg corpus/data/dev.tg

corpus/data/test.tg: install
	python src/preprocessing/treetaggerIO.py ext/tt corpus/data/test corpus/data/test.tg

corpus/data/train.tg: install
	python src/preprocessing/treetaggerIO.py ext/tt corpus/data/train corpus/data/train.tg

corpus/data/dev.tg: install
	python src/preprocessing/treetaggerIO.py ext/tt corpus/data/dev corpus/data/dev.tg

preprocessingServer:
	echo "Fetching preprocessed data from coli.. Please enter your coli username, followed by ENTER:" && read username && scp $username@login.coli.uni-sb.de:/home/CE.shadow/tbarth/kayproject-aimt/corpus/data/*.tg corpus/data/

corpus/.created:
	make -C corpus .created
ext/.created:
	make -C ext .created
