#!/usr/bin/env python
# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#  http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express
# or implied. See the License for the specific language governing permissions
# and limitations under the License.
"""
Example usage:
    python gather-data.py @awscloud

Substitute your company's twitter handle instead of @awscloud and
configure your Twitter API credentials in config.py (see
https://dev.twitter.com/oauth/overview/application-owner-access-tokens for information on
on how to get them)

This will produce a file called line_separated_tweets_json.txt. It is used by
later scripts.
"""

import codecs
import json
import os.path
import sys
from time import sleep

import twitter
from twitter.error import TwitterError

import config

twitter_api = None
output_file_name = 'line_separated_tweets_json.txt'
# max number of tweets that this script downloads.
max_tweets = 10


def status_to_map(prefix, status):
    result = {}
    result[prefix + 'sid'] = status.id
    result[prefix + 'created_at_in_seconds'] = status.created_at_in_seconds
    result[prefix + 'favorited'] = status.favorited
    result[prefix + 'favorite_count'] = status.favorite_count
    if status.geo is not None and status.geo['type'] == 'Point':
        result[prefix + 'lat'] = status.geo['coordinates'][0]
        result[prefix + 'lon'] = status.geo['coordinates'][1]
    result[prefix + 'in_reply_to_screen_name'] = status.in_reply_to_screen_name
    result[prefix + 'in_reply_to_user_id'] = status.in_reply_to_user_id
    result[prefix + 'in_reply_to_status_id'] = status.in_reply_to_status_id
    result[prefix + 'retweet_count'] = status.retweet_count
    result[prefix + 'text'] = status.text
    return result


def user_to_map(prefix, user):
    result = {}
    result[prefix + 'uid'] = user.id
    result[prefix + 'user.name'] = user.name
    result[prefix + 'screen_name'] = user.screen_name
    result[prefix + 'location'] = user.location
    result[prefix + 'description'] = user.description
    result[prefix + 'utc_offset'] = user.utc_offset
    result[prefix + 'time_zone'] = user.time_zone
    result[prefix + 'statuses_count'] = user.statuses_count
    result[prefix + 'followers_count'] = user.followers_count
    result[prefix + 'friends_count'] = user.friends_count
    result[prefix + 'favourites_count'] = user.favourites_count
    result[prefix + 'geo_enabled'] = user.geo_enabled
    result[prefix + 'verified'] = user.verified
    return result


# Flags so that call rate remains within api specified rate-limit
sleep_before_get_search = False
sleep_before_get_status = False
sleep_before_get_user = False


def sleep_then_update_flags():
    global sleep_before_get_search, sleep_before_get_status, sleep_before_get_user
    sleep(5.05)
    sleep_before_get_search = False
    sleep_before_get_status = False
    sleep_before_get_user = False


def process_status(status, output_file_handle):
    global sleep_before_get_status
    global sleep_before_get_user
    if status.retweeted_status is not None:
        return False
    record = {}
    record.update(status_to_map('', status))
    record.update(user_to_map('', status.user))
    if record['in_reply_to_status_id'] is not None:
        if sleep_before_get_status:
            sleep_then_update_flags()
        try:
            r2status = twitter_api.GetStatus(record['in_reply_to_status_id'])
            sleep_before_get_status = True
            record.update(status_to_map('r.', r2status))
            record.update(user_to_map('r.', r2status.user))
        except TwitterError as e:
            print(e)
            print('statusId:' + str(record['in_reply_to_status_id']))
    elif record['in_reply_to_user_id'] is not None:
        if sleep_before_get_user:
            sleep_then_update_flags()
        try:
            r2user = twitter_api.GetUser(int(record['in_reply_to_user_id']))
            sleep_before_get_user = True
            record.update(user_to_map('r.', r2user))
        except TwitterError as e:
            print(e)
            print('statusId:' + str(record['in_reply_to_user_id']))
    output_file_handle.write(json.dumps(record))
    output_file_handle.write('\n')
    return True


def fetch_tweets(twitter_handle):
    with codecs.open(output_file_name, 'w', 'utf-8') as output_file_handle:
        global sleep_before_get_search
        max_id = -1
        count = 0
        search_query = '@' + twitter_handle + ' -from:' + twitter_handle
        while count < max_tweets:
            if sleep_before_get_search:
                sleep_then_update_flags()
            if max_id == -1:
                statuses = twitter_api.GetSearch(
                    term=search_query, count=100, result_type='recent')
            else:
                statuses = twitter_api.GetSearch(
                    term=search_query, count=100, result_type='recent', max_id=max_id - 1)
            sleep_before_get_search = True
            if len(statuses) == 0:
                print("No more search results found.")
                break
            for status in statuses:
                # print a '.' for each tweet that is downloaded
                sys.stdout.write(".")
                sys.stdout.flush()
                if max_id == -1:
                    max_id = status.id
                else:
                    max_id = min(max_id, status.id)
                if process_status(status, output_file_handle):
                    count = count + 1
        print("{0} tweets downloaded.".format(count))
        print("See file {0} for tweets".format(output_file_name))


def main(twitter_handle):
    global twitter_api
    twitter_api = twitter.Api(consumer_key=config.CONSUMER_KEY,
                              consumer_secret=config.CONSUMER_SECRET,
                              access_token_key=config.ACCESS_TOKEN,
                              access_token_secret=config.ACCESS_TOKEN_SECRET)
    try:
        twitter_api.VerifyCredentials()
    except TwitterError as e:
        print(e)
        print(
            "Verify contents of file: {0}. See https://dev.twitter.com/oauth/overview/application-owner-access-tokens for help.".format(credentials_file))
    if os.path.isfile(output_file_name):
        raise IOError(
            "File '{0}' already exists. Won't overwrite.".format(output_file_name))
    fetch_tweets(twitter_handle)


def parse_handle(txt):
    import re

    re1 = '(@)'   # Single '@' character
    # any sequence that contains alphanumeric characters or underscore.
    re3 = '((?:[a-z0-9_]*))'

    rg = re.compile(re1 + re3, re.IGNORECASE)
    m = rg.search(txt)
    if m:
        return m.group(2)


if __name__ == "__main__":
    try:
        twitter_handle = sys.argv[1]
        parsed_handle = parse_handle(twitter_handle)
        if not parsed_handle:
            raise "{0} is not a legal handle. Please input in format similar to example: @awscloud".format(
                twitter_handle)
    except:
        print __doc__
        raise
    main(parsed_handle)
