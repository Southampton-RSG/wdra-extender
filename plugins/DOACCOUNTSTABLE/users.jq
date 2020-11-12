[
        .screen_name,
        .name,
        .description,
        .location,
	.entities.url.urls[0].expanded_url,
        .followers_count,
        .friends_count,
        .statuses_count,
        (.created_at | .[8:11] + .[4:8] + .[26:30] + .[10:19])
] | @tsv
