#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 18.07.2011

@author: tass
'''
from lexicalChain import lexChainWSD, finalizeLexChains
from nltk.tag import *
from nltk.tokenize import *

if __name__ == '__main__':
    input = '''Web pages, news articles, blog postings, and other
Internet data contain mentions of named entities such
as people, places, organizations, etc. Names are often
ambiguous: the same name can have many different
meanings. For example, given a text like “They per-
formed Kashmir, written by Page and Plant. Page
played unusual chords on his Gibson.”, how can we
tell that “Kashmir” denotes a song by Led Zeppelin
and not the Himalaya region (and that Page refers
to guitarist Jimmy Page and not to Google founder
Larry Page, and that Gibson is a guitar model rather
than the actor Mel Gibson)?
Establishing these mappings between the mentions
and the actual entities is the problem of named-entity
disambiguation (NED).
If the possible meanings of a name are known up-
front - e.g., by using comprehensive gazetteers such
as GeoNames (www.geonames.org) or knowledge
bases such as DBpedia (Auer07), Freebase (www.
freebase.com), or YAGO (Suchanek07), which
have harvested Wikipedia redirects and disambigua-
tion pages - then the simplest heuristics for name res-
olution is to choose the most prominent entity for a
given name. This could be the entity with the longest
Wikipedia article or the largest number of incoming
links in Wikipedia; or the place with the most inhab-
itants (for cities) or largest area, etc. Alternatively,
one could choose the entity that uses the mention
most frequently as a hyperlink anchor text. For the
example sentence given above, all these techniques
would incorrectly map the mention “Kashmir” to the
Himalaya region. We refer to this suite of methods
as a popularity-based (mention-entity) prior.
Key to improving the above approaches is to con-
sider the context of the mention to be mapped, and
compare it - by some similarity measure - to contex-
tual information about the potential target entities.
For the example sentence, the mention “Kashmir”
has context words like “performed” and “chords” so
that we can compare a bag-of-words model against
characteristic words in the Wikipedia articles of the
different candidate entities (by measures such as co-
sine similarity, weighted Jaccard distance, KL diver-
gence, etc.). The candidate entity with the highest
similarity is chosen. Alternatively, labeled training
data can be harnessed to learn a multi-way classifier,
and additional features like entire phrases, part-of-
speech tags, dependency-parsing paths, or nearby hyperlinks can be leveraged as well. These methods
work well for sufficiently long and relatively clean
input texts such as predicting the link target of a Wi-
kipedia anchor text (Milne08). However, for short or
more demanding inputs like news, blogs, or arbitrary
Web pages, relying solely on context similarity can-
not achieve near-human quality. Similarity measures
based on syntactically-informed distributional mod-
els require minimal context only. They have been
developed for common nouns and verbs (Thater10),
but not applied to named entities.
The key to further improvements is to jointly con-
sider multiple mentions in an input and aim for a col-
lective assignment onto entities (Kulkarni09). This
approach should consider the coherence of the re-
sulting entities, in the sense of semantic relatedness,
and it should combine such measures with the con-
text similarity scores of each mention-entity pair. In
our example, one should treat “Page”, “Plant” and
“Gibson” also as named-entity mentions and aim to
disambiguate them together with “Kashmir”.
Collective disambiguation works very well when a
text contains mentions of a sufficiently large number
of entities within a thematically homogeneous con-
text. If the text is very short or is about multiple, un-
related or weakly related topics, collective mapping
tends to produce errors by directing some mentions
towards entities that fit into a single coherent topic
but do not capture the given text. For example, a text
about a football game between “Manchester” and
“Barcelona” that takes place in “Madrid” may end up
mapping either all three of these mentions onto foot-
ball clubs (i.e., Manchester United, FC Barcelona,
Real Madrid) or all three of them onto cities. The
conclusion here is that none of the prior methods
for named-entity disambiguation is robust enough to
cope with such difficult inputs.
'''
    input = '''
Some patients converted from ventricular fibrillation to organized rhythms by defibrillation-trained ambulance technicians (EMT-Ds) will refibrillate before
hospital arrival. The authors analyzed 271 cases of ventricular fibrillation managed by EMT-Ds working without paramedic back-up. Of 111 patients initially converted to organized rhythms, 19 (17%) refibrillated, 11 (58%) of whom were reconverted to perfusing rhythms, including nine of 11 (82%) who had spontaneous pulses prior to refibrillation. Among patients initially converted to organized rhythms, hospital admission rates were lower for patients who refibrillated than for patients who did not (53% versus 76%, P = NS), although discharge rates were virtually identical (37% and 35%, respectively). Scene-to-hospital transport times were not predictively associated with either the frequency of refibrillation or patient outcome. Defibrillation-trained EMTs can effectively manage refibrillation with additional shocks and are not at a significant disadvantage when paramedic back-up is not available.
'''
    def run(input):
        input = input.replace("-\n","")
        input = sent_tokenize(input)
        input = [[pos_tag(word_tokenize(sent)) for sent in input]]
        senses = lexChainWSD(input, deplural=False)
        return [ch for ch in finalizeLexChains(senses) if len(ch) > 1]
          
    totalChains = []
    with open("../corpus/ohsu-trec/pre-test/ohsumed.87","r") as f:
        next = False
        counter = 1
        for line in f:
            if line.startswith(".W"):
                next = True
            elif next:
                totalChains += run(line.strip())
                next = False
                counter += 1
            if counter > 5:
                break
    
    print len(totalChains)
    totalChains = list(set([tuple(ch) for ch in totalChains]))
    print len(totalChains)
    print totalChains[:100]
    bigrams = []
    for ch in totalChains:
        bigrams.append((None, ch[0]))
        bigrams += [(ch[k-1], ch[k]) for k in xrange(1, len(ch))]
        bigrams.append((ch[-1], None))
    print bigrams
    print len(bigrams)
    print len(set(bigrams))