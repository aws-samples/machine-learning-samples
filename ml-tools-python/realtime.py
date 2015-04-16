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
"""Simple command-line realtime prediction utility

Usage:
    python realtime.py ml_model_id attribute1=value1 attribute2=value2 ...
or:
    python realtime.py ml_model_id --deleteEndpoint

Multi-word text attributes can be specified like:
    python realtime.py ml-12345678901 "textVar=Multiple words grouped together" numericVar=123
"""

import boto
import json
import sys
import time


def parse_args_to_dict(argv):
    """Returns a record as a python dict by parsing key=value pairs
    from the command line"""
    record = {}
    for kv in argv:
        try:
            (k, v) = kv.split('=')
            record[k] = v
        except:
            print('Unable to parse "%s" as attribute=value' % kv)
            raise RuntimeError()
    if not record:
        print("No attributes specified")
        raise RuntimeError()
    return record


def realtime_predict(ml_model_id, record):
    """Takes a string ml_model_id, and a dict record, and makes a realtime
    prediction call, if the ML Model has a realtime endpoint.
    If the ML Model doesn't have a realtime endpoint, it creates one instead
    of calling predict()
    """
    ml = boto.connect_machinelearning()
    model = ml.get_ml_model(ml_model_id)
    endpoint = model.get('EndpointInfo', {}).get('EndpointUrl', '')
    #endpoint = endpoint.replace("https://", "")  # This shouldn't be needed
    if endpoint:
        print('ml.predict("%s", %s, "%s") # returns...' % (ml_model_id,
                                                           json.dumps(record, indent=2), endpoint))
        start = time.time()
        prediction = ml.predict(ml_model_id, record, predict_endpoint=endpoint)
        latency_ms = (time.time() - start)*1000
        print(json.dumps(prediction, indent=2))
        print("Latency: %.2fms" % latency_ms)
    else:
        print(
            '# Missing realtime endpoint\nml.create_realtime_endpoint("%s")' % ml_model_id)
        result = ml.create_realtime_endpoint(ml_model_id)
        print(json.dumps(result, indent=2))
        print("""# Predictions will fail until the endpoint has been fully created.
# Note that you will be charged a reservation fee until this endpoint is deleted.
# Delete with:
    python realtime.py %s --deleteEndpoint""" % ml_model_id)


def delete_realtime_endpoint(ml_model_id):
    ml = boto.connect_machinelearning()
    print('# Deleting realtime endpoint\nml.delete_realtime_endpoint("%s")' %
          ml_model_id)
    result = ml.delete_realtime_endpoint(ml_model_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        ml_model_id = sys.argv[1]
        delete_endpoint = (sys.argv[2] == "--deleteEndpoint")
        if not delete_endpoint:
            record = parse_args_to_dict(sys.argv[2:])
    except:
        print(__doc__)
        sys.exit(-1)
    if delete_endpoint:
        delete_realtime_endpoint(ml_model_id)
    else:
        realtime_predict(ml_model_id, record)
