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
"""AWSPyML - Python utilities to help with Amazon Machine Learning.
"""
import boto
import csv
import json
import math
import random
import re


def aml_connection():
    """Connects to the service and validates that credentials are configured properly.
    """
    ml = boto.connect_machinelearning()
    try:
        # Check that the connection is configured properly
        ml.describe_ml_models(limit=1)
    except:
        raise RuntimeError("""There was a problem connecting to Amazon Machine Learning.
Be sure your AWS credentials are properly configured.
A credentials file should be in ~/.aws/credentials
(or C:\Users\USER_NAME\.aws\credentials on Windows)
and look like:

[Credentials]
aws_access_key_id = <your_access_key_here>
aws_secret_access_key = <your_secret_key_here>
    """)
    return ml


class Identifiers(object):
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'

    @classmethod
    def _new(cls, prefix=None):
        if prefix:
            out = prefix + '-'
        else:
            out = ''
        for i in range(11):
            # 62^11 -> 65 random bits, which is sufficient to avoid collisions
            # creating 1 entity per second for 200+ years.
            out += cls.chars[random.randint(0, len(cls.chars) - 1)]
        return out

    @classmethod
    def new_data_source_id(cls):
        return cls._new('ds')

    @classmethod
    def new_ml_model_id(cls):
        return cls._new('ml')

    @classmethod
    def new_evaluation_id(cls):
        return cls._new('ev')

    @classmethod
    def new_batch_prediction_id(cls):
        return cls._new('bp')


class AWSPyMLException(Exception):
    pass


class SchemaException(AWSPyMLException):
    pass


class InvalidSchemaException(SchemaException):
    pass


class JsonConfiguration(object):

    """Base class for JSON Configuration objects.
    """

    def as_obj(self):
        self.validate()
        return self._obj

    def _json_kwargs(self, dense):
        if dense:
            return {}
        else:
            return {"indent": 2}

    def validate(self):
        """Raises an exception if any of the contents do not match
        requirements.
        Should be overridden by sub-class.
        """
        pass  # base class does nothing

    def as_json_string(self, dense=False):
        self.validate()
        return json.dumps(self._obj, **(self._json_kwargs(dense)))

    def write_to_file(self, filename, dense=False):
        self.validate()
        f = open(filename)
        json.dump(self._obj, f, **self._json_kwargs(dense))
        f.close()

    def save_to_s3(self, s3url, dense=False):
        self.validate()
        raise "Not implemented yet"


class Schema(JsonConfiguration):

    """A Schema object for Amazon Machine Learning.
    Keeps track of variable types.  Helps format the
    JSON used by the API.
    """

    VALID_VARIABLE_TYPES = [
        "BINARY",
        "CATEGORICAL",
        "NUMERIC",
        "TEXT",
    ]

    def __init__(self):
        self._obj = {
            "version": "1.0",
            "dataFormat": "CSV",
            "attributes": [],
            "dataFileContainsHeader": True,
            "targetAttributeName": None,
            "excludedAttributeNames": [],  # Optional
            "rowId": None,  # Optional
        }

    def validate(self):
        """Validates that the schema object is properly formed.
        Either returns True or raises an exception.

        Note this is not 100% robust and might not catch all
        problems that the API will catch.
        """
        if self.num_attributes() == 0:
            raise InvalidSchemaException("no attributes defined")
        for idx, var in enumerate(self.attributes()):
            name = var["attributeName"]
            typ = var["attributeType"]
            if not name or not typ:
                raise InvalidSchemaException(
                    "Variable #%d is not fully defined" % idx)
            if len(name) > 64:
                raise InvalidSchemaException("%s" % var["attributeName"])
            if typ not in self.VALID_VARIABLE_TYPES:
                raise InvalidSchemaException(
                    "variable %s has invalid type %s" % (name, typ))
        return True  # Passes all rules.

    def set_target(self, target_variable_name):
        """Sets the target variable to the variable of the specified name
        """
        if not self.get_variable_by_name(target_variable_name):
            raise SchemaException("Can't set target to undefined variable %s" %
                                  target_variable_name)
        self._obj['targetAttributeName'] = target_variable_name

    def set_variable_name(self, idx, name):
        """For variable in the position idx, set its name
        """
        self.get_variable_by_idx(idx)['attributeName'] = name

    def set_variable_type(self, idx, attributeType):
        """For variable in the position idx, set its field type.
        """
        self.get_variable_by_idx(idx)['attributeType'] = attributeType

    def num_attributes(self):
        return len(self._obj['attributes'])

    def attributes(self):
        return self._obj["attributes"]

    def get_variable_by_name(self, name):
        for var in self.attributes():
            if var["attributeName"] == name:
                return var
        return None

    def get_variable_by_idx(self, idx):
        if self.num_attributes() <= idx:
            # The list is too small, so we expand it
            amount = 1 + idx - self.num_attributes()
            self._obj['attributes'].extend(
                [{
                    "attributeName": None,
                    "attributeType": None,
                }] * amount
            )
        return self._obj['attributes'][idx]

    def set_header_line(self, header_line):
        """Takes a boolean to specify whether or not the
        data file(s) contain a header line with the names
        of the attributes in it
        """
        self._obj["dataFileContainsHeader"] = header_line


