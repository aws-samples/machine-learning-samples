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
    python build-mturk-csv.py

This consumes the file line_separated_tweets_json.txt which is produced by
gather-data.py and produces mturk_unlabeled_dataset.csv which can be used to
generate labels using Amazon Mechanical Turk.
"""

import codecs
import json
import unicodecsv
import HTMLParser
import re
import os.path

re_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)

input_file_name = 'line_separated_tweets_json.txt'
output_file_name = 'mturk_unlabeled_dataset.csv'

if not os.path.isfile(input_file_name):
    raise IOError(
        "Input file '{0}' missing. Use gather-data.py.".format(input_file_name))

if os.path.isfile(output_file_name):
    raise IOError(
        "File '{0}' already exists. Won't overwrite.".format(output_file_name))

with codecs.open(input_file_name, 'r', 'utf-8') as line_separated_tweets_json:
    with open(output_file_name, 'wb') as mturk_unlabeled_dataset:
        html_parser = HTMLParser.HTMLParser()
        csv_writer = unicodecsv.writer(
            mturk_unlabeled_dataset, encoding='utf-8')
        csv_writer.writerow(['tweet', 'id'])
        for line in line_separated_tweets_json.readlines():
            tweet_json = json.loads(line)
            tweet_text = html_parser.unescape(tweet_json['text']).replace(
                '\n', ' ').replace('\r\n', ' ')
            # Convert tweet to utf-8 that only uses 3 bytes for mechanical turk
            # compatibility.
            mech_turk_compatible_text = re_pattern.sub(u'\uFFFD', tweet_text)
            csv_writer.writerow([mech_turk_compatible_text, tweet_json['sid']])
        print("See file {0} for Mechanical Turk dataset".format(output_file_name))
