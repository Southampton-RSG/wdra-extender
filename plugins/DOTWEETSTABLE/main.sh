#!/bin/sh
IN=$1

# It bothers me that this is a separate CONSTANT string that has to be updated separtately from the JQ file
echo 'ID,Replies,Retweets,Likes,Author,Author Name,Author Profile,Author Location,Author Followers,Author Tweets,In Reply To,Retweeted By,Retweeted At,Mentions,Hashtags,Embedded URL,Embedded Site Text,URL,Timestamp,Sanitised Text' > tweets.csv

jq -r -f $BIN/tweets_to_csv.jq $IN >> tweets.csv

echo "Saved to $(pwd)/tweets.csv"
