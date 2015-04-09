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
Sample usage:
    python build-aml-training-dataset.py
"""
import codecs
import json
import os
import unicodecsv
import HTMLParser

from unicodecsv import DictReader

mturk_labeled_filename = 'mturk_labeled_dataset.csv'
line_separated_tweets_json_file_name = 'line_separated_tweets_json.txt'
aml_training_dataset_filename = 'aml_training_dataset.csv'

if not os.path.isfile(mturk_labeled_filename):
    raise IOError(
        "Input file '{0}' missing. See README.md for directions on how to use MTurk for building labeled dataset.".format(
            mturk_labeled_filename))

if not os.path.isfile(line_separated_tweets_json_file_name):
    raise IOError(
        "Input file '{0}' missing. Use gather-data.py to generate it.".format(line_separated_tweets_json_file_name))

if os.path.isfile(aml_training_dataset_filename):
    raise IOError("File '{0}' already exists. Won't overwrite.".format(
        aml_training_dataset_filename))


def read_header():
    with open(mturk_labeled_filename, 'rb') as mturk_labeled_file_handle:
        mturk_labeled_data_reader = unicodecsv.reader(
            mturk_labeled_file_handle, encoding='utf-8')
        return mturk_labeled_data_reader.next()


header = read_header()

# This number decides how many turkers mark a tweet as one or more of
# Request|Question|Problem Report|Angry before we label that tweet as
# 'requires customer service attention' in the training dataset.
threshold_for_respond_to_tweet = 2

aml_training_data_header = [
    "created_at_in_seconds",
    "description",
    "favorite_count",
    "favorited",
    "favourites_count",
    "followers_count",
    "friends_count",
    "geo_enabled",
    "in_reply_to_screen_name",
    "in_reply_to_status_id",
    "in_reply_to_user_id",
    "location",
    "r.created_at_in_seconds",
    "r.description",
    "r.favorite_count",
    "r.favorited",
    "r.favourites_count",
    "r.followers_count",
    "r.friends_count",
    "r.geo_enabled",
    "r.in_reply_to_screen_name",
    "r.in_reply_to_status_id",
    "r.in_reply_to_user_id",
    "r.location",
    "r.retweet_count",
    "r.screen_name",
    "r.sid",
    "r.statuses_count",
    "r.text",
    "r.time_zone",
    "r.uid",
    "r.user.name",
    "r.utc_offset",
    "r.verified",
    "retweet_count",
    "screen_name",
    "sid",
    "statuses_count",
    "text",
    "time_zone",
    "uid",
    "user.name",
    "utc_offset",
    "verified",
    "trainingLabel",
]

html_parser = HTMLParser.HTMLParser()

with open(mturk_labeled_filename, 'rb') as mturk_labeled_file_handle:
    mturk_labeled_data_reader = DictReader(
        mturk_labeled_file_handle, fieldnames=header, encoding='utf-8')
    # skip first
    mturk_labeled_data_reader.next()
    # Dictionary to count flags
    flag_count_on_tweets = {}
    for hit in mturk_labeled_data_reader:
        if hit["AssignmentStatus"] != "Approved":
            continue
        tweet_id = hit['Input.id']
        answer = hit['Answer.Q3Answer']
        if tweet_id not in flag_count_on_tweets:
            flag_count_on_tweets[tweet_id] = 0
        if answer != 'N/A':
            flag_count_on_tweets[tweet_id] += 1
    counter = {0: 0, 1: 0, 2: 0, 3: 0}
    with codecs.open(line_separated_tweets_json_file_name, 'r', 'utf8') as line_separated_tweets_handle:
        with open(aml_training_dataset_filename, 'wb') as aml_training_dataset_handle:
            csv_writer = unicodecsv.writer(
                aml_training_dataset_handle, encoding='utf-8')
            csv_writer.writerow(aml_training_data_header)
            for line in line_separated_tweets_handle.readlines():
                tweet_data = json.loads(line)
                tweet_id = unicode(tweet_data['sid'])
                if tweet_id in flag_count_on_tweets:
                    num_votes = flag_count_on_tweets[tweet_id]
                    counter[num_votes] += 1
                    training_label = None
                    if num_votes >= threshold_for_respond_to_tweet:
                        training_label = '1'
                    else:
                        training_label = '0'
                    tweet_data['trainingLabel'] = training_label
                    row_data = []
                    for key in aml_training_data_header:
                        if key in tweet_data:
                            if isinstance(tweet_data[key], str) or isinstance(tweet_data[key], unicode):
                                row_data.append(html_parser.unescape(tweet_data[key]).replace(
                                    '\n', ' ').replace('\r\n', ' ').replace('\r', ' '))
                            else:
                                row_data.append(tweet_data[key])
                        else:
                            row_data.append(None)
                    csv_writer.writerow(row_data)
    print("Statistics:")
    for i in range(4):
        print(
            "{1} tweets had {0}/3 turkers mark it as one or more of Request|Question|Problem Report|Angry".format(i, counter[i]))
    print("See file {0} for machine learning training dataset".format(
        aml_training_dataset_filename))
