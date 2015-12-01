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
"""
Demonstrate how to create tasks on Amazon ML to train and evaluate a model for
K-fold cross-validation. The main function of this module requires the number
of folds(kfolds).

usage: build_folds.py [--name][--debug] kfolds

example:
    python build_folds.py --name 4-fold-cv-demo 4

"""
import sys
import logging
import argparse
import config
from fold import Fold
from collections import namedtuple


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(config.APP_NAME)


def build_folds(data_spec=None, kfolds=None):
    """
    Create Datasources, ML Model and Evaluation for each fold. Returns
        a list of newly created evaluation IDs for all folds.

    Args:
        data_spec: the named tuple object that wraps dataset related
            parameters.
        kfolds: the integer number representing the number of folds.
    Returns:
        a list of newly created evaluation IDs.
    """
    folds = [Fold(data_spec=data_spec, this_fold=i,
                  kfolds=kfolds) for i in range(kfolds)]
    for f in folds:
        f.build()  # each fold creates entities
        logger.info(f)  # prints details of folds
    return [f.ev_id for f in folds]  # return list of eval IDs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="%(prog)s [--name][--debug] kfolds",
        description="Demo code to create entities on Amazon ML for \
            K-fold cross-validation.")
    parser.add_argument("kfolds",
                        type=int,
                        choices=range(2, 11),  # 2 to 10 is valid input
                        help="the number of folds for cross-validation")
    parser.add_argument("-n", "--name",
                        default="CV sample",
                        help="the name of entities to create on Amazon ML"
                             "[default: '%(default)s']")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="enable debug mode, logging from DEBUG level"
                             "[default: off]")

    args = parser.parse_args()
    if (args.debug):
        logger.setLevel(logging.DEBUG)  # modify the logging level

    logger.debug("User inputs:")
    logger.debug(vars(args))

    kfolds = args.kfolds
    name = args.name

    DataSpec = namedtuple("DataSpec", ["name", "data_s3_url",
                                       "schema", "recipe",
                                       "ml_model_type", "sgd_maxPasses",
                                       "sgd_maxMLModelSizeInBytes",
                                       "sgd_l2RegularizationAmount"])

    # read datasource schema and training recipe from files:
    with open("banking.csv.schema", 'r') as schema_f:
        schema = schema_f.read()
    with open("recipe.json", 'r') as recipe_f:
        recipe = recipe_f.read()

    data_spec = DataSpec(name=name,
                         data_s3_url="s3://aml-sample-data/banking.csv",
                         schema=schema,
                         recipe=recipe,
                         ml_model_type="BINARY",
                         sgd_maxPasses="10",
                         sgd_maxMLModelSizeInBytes="104857600",  # 100MiB
                         sgd_l2RegularizationAmount="1e-4")

    eval_ids = build_folds(data_spec=data_spec, kfolds=kfolds)

    print("""

====================================
For the next step in the demo, run:
    python collect_perf.py {}""".format(" ".join(eval_ids)))
