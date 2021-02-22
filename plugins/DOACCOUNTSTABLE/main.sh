#!/bin/sh
PATH=$PATH:/usr/local/bin/
TMP=/tmp/tmp.$$
OUT0=/tmp/o0.$$
OUT1=/tmp/o1.$$
OUT2=/tmp/o2.$$
UJS=/tmp/ujs.$$
TABL=/tmp/tl.$$
TABR=/tmp/tr.$$
RES=/tmp/res.$$
RES2=/tmp/res2.$$
EDGES=/tmp/net.$$
D3NODES=/tmp/nodes.$$
D3EDGES=/tmp/edges.$$
ACTIV=/tmp/pass.$$

PRE=$BIN/network_pre.htx
POST=$BIN/network_post.htx

PYTHON=python3
MODULARITYSCRIPT=$BIN/modularity.py
MODS=/tmp/mod.$$

#NB this script is run from a temporary directory. any created files in . will be
#zipped up and returned to the user
D3=./network.html
CSVEDGES=./edges.csv

TWEETDATA=$1

export LC_ALL=C

#OK folks. The accounts table is in two parts - left and right.
#The left part (TABL) contains data about the way that accounts contribute to the conversation.
#They are either authors of tweets, or they are mentioned in tweets (that includes being replied to).
#All that informatyion comes from the tweet json.
#When Twitter returns data about a tweet, it includes information about the author.
#That's so the Twitter Web app can show off its dropdown panels when you hover over someone's profile icon.
#However, it doesn't include any information about the accounts who are mentioned. We need to grab that separately.

# file $1 aka $TWEETDATA is the json tweet data
# file $TMP is one record per tweet <count of appearances><tab><author><tab><mentionedaccounts>...
# file $OUT1 is one record per author <author><tab><count of tweets><tab><sum of all tweet appearances>
# file $OUT2 is one record per mentioned account <account><tab><count of tweets><tab><sum of all tweet appearances>
# file $OUT0 is a list of all account names - author or mentioned
# file $TABL is a table of all the accounts with columns for how often they authored tweets or were mentioned
# THAT just recreates the data that we had in the original javasceript client software.


echo "Account	Author	Author+Retweets	Mentions	Mentions+Retweets	Name	Description	Location	URL	Followers	Friends	Statuses	Registration" > accounts.csv

  jq -r -f $BIN/accounts.jq $TWEETDATA > $TMP
  cut -f 1-2 $TMP | $BIN/SUMBYKEY -S -b > $OUT1
  cut -f 1,3-999 $TMP | grep '	.' | awk -F '	' '{for(c=2;c<=NF;c++)if($c!="")printf("%s\t%s\n",$1,$c)}' | $BIN/SUMBYKEY -S -b |
     sed -e 's/	/	|/'> $OUT2

  cut -f1 $OUT1 $OUT2 | sort -u | grep -v '^[0-9][0-9]*$' > $OUT0
  #OUT0 may contain usernames (screennames) consisting entirely of digits. These aren't valid screen names,
  #and they bodge up TWARC users, by sorting to the top and making it think it has a list of ids not names
  #they also bodge up the network file becaue javascript can't tell the difference between a string and an integer
  #TODO: put the grep-v onto the output of the jq command above

  join -t '	' -a 1 $OUT0 $OUT1 | join -t '	' -a 1 - $OUT2 |
  sed -e '/^[^	]*	|/s/|/		/' -e 's/|//' -e 's/$/		/' |
  cut -f 1-5 > $TABL

# TABL just recreates the data that we had in the original javascript client software.
# now we want to get all the supplementary data about all the accounts - authors or mentioned
# technically, we could get most of it for the authors from the original TWARC tweet data
# but not for the non-authors. So we're getting all the data for all the accounts from scratch
# using twarc.

  test -f 00USERS.json && cat 00USERS.json>$UJS || twarc --config $BIN/TWARC.config --log $BIN/TWARC.log users $OUT0 > $UJS
  jq -r -f $BIN/users.jq $UJS | sed -e 's/"/``/g' | sort > $TABR

# now $TABR contains all the extra data for each account to be pasted onto the original $TABL
# to form the final result $RES

  join -t '	' -a 1 $TABL $TABR | sort > $RES
#the sort seems necessary to stop the final join (with $MODS) blowing up. Can't see why.
  #cat $RES

# that was too simple. all rows need to have the same number of columns or cvs2xlsx will terminate
# we need to pad out rows of misssing/disappeared accounts or cvs2xlsx will terminate
# these two lines just replace the `cat`
  maxcols=`awk -F '	' '{if(NF>max)max=NF}END{print max}' $RES`
  awk -F '	' -v "max=$maxcols" 'BEGIN{OFS="\t"}{for(c=NF+1; c<=max; c++)$c="-"; print}' $RES >> accounts.csv

# that's the end of the main accounts table
# now we produce two extra outputs - the D3 network diagram and the edges csv table for Gephi
# but they are both interdependent!

