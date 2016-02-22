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
Demonstrates how to use an ML Model, by setting the score threshold, 
and kicks off a batch prediction job, which uses the ML Model to 
generate predictions on new data.  This script needs the id of the 
ML Model to use.  It also requires the score threshold.

Useage:
    python use_model.py ml_model_id score_threshold s3_output_url

For example:
    python use_model.py ml-12345678901 0.77 s3://your-bucket/prefix
"""
import base64
import boto3
import datetime
import os
import random
import sys
import time
import urlparse

# The URL of the sample data in S3
UNSCORED_DATA_S3_URL = "s3://aml-sample-data/banking-batch.csv"


def use_model(model_id, threshold, schema_fn, output_s3, data_s3url):
    """Creates all the objects needed to build an ML Model & evaluate its quality.
    """
    ml = boto3.client('machinelearning') 

    poll_until_completed(ml, model_id)  # Can't use it until it's COMPLETED
    ml.update_ml_model(MLModelId=model_id, ScoreThreshold=threshold)
    print("Set score threshold for %s to %.2f" % (model_id, threshold))

    bp_id = 'bp-' + base64.b32encode(os.urandom(10))
    ds_id = create_data_source_for_scoring(ml, data_s3url, schema_fn)
    ml.create_batch_prediction(
        BatchPredictionId=bp_id,
        BatchPredictionName="Batch Prediction for marketing sample",
        MLModelId=model_id,
        BatchPredictionDataSourceId=ds_id,
        OutputUri=output_s3
    )
    print("Created Batch Prediction %s" % bp_id)


def poll_until_completed(ml, model_id):
    delay = 2
    while True:
        model = ml.get_ml_model(MLModelId=model_id)
        status = model['Status']
        message = model.get('Message', '')
        now = str(datetime.datetime.now().time())
        print("Model %s is %s (%s) at %s" % (model_id, status, message, now))
        if status in ['COMPLETED', 'FAILED', 'INVALID']:
            break

        # exponential backoff with jitter
        delay *= random.uniform(1.1, 2.0)
        time.sleep(delay)


def create_data_source_for_scoring(ml, data_s3url, schema_fn):
    ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    ml.create_data_source_from_s3(
        DataSourceId=ds_id,
        DataSourceName="DS for Batch Prediction %s" % data_s3url,
        DataSpec={
            "DataLocationS3": data_s3url,
            "DataSchema": open(schema_fn).read(),
        },
        ComputeStatistics=False
    )
    print("Created Datasource %s for batch prediction" % ds_id)
    return ds_id


if __name__ == "__main__":
    try:
        model_id = sys.argv[1]
        threshold = float(sys.argv[2])
        s3_output_url = sys.argv[3]
        parsed_url = urlparse.urlparse(s3_output_url)
        if parsed_url.scheme != 's3':
            raise RuntimeError("s3_output_url must be an s3:// url")
    except IndexError:
        print(__doc__)
        sys.exit(-1)
    except:
        print(__doc__)
        raise
    use_model(model_id, threshold, "banking-batch.csv.schema",
              s3_output_url, UNSCORED_DATA_S3_URL)
