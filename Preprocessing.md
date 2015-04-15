# How to run #

  * The TreeTagger wrapper can be anonymously checked out from https://subversion.cru.fr/ttpw

  * The simple class treetaggerIO.py (/src/preprocessing/) can be used to tag files and write the result into a conll09-like file in the following way:
    1. TREETAGGER\_DIR should point to the directory of TreeTagger
```
    #initialize tagger
    myTagger = TreeTaggerIO(TREETAGGER_DIR)
    
    #tag a file
    myTagger.process(INPUT_FILE, OUTPUT_FILE)
```
    1. Or like this on the command line:
```
    treetaggerIO.py treetaggerDir inputFile outFile
```

# Details #

## TreeTagger wrapper ##

The TreeTagger wrapper by default replaces all occurrences of URLs, emails, IP addresses, and DNS names in a preprocessing step. They are replaced by a 'replaced-xxx' (e.g. 'replaced-email') string, followed by an XML tag containing the replaced text as attribute.

This option could be turned off, but after experimenting with it I found that the result returned is not very satisfactory. The e-mail found in the text was split into three: the part before the @-symbol, the @-symbol, and the part following it, while the original TreeTagger would return the e-mail as it is.

If you don't think that replacing is an issue, I would vote for using it. Otherwise the wrapper will have to be modified.

## Output ##

Currently the output produced by the treetaggerIO.py looks like this:

```
1	This	this	_	DT
2	is	be	_	VBZ
3	a	a	_	DT
4	very	very	_	RB
5	short	short	_	JJ
6	text	text	_	NN
7	of	of	_	IN
8	12	@card@	_	CD
9	words	word	_	NNS
10	to	to	_	TO
11	tag	tag	_	VV
12	.	.	_	SENT
```

Where "`_`" stands for unknown/none.