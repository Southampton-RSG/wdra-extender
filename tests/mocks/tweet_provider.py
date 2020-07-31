"""Mocks for testing requiring a tweet provider."""

import typing

TEST_TWEET_IDS = {1, 2, 3, 4, 5}

TEST_TWEETS = [
    {'id': 1, 'content': 'Hello World 1'},
    {'id': 2, 'content': 'Hello World 2'},
    {'id': 3, 'content': 'Hello World 3'},
    {'id': 4, 'content': 'Hello World 4'},
    {'id': 5, 'content': 'Hello World 5'},
] # yapf: disable


def tweet_provider(
    tweet_ids: typing.Iterable[int]
) -> typing.Tuple[typing.List[int], typing.List[typing.Mapping]]:
    """Mock tweet provider which just returns a static response."""
    return (TEST_TWEET_IDS, TEST_TWEETS)
