.[] |
.user.screen_name as $by |
.created_at as $when |
has("retweeted_status") as $rt |
if $rt then .retweeted_status else . end |
[
        .user.screen_name,
        .retweet_count + .favorite_count
] | @tsv
