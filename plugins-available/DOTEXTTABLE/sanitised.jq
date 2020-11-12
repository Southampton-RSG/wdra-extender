.[] |
.user.screen_name as $by |
has("retweeted_status") as $rt |
if $rt then .retweeted_status else . end |
	(.full_text|gsub("[@#]\\w+";"")|gsub("https?://\\S+";""))
