#!/usr/bin/env python
# Amazon Machine Learning Samples
# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use
# this file except in compliance with the License. A copy of the License is
# located at
#
#     http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or
# implied. See the License for the specific language governing permissions and
# limitations under the License.
import base64
import boto
import json
import os
import logging
import config


logger = logging.getLogger(config.APP_NAME)


class Fold(object):
    """
    This class represents a 'Fold' in K-fold Cross-validation. A fold
    understands the ordinal number in its sequence of Fold objects,
    so that it is able to draw the splitting range, and the splitting
    complement flag for DataRearrangement string. The instance of a
    fold can use Amazon ML's API to create an evaluation datasource,
    a training datasource, an ML model and an evaluation.

    """

    def __init__(self, data_spec=None, this_fold=None, kfolds=None):
        """
        Construct this instance of Fold.

        Args:
            data_spec: the named tuple object that wraps dataset related
                       parameters.
            this_fold: the integer number indicating the ordinal number
                       of this instance in its sequence of Fold objects.
            kfolds: the integer number representing the number of folds.
        """
        self.data_spec = data_spec
        self.this_fold = this_fold
        self.kfolds = kfolds
        self.fold_ordinal = self.this_fold + 1  # fold_ordinal counting from 1
        self.train_ds_id = None
        self.train_ds_rearrange = None
        self.eval_ds_id = None
        self.eval_ds_rearrange = None
        self.ml_id = None
        self.ev_id = None

    def build(self):
        """
        Builds the necessary entities on Amazon ML.
        """
        self._ml = boto.connect_machinelearning()
        self.create_datasources()
        self.create_ml_model()
        self.create_eval()

    def __str__(self):
        """
        Returns the string representing this fold object. The string
        includes the IDs of entities newly created on Amazon ML, as
        well as the DataRearrangement string for each newly created
        datasource.
        """
        return """\n\
Fold {fold_ordinal} of {kfolds}:
-Training Datasource ID: {train_ds_id}
-Training Datasource Rearrangement: {train_ds_rearrange}
-Evaluation Datasource ID: {eval_ds_id}
-Evaluation Datasource Rearrangement: {eval_ds_rearrange}
-ML Model ID: {ml_id}
-Evaluation ID: {ev_id}""".format(**self.__dict__)

    def create_datasources(self):
        """
        Creates datasource for model training and evaluation on Amazon ML.
        """
        # create training datasource for this fold
        self.train_ds_id = "ds-" + base64.b32encode(os.urandom(10)).decode(
            "ascii")
        self.train_ds_rearrange = self.build_rearrangement_str(
            is_complement=True)
        self.train_ds_name = self.build_datasource_name(
            self.data_spec.name, self.train_ds_rearrange)

        self._ml.create_data_source_from_s3(
            data_source_id=self.train_ds_id,
            data_source_name=self.train_ds_name,
            data_spec={
                "DataLocationS3": self.data_spec.data_s3_url,
                "DataSchema": self.data_spec.schema,
                "DataRearrangement": self.train_ds_rearrange
            },
            compute_statistics=True
        )
        logger.info("Created Training Datasource " + self.train_ds_id)

        # create evaluation datasource for this fold
        self.eval_ds_id = "ds-" + base64.b32encode(os.urandom(10)).decode(
            "ascii")
        self.eval_ds_rearrange = self.build_rearrangement_str(
            is_complement=False)
        self.eval_ds_name = self.build_datasource_name(
            self.data_spec.name, self.eval_ds_rearrange)
        self._ml.create_data_source_from_s3(
            data_source_id=self.eval_ds_id,
            data_source_name=self.eval_ds_name,
            data_spec={
                "DataLocationS3": self.data_spec.data_s3_url,
                "DataSchema": self.data_spec.schema,
                "DataRearrangement": self.eval_ds_rearrange
            },
            compute_statistics=True
        )
        logger.info("Created Evaluation Datasource " + self.eval_ds_id)

    def build_rearrangement_str(self, is_complement):
        """
        Returns the DataRearrangement string.

        Args:
            is_complement: the boolean flag to indicate whether the
                datasource takes the given splitting range, or the
                complement of it.
        Returns:
            a string of the DataRearrangement
        """
        # Use integer division as rearrange API only support percentage
        # in integer. Casting self.kfolds to integer for Python 2
        # compatibility.
        percent_begin = self.this_fold * (100 // int(self.kfolds))
        percent_end = (self.this_fold + 1) * (100 // int(self.kfolds))

        return json.dumps({
            "splitting": {
                "percentBegin": percent_begin,
                "percentEnd": percent_end,
                "complement": is_complement,
                "strategy": config.STRATEGY,
                "strategyParams": {
                    "randomSeed": config.RANDOM_STRATEGY_RANDOM_SEED
                }
            }
        })

    def build_datasource_name(self, name, rearrangement_str):
        """
        Builds the name of datasource to create

        Args:
            name: the user-provided name of entities on Amazon ML
            rearrangement_str: the rearrangement JSON string
        Returns:
            a string representing the name of datasource to create
        """
        rearrangement = json.loads(rearrangement_str)
        percent_begin = rearrangement["splitting"]["percentBegin"]
        percent_end = rearrangement["splitting"]["percentEnd"]
        is_complement = rearrangement["splitting"]["complement"]

        return "{name} [percentBegin={pb}, percentEnd={pe}, complement={c}]"\
            .format(name=name,
                    pb=percent_begin,
                    pe=percent_end,
                    c=is_complement)

    def create_ml_model(self):
        """
        Creates ML Model on Amazon ML using the training datasource.
        """
        self.ml_id = "ml-" + base64.b32encode(os.urandom(10)).decode("ascii")
        self.ml_name = "ML model: " + self.train_ds_name
        self._ml.create_ml_model(
            ml_model_id=self.ml_id,
            ml_model_name=self.ml_name,
            training_data_source_id=self.train_ds_id,
            ml_model_type=self.data_spec.ml_model_type,
            parameters={
                "sgd.maxPasses": self.data_spec.sgd_maxPasses,
                "sgd.maxMLModelSizeInBytes":
                self.data_spec.sgd_maxMLModelSizeInBytes,
                "sgd.l2RegularizationAmount":
                self.data_spec.sgd_l2RegularizationAmount
            },
            recipe=self.data_spec.recipe,
        )
        logger.info("Created ML Model " + self.ml_id)

    def create_eval(self):
        """
        Created Evaluation on Amazon ML using the evaluation datasource.
        """
        self.ev_id = "ev-" + base64.b32encode(os.urandom(10)).decode("ascii")
        self.ev_name = "Evaluation: " + self.ml_name
        self._ml.create_evaluation(
            evaluation_id=self.ev_id,
            evaluation_name=self.ev_name,
            ml_model_id=self.ml_id,
            evaluation_data_source_id=self.eval_ds_id
        )
        logger.info("Created Evaluation " + self.ev_id)
