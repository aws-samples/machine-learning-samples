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
import json
import os
from time import sleep
from zipfile import ZipFile

import boto
from boto.kinesis.exceptions import ResourceInUseException

import config

# To enable logging:
# boto.set_stream_logger('boto')

# Initialize the AWS clients.
sns = boto.connect_sns()
kinesis = boto.connect_kinesis()
aws_lambda = boto.connect_awslambda()
ml = boto.connect_machinelearning()

lambda_execution_policy = open('lambdaExecutionPolicyTemplate.json').read().format(**config.AWS)

aws_account_id = config.AWS["awsAccountId"]
region = config.AWS["region"]
kinesis_stream = config.AWS["kinesisStream"]
sns_topic = config.AWS["snsTopic"]

lambda_function_name = config.AWS["lambdaFunctionName"]
lambda_execution_role = config.AWS["lambdaExecutionRole"]
lambda_trust_policy = '{"Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'


def role_exists(iam, role_name):
    try:
        iam.get_role(role_name)
    except:
        return False
    return True


def create_role(policy_name, assume_role_policy_document, policy_str):
    iam = boto.connect_iam()
    if role_exists(iam, policy_name):
        print('Role "{0}" already exists. Assuming correct values.'.format(policy_name))
    else:
        print('Creating policy: ' + policy_name)
        iam.create_role(policy_name, assume_role_policy_document=assume_role_policy_document)
        iam.put_role_policy(policy_name, 'inlinepolicy', policy_str)


def create_stream(stream):
    print('Creating Amazon Kinesis Stream: ' + stream)
    try:
        kinesis.create_stream(kinesis_stream, 1)
    except ResourceInUseException, e:
        print(e.message + ' Continuing.')


def main():
    # Create execution role
    create_role(lambda_execution_role, lambda_trust_policy, lambda_execution_policy)
    # Create Amazon Kinesis Stream
    create_stream(kinesis_stream)
    # Create Amazon SNS Topic
    print('Creating Amazon SNS topic: ' + sns_topic)
    sns.create_topic(sns_topic)
    # Create and upload AWS Lambda function
    create_lambda_function(lambda_function_name)
    # Create realtime endpoint for the ml model
    ml.create_realtime_endpoint(config.AWS['mlModelId'])
    # Wait for kinesis
    pause_until_kinesis_active()
    # Wait for 5 seconds
    sleep(5)
    # Connect Kinesis with Lambda
    add_kinesis_as_source_to_lambda()
    print('Kinesis stream is active now. You can start calling it.')

def create_lambda_function_zip():
    with open('index.js.template') as lambda_function_template:
        lf_string = lambda_function_template.read().format(**config.AWS)
        with open('index.js', 'w') as lambda_function_file:
            lambda_function_file.write(lf_string)

    zip_file_name = 'lambda.zip'

    with ZipFile(zip_file_name, 'w') as lambda_zip:
        lambda_zip.write('index.js')
        for root, dirs, files in os.walk('node_modules'):
            for file in files:
                lambda_zip.write(os.path.join(root, file))

    return zip_file_name

def upload_lambda_function(zip_file_name):
    with open(zip_file_name) as zip_blob:
        lambda_execution_role_arn = 'arn:aws:iam::' + \
            aws_account_id + ':role/' + lambda_execution_role
        aws_lambda.upload_function(
            lambda_function_name,
            zip_blob.read(),
            "nodejs",
            lambda_execution_role_arn,
            "index.handler",
            "event",
            description=None,
            timeout=60,
            memory_size=128)

def create_lambda_function(lambda_function_name):
    # Create lambda function
    print('Creating Lambda Function: ' + lambda_function_name)
    zip_file_name = create_lambda_function_zip()
    upload_lambda_function(zip_file_name)


def pause_until_kinesis_active():
    # Wait for Kinesis stream to be active
    while kinesis.describe_stream(kinesis_stream)['StreamDescription']['StreamStatus'] != 'ACTIVE':
        print('Kinesis Stream [' + kinesis_stream + '] not active yet.')
        sleep(5)


def add_kinesis_as_source_to_lambda():
    # Add Kinesis as event source to the lambda function
    print('Adding Kinesis as event source for Lambda function.')
    response_add_event_source = aws_lambda.add_event_source(
        event_source='arn:aws:kinesis:' + region + ':' + aws_account_id
                                        + ':stream/' + kinesis_stream,
        function_name=lambda_function_name,
        role='arn:aws:iam::' + aws_account_id + ':role/' + lambda_execution_role
    )
    event_source_id = response_add_event_source['UUID']

    while response_add_event_source['IsActive'] != 'true':
        print('Waiting for the event source to become Active.')
        sleep(5)
        response_add_event_source = aws_lambda.get_event_source(event_source_id)

main()
