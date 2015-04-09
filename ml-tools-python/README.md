# ML Tools

These are utilities that we've found helpful when working with
Amazon Machine Learning.

## Schema Guesser

This script examines the first 1,000 lines of a local CSV file, and
uses them to generate a JSON schema.  

Amazon Machine Learning's API requires you to specify exactly what type of
data is in each column of your CSV in a schema file.  The web console makes
guesses for you to simplify this process.  This utility makes similar
guesses.

For usage information run:

    python guess_schema.py


## Wait For Entity

This script polls the status of an entity (data source, ML model, evaluation, 
or batch prediction) waiting for it to reach a terminal state.

Many operations in Amazon Machine Learning are asynchronous, including all
of the Create... operations.  Most of these can be chained together so that
they will wait until their dependencies are complete before starting.
However some operations (like setting the score threshold on a model)
require the entity to be in a COMPLETED state before they will run.  This
utility provides a simple way to watch the progress of your entities.

For usage information run:

    python wait_for_entity.py


## Realtime Prediction Tool

This script enables realtime predictions through a simple command line 
interface.  It will automatically create a realtime endpoint if one is 
needed, and lets you delete the endpoint when you are done.

NOTE: Your account will be charged an hourly realtime reservation 
fee for every ML model that has a realtime endpoint.  So remember to 
delete the endpoints when you are done using them.

For usage information run:

    python realtime.py


## AWSPyML library

This is a set of classes and functions that might be useful in developing
predictive applications with Amazon Machine Learning.  There are utilities
for testing the configuration of a connection to Amazon Machine Learning,
for generating friendly identifiers, and classes for working with Schema
files.  The `guess_schema.py` script relies on this library.

