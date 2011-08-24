read -p "Fetching preprocessed data from coli.. Please enter your coli username, followed by ENTER: " NAME && \
	scp "${NAME}"@login.coli.uni-sb.de:/home/CE.shadow/tbarth/kayproject-aimt/corpus/data/*.tg.gz corpus/data/ && gunzip corpus/data/*.tg.gz
