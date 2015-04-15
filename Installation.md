The overall file structure currently looks like this:
  * ./ext: External scripts and applications
  * ./ext/tt: TreeTagger. Will be installed by make
  * ./ext/tt-wrapper: TreeTagger python wrapper. Will be installed by make
  * ./src: Our own code
  * ./src/lexChains/: Python scripts for lexical chains
  * ./src/preprocessing/: Scripts for tagging
  * ./src/preprocessing/splitCorpusIntoFiles.sh: Shell script for splitting corpus files into chunks which are easier to handle
  * ./corpus: The TREC9 filtering task corpus
  * ./corpus/train/: Contains training document chunks (make)
  * ./corpus/test/: Contains test document chunks (make)

The setup is controlled by a bunch of makefiles in /., ext, and corpus. They will download and preprocess the corpus, and also install TreeTagger.
If you add new external packages not included in the subversion repo, please make sure to add the installation commands to one of the makefiles.