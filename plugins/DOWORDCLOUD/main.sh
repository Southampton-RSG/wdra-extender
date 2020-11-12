#!/bin/sh

SAN=/tmp/san.$$
IMAGE=./wordcloud.png

IN=$1

# prepare a list of words in the tweets (see also DOTEXTTABLE)
# note - the KWIC file needs to use all the words, not just the non-stopwords, so
# don't remove them from this list

jq -r -M -f $BIN/sanitised.jq $IN |
tr -cd '	-~' |
sed -e 's/[^A-Za-z0-9 ]/ /' > $SAN
#it was -e 's/[^A-Za-z0-9]*$//' but I'm confused. and shouldnt there be a g?

#create the wordcloud
wordcloud_cli --text $SAN --imagefile wordcloud.png --background white --width 1024 --height 764 --stopwords $BIN/STOPWORDS.100

exit 0
