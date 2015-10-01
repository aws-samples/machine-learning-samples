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
Utility to call Amazon Kinesis stream using payload from a file that contains line
separated json. This script is used in conjunction with
create-lambda-function.py, which expectes the Kinesis stream to provide the
input on which predictions are made. All json data being pushed to kinesis is
first converted to string to string key value pairs as that is the expected
format by Amazon Machine Learning.

Usage:
    python push-json-to-kinesis.py line_separated_json.txt kinesis_stream_name interval

line_separated_json.txt : File that contains line separated json data.
kinesis_stream_name     : Name of the stream to which the data is pushed to.
interval                : Interval in millis between two calls to kinesis stream.
"""

import boto
import codecs
import json
import sys

from time import sleep

kinesis = boto.connect_kinesis()


def build_string_to_string_dictionary(dictionary):
    output = {}
    for key, value in dictionary.items():
        output[key] = unicode(value)
    return output


def main(kinesis_stream_name, line_separated_tweets_json_filename, interval):
    with codecs.open(line_separated_tweets_json_filename, 'r', 'utf-8') as line_separated_tweets_json:
        for line in line_separated_tweets_json.readlines():
            json_payload = build_string_to_string_dictionary(json.loads(line))
            string_payload = json.dumps(json_payload)
            sleep(interval * 1.0 / 1000)  # convert to seconds
            print("Payload to kinesis: {0}".format(string_payload))
            print("Response from kinesis: {0}".format(
                str(kinesis.put_record(kinesis_stream_name, string_payload, '0'))))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Missing arguments"
        print __doc__
        sys.exit(-1)
    if len(sys.argv) > 4:
        print "Extra arguments"
        print __doc__
        sys.exit(-1)
    try:
        line_separated_tweets_json_filename = sys.argv[1]
        kinesis_stream_name = sys.argv[2]
        if len(sys.argv) == 4:
            interval = int(sys.argv[3])
        else:
            interval = 1000
        main(kinesis_stream_name, line_separated_tweets_json_filename, interval)
    except Exception as e:
        print __doc__
        raise e
