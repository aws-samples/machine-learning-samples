import base64
import boto
import json
import logging
import sys

from twitter import OAuth, TwitterStream

import config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def prepare(tweet):
    '''Prepares the tweet as a flat JSON object that matches the schema
    expected by the ML model it will be sent to.'''
    logger.info('Preparing tweet %s', tweet)
    ans = {
        'description': tweet['user']['description'],
        'favourites_count': str(tweet['user']['favourites_count']),
        'followers_count': str(tweet['user']['followers_count']),
        'friends_count': str(tweet['user']['friends_count']),
        'geo_enabled': str(tweet['user']['geo_enabled']),
        'screen_name': tweet['user']['screen_name'],
        'sid': tweet['id_str'],
        'statuses_count': str(tweet['user']['statuses_count']),
        'text': tweet['text'],
        'uid': tweet['user']['id_str'],
        'user.name': tweet['user']['name'],
        'verified': str(tweet['user']['verified'])
    }
    ans = json.dumps(ans)
    logger.debug('Prepared JSON object %s', ans)
    return ans


def scan():
    '''Scans for public tweets using Tweeter's public stream API with a
    basic filter. See
    https://dev.twitter.com/streaming/reference/post/statuses/filter
    '''
    kinesis = boto.connect_kinesis()
    auth = OAuth(consumer_key=config.CONSUMER_KEY, consumer_secret=config.CONSUMER_SECRET,
                 token=config.ACCESS_TOKEN, token_secret=config.ACCESS_TOKEN_SECRET)
    stream = TwitterStream(auth=auth)
    tweets = stream.statuses.filter(track=config.TWITTER_FILTER)
    for tweet in tweets:
        payload = prepare(tweet)
        kinesis.put_record(config.KINESIS_STREAM, payload, config.KINESIS_PARTITION)
        logger.debug('Sent to Amazon Kinesis.')

if __name__ == '__main__':
    scan()
