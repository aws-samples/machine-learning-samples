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
Waits for an entity to reach a terminal state.

Type of entity can be inferred from the initial two letters of the id,
or specified manually with the convention:

  ds = data source
  ml = ML Model
  ev = evaluation
  bp = batch prediction

Useage:
    python wait_for_entity.py entity_id [entity_type]
"""
import boto
import datetime
import json
import random
import sys
import time


def poll_until_completed(entity_id, entity_type_str):
    ml = boto.connect_machinelearning()
    polling_function = {
        'ds': ml.get_data_source,
        'ml': ml.get_ml_model,
        'ev': ml.get_evaluation,
        'bp': ml.get_batch_prediction,
    }[entity_type_str]
    delay = 2
    while True:
        results = polling_function(entity_id)
        status = results['Status']
        message = results.get('Message', '')
        now = str(datetime.datetime.now().time())
        print("Object %s is %s (%s) at %s" % (entity_id, status, message, now))
        if status in ['COMPLETED', 'FAILED', 'INVALID']:
            break

        # exponential backoff with jitter
        delay *= random.uniform(1.1, 2.0)
        time.sleep(delay)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    try:
        entity_id = sys.argv[1]
        if len(sys.argv) > 2:
            entity_type_str = sys.argv[2]
        else:
            entity_type_str = entity_id[:2]
        if entity_type_str not in ['ds', 'ml', 'ev', 'bp']:
            raise RuntimeError("Unknown entity type")
    except:
        print(__doc__)
        sys.exit(-1)
    poll_until_completed(entity_id, entity_type_str)
