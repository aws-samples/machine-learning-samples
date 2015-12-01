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
This module contains configurations consumed by the sample scripts. Feel free
to modify them based on instructions.
"""

# App Config

APP_NAME = "aws-ml-cross-validation"

# Rearrangement Config

# setting splitting strategy in DataRearrangement. User can change it
# to 'sequential' if the provided data is well shuffled.
# Learn more about DataRearrangement Strategy at
# http://docs.aws.amazon.com/machine-learning/latest/dg/data-rearrangement.html
STRATEGY = "random"

# setting the seed for 'random' splitting in DataRearrangement.
# If the splitting strategy is not 'random', then this setting
# is a no-op. Changing the random seed will result in different
# way to split the original data, which may impact the predictive
# performance metric.
# Learn more about DataRearrangement RandomSeed at
# http://docs.aws.amazon.com/machine-learning/latest/dg/data-rearrangement.html
RANDOM_STRATEGY_RANDOM_SEED = "RANDOMSEED"


# Polling Config

# setting the timeout (in seconds) waiting all Evaluation to complete
TIME_OUT = 3600  # 1 hour

# setting the initial polling delay (in seconds)
INITIAL_POLLING_DELAY = 1  # 1 second

# setting the max delay (in seconds) between two polls
DELAY_CAP = 600  # 10 mins
