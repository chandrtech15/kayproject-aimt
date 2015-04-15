# Intro #

Our data format contains one line per token. Each line is a list of tab-separated items. The items are:


| Column 0: | sentence-local id of the token, starting from 1 |
|:----------|:------------------------------------------------|
| Column 1: | form |
| Column 2: | lemma |
| Column 3: | lexical chain id |
| Column 4: | POS-tag |
| Column 5: | topic id |
| Column 6: | term extraction information -- head word id for a term word, otherwise 0 |

Multiple sentences belonging to the same document are separated by a blank line and every document is preceded by a line of the form ".I `<doc-id>`", specifying the document id.