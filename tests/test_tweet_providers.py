import unittest

from wdra_extender.extract import tweet_providers
from .mocks.tweet_provider import TEST_TWEET_IDS, TEST_TWEETS


class TweetProvidersTest(unittest.TestCase):
    def test_get_tweets_from_mock(self):
        tweets = tweet_providers.get_tweets_by_id(
            TEST_TWEET_IDS, ['tests.mocks.tweet_provider.tweet_provider'])

        self.assertEqual(TEST_TWEETS, tweets)
