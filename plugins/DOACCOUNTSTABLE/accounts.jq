.[] |
has("retweeted_status") as $rt |
if $rt then .retweeted_status else . end |
[
        .retweet_count + 1, #0 retweets means one (nonretweeted) appearance
        .user.screen_name,
        ([.in_reply_to_screen_name, (.entities.user_mentions | map(.screen_name))] | flatten | unique)
] | flatten | @tsv
