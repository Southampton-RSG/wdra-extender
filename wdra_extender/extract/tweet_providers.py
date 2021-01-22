import datetime
import importlib
import json
import logging
import pathlib
import typing

from flask import current_app
import redis
from searchtweets import ResultStream, gen_request_parameters, load_credentials
from twarc import Twarc

__all__ = [
    'get_tweets_by_id',
    'get_tweets_by_search',
    'save_to_redis',
    'redis_provider',
    'twarc_provider',
]

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def import_object(name: str) -> object:
    """Get a single object from a module."""
    module_name, object_name = name.rsplit('.', 1)

    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_tweets_by_id(
        tweet_ids: typing.Iterable[int],
        tweet_providers: typing.Iterable[str]) -> typing.List[typing.Mapping]:
    """Get a list of Tweets from their IDs.

    Attempt to get tweets from each of the tweet providers in turn.
    Tweet providers should be passed as the importable name of the callable.
    e.g. 'wdra_extender.extract.tweet_providers.redis_provider'

    :param tweet_ids: Tweet IDs to lookup.
    :param tweet_providers: Iterable of names of tweet provider functions to import.
    """
    tweet_ids = set(tweet_ids)
    found_tweets = []

    for provider in map(import_object, tweet_providers):
        try:
            provider_found_ids, provider_found_tweets = provider(tweet_ids)
        except ConnectionError as exc:
            logger.error('Failed to execute Tweet provider: %s', exc)
        else:
            found_tweets.extend(provider_found_tweets)
            tweet_ids -= provider_found_ids

        if not tweet_ids:
            logger.info('Found all tweets - skipping remaining providers')
            break

    return found_tweets


def get_tweets_by_search(query, additional_search_parameters, tweet_providers) -> typing.List[typing.Mapping]:
    found_tweets = []
    for provider in map(import_object, tweet_providers):
        try:
            provider_found_ids, provider_found_tweets = provider('search_tweets', query, additional_search_parameters)
        except ConnectionError as exc:
            logger.error('Failed to execute Tweet provider: %s', exc)
        else:
            # TODO: Add an assert that if a tweet is in 'redis' we check the return fields match expected and if not
            # TODO: get the full tweet from the provider and replace the one in redis.
            # TODO: For tweets generated from redis check the tweet is still available via twitter (GDPR?)
            found_tweets.extend(provider_found_tweets)
            logger.info(f'Found {len(found_tweets)} tweets from the API')
    return found_tweets


def save_to_redis(
    tweets: typing.List[typing.Mapping],
    cache_time: datetime.timedelta = datetime.timedelta(days=10)
) -> None:
    """Save tweet JSON to Redis cache."""
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    # Pipeline executes all commands in a single request
    pipe = r.pipeline()
    for tweet in tweets:
        logger.debug(f'Saving tweet:{tweet["id"]}')
        redis_key = f'tweet_hydrated:{tweet["id"]}'
        redis_value = json.dumps(tweet)
        # There is no MSETEX command to do this in one request without a pipeline
        pipe.setex(redis_key, cache_time, redis_value)
    try:
        pipe.execute()
    except redis.exceptions.ConnectionError as exc:
        raise ConnectionError from exc


def redis_provider(
    tweet_ids: typing.Iterable[int]
) -> typing.Tuple[typing.List[int], typing.List[typing.Mapping]]:
    config = current_app.config
    r = redis.Redis(  # pylint: disable=invalid-name
        host=config['REDIS_HOST'],
        port=config['REDIS_PORT'],
        db=config['REDIS_DB'])

    found_tweet_ids = set()
    found_tweets = []

    # Attempt to get all Tweets from cache
    try:
        tweets = r.mget(map(lambda i: f'tweet_hydrated:{i}', tweet_ids))
    except redis.exceptions.ConnectionError as exc:
        raise ConnectionError from exc

    for tweet_id, tweet_string in zip(tweet_ids, tweets):
        if tweet_string is not None:
            found_tweet_ids.add(tweet_id)
            found_tweets.append(json.loads(tweet_string))

    logger.info('Found %d cached Tweets', len(found_tweet_ids))

    return found_tweet_ids, found_tweets


def twarc_provider(extract_method: str,
                   tweet_ids: typing.Iterable[int]=None,
                   search_dict: dict = {}
                   ) -> typing.Tuple[typing.Set[int], typing.List[typing.Mapping]]:
    """Get a list of Tweets from their IDs sourced from the Twitter API.

    Uses Twarc Twitter API connector - https://github.com/DocNow/twarc.
    """

    # Twitter API consumer - handles rate limits for us
    t = Twarc(  # pylint: disable=invalid-name
        consumer_key=current_app.config['TWITTER_CONSUMER_KEY'],
        consumer_secret=current_app.config['TWITTER_CONSUMER_SECRET'],
        access_token=current_app.config['TWITTER_ACCESS_TOKEN'],
        access_token_secret=current_app.config['TWITTER_ACCESS_TOKEN_SECRET'],
    )
    if extract_method == 'ID':
        logger.info('Fetching %d uncached Tweets', len(tweet_ids))
        found_tweets = list(t.hydrate(tweet_ids))
        found_tweet_ids = {tweet['id'] for tweet in found_tweets}
    elif extract_method == 'Search':
        api_query = ""
        logger.info(f'Executing api query:\n{api_query}\n')
    return found_tweet_ids, found_tweets


def searchtweets_provider(api_endpoint, request_arguments, additional_search_parameters):
    """ Download tweets via the searchtweets_v2 package for the TwitterV2 API.
    https://github.com/twitterdev/search-tweets-python/tree/v2
    """

    # Note a future bug may appear here as and when the v2 branch is merged with the main branch
    # and searchtweets will need to be reconfigured/reinstalled.

    # api_endpoint via searchtweets is currently limited to search_tweets
    # Search Tweets: developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
    # support for the additional methods and endpoints will be followed up later
    # Tweet lookup by id: developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
    # Tweets mentioning user: developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets
    # Tweets by user: developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
    # The twitter stream, user lookup and features could also be considered.
    # More info at dev portal: developer.twitter.com/en/portal/products
    # Configure the searchtweets api

    available_endpoints = {'search_tweets', }

    assert api_endpoint in available_endpoints, f'api_endpoint must be in\n\n {available_endpoints} \n\n' \
                                                f'other endpoints not yet configured'
    search_args = load_credentials(filename=current_app.config['TWITTER_CONF'],
                                   yaml_key=f"{api_endpoint}",
                                   env_overwrite=False)

    query = gen_request_parameters(request_arguments, **additional_search_parameters)
    rs = ResultStream(request_parameters=query, **search_args)
    tweets = list(rs.stream())
    logger.info(f"{tweets}")
    tweet_ids, tweets = [[row[i] for row in
                          [[tweet['id'], tweet] for tweet in tweets if 'id' in list(tweet.keys())]]
                         for i in range(2)]
    return tweet_ids, tweets
