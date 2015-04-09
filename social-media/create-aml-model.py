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
Utility to create a machine learning model that performs binary classification.
Requires input dataset and corresponding scheme specified through file names in
the parameter. This utility splits the dataset into two pieces, 70% of the
dataset is used for training and 30% of the dataset is used for evaluation.
Once training and evaluation is successful, AUC is printed.

Usage:
    python create-aml-model.py aml_training_dataset.csv aml_training_dataset.schema s3-bucket-name s3-key-name
"""

import boto
import json
import random
import sys
import time

from boto.exception import S3ResponseError
from time import sleep

CONSOLE_URL_BASE = 'console.aws.amazon.com'
CONSOLE_URL_ML_MODEL = "https://{0}/machinelearning/home?#/predictor-insight/{1}?tabId=summary"
CONSOLE_URL_EVALUATION = "https://{0}/machinelearning/home?#/predictor-insight/{1}?tabId=evaluations&evaluationId={2}&viewId=summary"
CONSOLE_URL_DATA_SOURCE = "https://{0}/machinelearning/home#/insights/{1}/summary"


def pretty_print(input):
    if input == '':
        return input
    else:
        return json.dumps(json.loads(input), sort_keys=True, indent=4, separators=(',', ': '))

def check_bucket_policy(s3_key):
    with open('amlS3ReadPolicyTemplate.json') as read_policy_template_file_handle:
        target_bucket_policy = read_policy_template_file_handle.read().format(bucketName=s3_key.bucket.name,
                                                                              keyName=s3_key.name)
    print("Checking access policy on {0}".format("s3://{0}/{1}".format(s3_key.bucket.name, s3_key.name)))
    # Fetch current bucket policy
    existing_bucket_policy = ''
    try:
        existing_bucket_policy = s3_key.bucket.get_policy()
    except S3ResponseError as e:
        if 'The bucket policy does not exist' != e.message:
            # Unknown exception hence raise it to the user.
            raise e
    updated_policy_json = determine_changed_bucket_policy(existing_bucket_policy, target_bucket_policy)
    if updated_policy_json is not None:
        # log existing bucket policy
        print("Current bucket policy:\n{0}\n".format(pretty_print(existing_bucket_policy)))
        # log summary of the required resource access
        required_access = json.dumps(json.loads(target_bucket_policy)['Statement'][0])
        print("Required resource access:\n{0}\n".format(pretty_print(required_access)))
        # log a suggested bucket policy that add the required access to the existing policy
        print("Suggested bucket policy:\n{0}\n".format(pretty_print(updated_policy_json)))
        help_url_1 = "http://docs.aws.amazon.com/AmazonS3/latest/UG/EditingBucketPermissions.html"
        help_url_2 = "http://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html"
        print("See {0} and {1} for details.".format(help_url_1, help_url_2))
        sys.exit("Please retry after setting appropriate policy on bucket {0}.".format(s3_key.bucket.name))

def determine_changed_bucket_policy(existing_bucket_policy, target_bucket_policy):
    if existing_bucket_policy == '':
        return target_bucket_policy
    json_policy = json.loads(existing_bucket_policy)
    target_statement = json.loads(target_bucket_policy)['Statement'][0]
    target_resource_arn = target_statement['Resource'][0]
    for statement in json_policy['Statement']:
        if (
            statement.has_key('Principal') and
            statement['Principal'].has_key('Service') and
            statement['Principal']['Service'] == 'machinelearning.amazonaws.com' and
            statement['Effect'] == "Allow" and
            "s3:GetObject" in statement['Action']
        ):
            if target_resource_arn == statement['Resource'] or target_resource_arn in statement['Resource']:
                # no change required
                return None
            elif isinstance(statement['Resource'], str) or isinstance(statement['Resource'], unicode):
                # convert the resource value to a list
                statement['Resource'] = [statement['Resource']]
            # If we reach here then we know that resource is a list that doesn't contain target_resource_arn
            statement['Resource'].append(target_resource_arn)
            return json.dumps(json_policy)
    # If we reach here then we know that simplest change is to append the desired statement into the policy.
    json_policy['Statement'].append(target_statement)
    return json.dumps(json_policy)


def create_data_source(s3_uri, dataset_schema, ds_type, percent_begin, percent_end, compute_statistics):
    global time_stamp
    ds_id = "ds-tweets-{0}-{1}".format(ds_type, time_stamp)
    data_spec = {}
    data_spec['DataLocationS3'] = s3_uri
    data_spec['DataSchema'] = dataset_schema
    data_spec['DataRearrangement'] = '{{"randomSeed":"0","splitting":{{"percentBegin":{0},"percentEnd":{1}}}}}'.format(
        percent_begin, percent_end)
    ml.create_data_source_from_s3(
        ds_id,
        data_spec,
        data_source_name="{0}_DataSplitting [percentBegin={1}, percentEnd={2}]".format(aml_training_dataset,
                                                                                       percent_begin, percent_end),
        compute_statistics=compute_statistics)
    print("Creating {0} datasource. See:".format(ds_type))
    print(CONSOLE_URL_DATA_SOURCE.format(CONSOLE_URL_BASE, ds_id))
    return ds_id


def poll_until_ready(evaluation_id):
    delay = 2
    while True:
        evaluation = ml.get_evaluation(evaluation_id)
        if evaluation['Status'] in ['COMPLETED', 'FAILED', 'INVALID']:
            return
        sys.stdout.write(".")
        sys.stdout.flush()
        delay *= random.uniform(1.1, 2.0)
        sleep(delay)


def main(s3_uri, dataset_schema):
    global time_stamp
    training_ds_id = create_data_source(s3_uri, dataset_schema, "training", 0, 70, True)
    evaluation_ds_id = create_data_source(s3_uri, dataset_schema, "evaluation", 70, 100, False)
    ml_model_id = 'ml-tweets-' + time_stamp
    ml.create_ml_model(ml_model_id, "BINARY", training_ds_id)
    print("Creating ml model with id {0}. See:".format(ml_model_id))
    print(CONSOLE_URL_ML_MODEL.format(CONSOLE_URL_BASE, ml_model_id))
    evaluation_id = 'ev-tweets-' + time_stamp
    ml.create_evaluation(evaluation_id, ml_model_id, evaluation_ds_id)
    print("Creating evaluation with id {0}. See:".format(evaluation_id))
    print(CONSOLE_URL_EVALUATION.format(CONSOLE_URL_BASE, ml_model_id, evaluation_id))
    print("Waiting for evaluation to complete.")
    poll_until_ready(evaluation_id)
    print("done")
    evaluation = ml.get_evaluation(evaluation_id)
    print("Performance metric on the evaluation dataset: Binary AUC: " + evaluation['PerformanceMetrics']['Properties'][
        'BinaryAUC'])


time_stamp = time.strftime('%Y-%m-%d-%H-%M-%S')

ml = boto.connect_machinelearning()
s3 = boto.connect_s3()

aml_training_dataset = None

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print __doc__
        sys.exit(-1)
    try:
        aml_training_dataset = sys.argv[1]
        s3_bucket = s3.get_bucket(sys.argv[3])
        s3_key = s3_bucket.new_key(sys.argv[4])
        s3_uri = "s3://{0}/{1}".format(sys.argv[3], sys.argv[4])
        print("Uploading {0} to {1}".format(sys.argv[1], s3_uri))
        if s3_key.exists():
            sys.stderr.write("{0} already exists. Skipping upload of {1}.\n".format(s3_uri, sys.argv[1]))
        else:
            s3_key.set_contents_from_filename(sys.argv[1])
        with open(sys.argv[2]) as schema_file_handle:
            dataset_schema = schema_file_handle.read()
        check_bucket_policy(s3_key)
        main(s3_uri, dataset_schema)
    except Exception as e:
        print __doc__
        raise e
