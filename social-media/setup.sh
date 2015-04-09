#!/bin/bash
# This script sets up the node.js and python dependencies.

rm -rf node_modules/
npm install aws-sdk

virtualenv --clear local-python
source local-python/bin/activate
pip install --upgrade pip
pip install ndg-httpsclient pyasn1 pyopenssl python-twitter unicodecsv
pip install boto