# list the nodes for D3 -- hang on make this happen after we've calculated the node modularity from the edges...
# awk -F '	' 'BEGIN{print "[["}{printf("%s{name:\"%s\", tweets:\"%s\", fullname:\"%s\", profile:\"%s\", followers:%s}",NR==1?"":",\n",$1,$2+0,$6,$7,$9+0)}END{print "]"}' $RES > $D3NODES

#NB This can go in various ways
#(a)Total graph of everyone who tweets, is replied to or mentioned
#(b)Graph of those who tweet
#(c)Graph of those who tweet and are responded to (the conversational graph)
#THIS IS ALL HANDLED BY THE JAVASCRIPT NOW

#to do (a) the list of active accounts is in OUT0
#cp $OUT0 $ACTIV

#to do (b), find the list of accounts whose "author" metric contains a value
#conveniently, that's column 1 of OUT1
#cut -f 1 $OUT1 > $ACTIV
#(cut -f 1 $OUT1 ; cat $OUT0 ) | sort | uniq -c | grep '^ *1 ' | sed -e 's/.* //' > $ACTIV

#to do (c) find the intersection of the list of tweeters who also appear in the mentions/inreplyto
#that's ids in both col1 of OUT1 and OUT2, ie list col 1 of both files and choose all those that appear twice
#cut -f 1 $OUT1 $OUT2 | sort | uniq -c | grep '^ *2 ' | sed -e 's/.* //' | sort > $ACTIV

#This is (a), the total graph
# create the list of edges that will be used by both D3 and Gephi
# create the full list and then filter both source, dest columns and then the RES file
  cut -f 2-999 $TMP | awk '{for(c=2;c<=NF;c++)if($1!=$c)print $1, $c}' | sort | uniq -c | awk '{printf("%s\t%s\t%s\n",$2,$3,$1)}' |
#  sort | join -t '	' - $ACTIV |
#  awk '{printf("%s\t%s\t%s\n",$2,$1,$3)}' |
#  sort | join -t '	' - $ACTIV |
#  awk '{printf("%s\t%s\t%s\n",$2,$1,$3)}' |
  sort > $EDGES

# We used to do this (calculate the modularity) on the server, now it is calculated all in the javascript
# however there is extra data that we want to join to the acounts, so this infrastructure works
# MODS should be a file that looks like 'id<tab>value'
# just change the property name in the awk script as appropriate
#  $PYTHON $MODULARITYSCRIPT $EDGES | sed -e 's/ //g' | sort > $MODS
#now we want to calculate the significant accounts, ie thge accounts whose tweets get significant attention
jq -r -c -f $BIN/significance.jq $TWEETDATA  | sort | $BIN/SUMBYKEY > $MODS
  join -t '	' -a 1 $RES $MODS > $RES2
  #these comments havent aged well
  #we used to add "-a 1" to the above to make it keep unmatched nodes in, but now we're filtering them out for b and c
  #TODO: fix this for case (a)

# list the nodes for D3 INCORPORATING the node modularity from the edges...
 #awk -F '	' 'BEGIN{print "[["}{printf("%s{id:\"%s\", name:\"%s\", tweets:\"%s\", fullname:\"%s\", profile:\"%s\", followers:%s, mod:%s}",NR==1?"":",\n",$1,$1,$2+0,$6,$7,$10+0,$14==""?-1:$14)}END{print "]"}' $RES2 > $D3NODES
  awk -F '	' 'BEGIN{print "[["}{printf("%s{id:\"%s\", name:\"%s\", tweets:\"%s\", fullname:\"%s\", profile:\"%s\", followers:%s, significance:%s}",NR==1?"":",\n",$1,$1,$2+0,$6,$7,$10+0,$14==""?-1:$14)}END{print "]"}' $RES2 > $D3NODES

# turn the edges list into the right D3 format
  awk -F '	' 'BEGIN{print ",["}{printf("%s{source:\"%s\", target:\"%s\", weight:%s}",NR==1?"":",\n",$1,$2,$3)}END{print "]]"}' $EDGES > $D3EDGES
# and join all the bits of D3 together into an HTML file
  (cat $PRE; cat $D3NODES; cat $D3EDGES; cat $POST; ) > $D3

# now turn the edges TSV into a proper CSV file for Gephi
  (echo "Source	Target	Weight"; cat $EDGES) | $BIN/tsvtocsv > $CSVEDGES
# we should probs do the same thing for the Gephi nodes...
# but Gephi can manage without and I'm tired/bored/confused

rm -f $OUT0 $OUT1 $OUT2 $TABL $TABR $D3NODES $D3EDGES
#keep the users file for the moment. this might be really big.
#turns out DOKWIC needs it. ATM let's just park it in the current (cache) directory.
#but #bigflag we need a coherent way of sharing intermediate files!
#rm -f $UJS
mv $TMP 00TMP
mv $UJS 00USERS.json
mv $MODS 00MODS
mv $RES 00RES
mv $RES2 00RES2
mv $EDGES 00EDGES
#hmmm DOKWIC only needs author details, which is all available in the TWEET file....
#...
#no it needs dates of registration?
#sort that out later