class SchemaGuesser(object):

    """Guesses at a good Schema object by looking at sample data.
    """

    def __init__(self):
        self.data = []
        self.num_attributes = 0
        self.schema = Schema()
        self.text_words_threshold = 20  # Heuristic.

    def from_file(self, filename, target_variable=None, header_line='auto',
                  num_lines_to_use=1000):
        """Returns a Schema object that is guessed by looking at the first
        num_lines_to_use records from the given file.

        Can set header_line to true or false if known, otherwise, it guesses.
        """
        f = open(filename)
        try:
            self._load_csv_data(f, num_lines_to_use)
            schema = self._guess_schema_from_data(header_line)
            if target_variable:
                schema.set_target(target_variable)
            return schema
        finally:
            f.close()

    def _guess_schema_from_data(self, header_line):
        if header_line == 'auto':
            header_line = self._guess_if_header_line_present()
        self._name_attributes(header_line)

        for i in xrange(self.num_attributes):  # Loop through columns
            column = [row[i] for row in self.data]
            if header_line:
                column = column[1:]
            self.schema.set_variable_type(i, self._guess_variable_type(column))
        return self.schema

    def _guess_variable_type(self, samples):
        counts = {
            "NUMERIC": 0,
            "BINARY": 0,
            "TEXT": 0,
            "CATEGORICAL": 0,
        }
        for sample in samples:
            try:
                num = float(sample)
                counts["NUMERIC"] += 1
                if num == 0 or num == 1:
                    counts["BINARY"] += 1
            except:
                # Non-numeric
                word_count = len(re.split("\s+", sample))
                if word_count > self.text_words_threshold:
                    counts["TEXT"] += 1
                else:
                    counts["CATEGORICAL"] += 1
        return max(counts, key=counts.get)

    def _name_attributes(self, header_line):
        digits = int(math.floor(math.log10(self.num_attributes))) + 1
        for idx, name in enumerate(self.data[0]):
            if header_line:
                self.schema.set_variable_name(idx, name)
            else:
                name = "Var{number:0{width}d}".format(width=digits, number = idx + 1)
                self.schema.set_variable_name(idx, name)

    def _guess_if_header_line_present(self):
        header_row = self.data[0]
        has_header_line = self._guess_variable_type(
            header_row) == "CATEGORICAL"
        self.schema.set_header_line(has_header_line)
        return has_header_line

    def _load_csv_data(self, csvfile, num_lines_to_use):
        """Loads at most num_lines_to_use records from the open file with csv
        data.  Returns as list of lists.
        """
        csvreader = csv.reader(csvfile)
        for record in csvreader:
            self.data.append(record)
            if len(self.data) == num_lines_to_use:
                break
        self.num_attributes = len(self.data[0])
