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
Schema guessing utility for Amazon Machine Learning.
Looks at the beginning of a CSV file and makes a guess as to what
data type each column is.  Then produces a valid JSON schema that
can be passed to create_data_source_from_s3 method.

Usage:
    python guess_schema.py data_file.csv [target_variable_name] > data_file.csv.schema

If specified, target_variable_name should match one of the variables
in the file's header.
"""
import sys
import awspyml


if __name__ == "__main__":
    try:
        data_fn = sys.argv[1]
        target = None
        if len(sys.argv) > 2:
            target = sys.argv[2]
    except:
        print(__doc__)
        sys.exit(-1)
    schema = awspyml.SchemaGuesser().from_file(data_fn, target_variable=target)
    print(schema.as_json_string())
