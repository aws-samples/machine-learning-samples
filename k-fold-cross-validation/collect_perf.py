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
Demonstrate how to wait for Evaluation jobs to complete on Amazon ML,
collect performance metrics (AUC score), and generate an estimation of
the generalized performance for K-fold cross-validation.

usage: collect_perf.py [--debug] evals ...

example:
    python collect_perf.py ev-YOUR_1ST_EVAL ev-YOUR_2ND_EVAL ...

"""
import sys
import time
import boto
import random
import logging
import argparse
import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(config.APP_NAME)


def collect_perf(eval_id_list):
    """
    This function collects the AUC score for a list of
    evaluations (based on binary classification model)
    on Amazon ML. If any evaluation is in progress,
    the script will poll and wait with exponential
    backoff.

    Args:
        eval_id_list: a list of Evaluation IDs to collect
            performance metrics.
    Returns:
        a map of completed evaluation's ID to
            the corresponding AUC score.
    Raises:
        exception when any Evaluation is in
            Failed status.
    """
    ml = boto.connect_machinelearning()  # boto Amazon ML client
    completed_evals = dict()  # to collect completed Evaluations
    start_timestamp = time.time()  # start timestamp in seconds

    # time delay in seconds between two polling attempt
    polling_delay = config.INITIAL_POLLING_DELAY

    logger.info("Checking the Evaluation status...")
    while time.time() - start_timestamp < config.TIME_OUT:
        any_in_progress = False  # assume all complete

        for ev_id in eval_id_list:  # fetching each Evaluation status
            if ev_id in completed_evals:  # skip any completed Evaluations
                continue

            # fetch evaluation status
            evaluation = ml.get_evaluation(ev_id)
            eval_status = evaluation["Status"]
            logger.info("{} status: {}".format(ev_id, eval_status))

            if eval_status == "COMPLETED":
                # get the AUC score from the Evaluation
                auc = evaluation["PerformanceMetrics"][
                    "Properties"]["BinaryAUC"]
                # mark this Evaluation to be completed, and write down the
                # AUC score in floating point number. Note that this entity
                # will be skipped in next polling
                completed_evals[ev_id] = float(auc)
            elif eval_status == "FAILED":
                raise Exception("Evaluation {} is FAILED!".format(
                    ev_id))
            else:
                any_in_progress = True  # in progress

        if not any_in_progress:  # exit polling if all Evaluations completed
            break
        logger.debug("Next poll in {} seconds...".format(polling_delay))
        time.sleep(polling_delay)
        # update polling_delay in the next polling
        polling_delay = min(polling_delay * 2, config.DELAY_CAP)
    return completed_evals

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="%(prog)s [--debug] evals ... ",
        description="Demo code to collect AUC score from Evaluation entities \
            on Amazon ML, and generate the mean AUC score for the K-fold \
            cross-validation.")
    parser.add_argument("evals", nargs="+",
                        help="one or more Evaluation IDs")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="enable debug mode, logging from DEBUG level"
                             "[default: off]")
    args = parser.parse_args()
    if (args.debug):
        logger.setLevel(logging.DEBUG)  # modify the logging level

    logger.debug("User inputs:")
    logger.debug(vars(args))

    eval_id_list = args.evals
    kfolds = len(eval_id_list)
    eval_auc_map = collect_perf(eval_id_list)  # start polling & collect

    # Comput the mean/variance of auc scores. Casting kfolds to float for
    # Python 2 compatibility.
    avg_auc = sum([x for x in eval_auc_map.values()]) / float(kfolds)
    var_auc = sum([(x - avg_auc) ** 2 for x in eval_auc_map.values()]) / float(
        kfolds)

    print("""\

==========================
The mean of AUC score: {:.6f}
The variance of AUC score: {:.6f}""".format(avg_auc, var_auc))

    print("The ascending sorted list of AUC scores:")
    sorted_aucs = sorted(
        [(eval_auc_map[k], k) for k in eval_auc_map])
    for auc, ev_id in sorted_aucs:
        print("{}: {:.6f}".format(ev_id, auc))
