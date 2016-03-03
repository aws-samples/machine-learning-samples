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
Demonstrates all the steps needed to build an ML Model
for the targeted marketing example in the Getting Started Guide
for Amazon Machine Learning

Usage:
    python build_model.py ["Optional name for created objects"]
"""
import base64
import boto3
import json
import os
import sys


TRAINING_DATA_S3_URL = "s3://aml-sample-data/banking.csv"


def build_model(data_s3_url, schema_fn, recipe_fn, name, train_percent=70):
    """Creates all the objects needed to build an ML Model & evaluate its quality.
    """
    ml = boto3.client('machinelearning')
    (train_ds_id, test_ds_id) = create_data_sources(ml, data_s3_url, schema_fn,
                                                    train_percent, name)
    ml_model_id = create_model(ml, train_ds_id, recipe_fn, name)
    eval_id = create_evaluation(ml, ml_model_id, test_ds_id, name)

    return ml_model_id


def create_data_sources(ml, data_s3_url, schema_fn, train_percent, name):
    """Create two data sources.  One with (train_percent)% of the data,
    which will be used for training.  The other one with the remainder of the data,
    which is commonly called the "test set" and will be used to evaluate the quality
    of the ML Model.
    """
    train_ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    spec = {
        "DataLocationS3": data_s3_url,
        "DataRearrangement": json.dumps({
            "splitting": {
                "percentBegin": 0,
                "percentEnd": train_percent
            }
        }),
        "DataSchema": open(schema_fn).read(),
    }
    ml.create_data_source_from_s3(
        DataSourceId=train_ds_id,
        DataSpec=spec,
        DataSourceName=name + " - training split",
        ComputeStatistics=True
    )
    print("Created training data set %s" % train_ds_id)

    test_ds_id = 'ds-' + base64.b32encode(os.urandom(10))
    spec['DataRearrangement'] = json.dumps({
        "splitting": {
            "percentBegin": train_percent,
            "percentEnd": 100
        }
    })
    ml.create_data_source_from_s3(
        DataSourceId=test_ds_id,
        DataSpec=spec,
        DataSourceName=name + " - testing split",
        ComputeStatistics=True
    )
    print("Created test data set %s" % test_ds_id)
    return (train_ds_id, test_ds_id)


def create_model(ml, train_ds_id, recipe_fn, name):
    """Creates an ML Model object, which begins the training process.
The quality of the model that the training algorithm produces depends
primarily on the data, but also on the hyper-parameters specified
in the parameters map, and the feature-processing recipe.
    """
    model_id = 'ml-' + base64.b32encode(os.urandom(10))
    ml.create_ml_model(
        MLModelId=model_id,
        MLModelName=name + " model",
        MLModelType="BINARY",  # we're predicting True/False values
        Parameters={
            # Refer to the "Machine Learning Concepts" documentation
            # for guidelines on tuning your model
            "sgd.maxPasses": "100",
            "sgd.maxMLModelSizeInBytes": "104857600",  # 100 MiB
            "sgd.l2RegularizationAmount": "1e-4",
        },
        Recipe=open(recipe_fn).read(),
        TrainingDataSourceId=train_ds_id
    )
    print("Created ML Model %s" % model_id)
    return model_id


def create_evaluation(ml, model_id, test_ds_id, name):
    eval_id = 'ev-' + base64.b32encode(os.urandom(10))
    ml.create_evaluation(
        EvaluationId=eval_id,
        EvaluationName=name + " evaluation",
        MLModelId=model_id,
        EvaluationDataSourceId=test_ds_id
    )
    print("Created Evaluation %s" % eval_id)
    return eval_id


if __name__ == "__main__":
    try:
        data_s3_url = TRAINING_DATA_S3_URL
        schema_fn = "banking.csv.schema"
        recipe_fn = "recipe.json"
        if len(sys.argv) > 2:
            name = sys.argv[1]
        else:
            name = "Marketing sample"
    except:
        raise
    model_id = build_model(data_s3_url, schema_fn, recipe_fn, name=name)
    print("""\nFor the next step in the demo, run:
    python use_model.py %s 0.77 s3://your-bucket/ml-output/""" % model_id)
