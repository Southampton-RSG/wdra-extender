#!/bin/sh
TMPHASH=/tmp/ht.$$
TMPWORD=/tmp/wd.$$

IN=$1

echo 'Hashtag	Freq		Word	Freq' > language.csv

#the json has a specific list of hashtags. count them
jq -r -f $BIN/hashtags.jq $IN | grep . | tr '[A-Z]\011' '[a-z]\012' | sort | uniq -c | awk '{printf("%s\t%s\n",$2,$1)}' > $TMPHASH

# the json has a column of sanitised text (no accounts URLs or hashtags. just words.
# deconstruct it into a list of words, remove the stop words and count them
# no stemming. could use NTLK but didn't bother.
jq -r -M -f $BIN/sanitised.jq $IN | sed -e 's/[^ -}]//g' | tr '[A-Z] ' '[a-z]\012' | sed -e 's/[^a-z].*//' | grep . | sort | join -v 1 - $BIN/STOPWORDS.100 |
uniq -c | sort -rn | sed -e 's/^  *//' -e 's/ /	/' -e '/^1	/d' -e 's/\(.*\)	\(.*\)/\2	\1/' > $TMPWORD

#smush these two tables together but don';t forget that they're unequal lengths so pad those rows out.
paste -d '' $TMPHASH $TMPWORD | sed -e 's/^/			/' -e 's//		/' >> language.csv

rm -f $TMPHASH $TMPWORD
