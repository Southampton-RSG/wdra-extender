.[] |
.user.screen_name as $by |
.created_at as $when |
has("retweeted_status") as $rt |
if $rt then .retweeted_status else . end |
[
        "ID:"+.id_str,
        "-",
        .retweet_count,
        .favorite_count,
        .user.screen_name,
        .user.name,
        .user.description,
        .user.location,
        .user.followers_count,
        .user.statuses_count,
        .in_reply_to_screen_name,
        if $rt then $by else "" end,
        if $rt then $when else "" end,
        (.entities.user_mentions | map(.screen_name) | join(" ")),
        (.entities.hashtags | map(.text) | join(" ")),
        (.entities.urls | map(.expanded_url) | join(" ")),
        (.entities.urls | map(.expanded_url) | map(split("/") |.[2]) | join(" ")),
        .full_text, ## was  .retweeted_status.full_text//.full_text,
        ("https://twitter.com/"+.user.screen_name+"/status/"+.id_str),
        (.created_at | .[8:11] + .[4:8] + .[26:30] + .[10:19]),
	(.full_text|gsub("[@#]\\w+";"")|gsub("https?://\\S+";""))
] | @csv
