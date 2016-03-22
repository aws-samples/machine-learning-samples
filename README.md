# Amazon Machine Learning Samples

Each subdirectory contains sample code for using Amazon Machine Learning.
Refer to the `README.md` file in each sub-directory for details on using
each sample.

## Targeted Marketing Samples

These samples show how to use the Amazon Machine Learning API for a
targeted marketing application.  This follows the "banking" dataset example
described in the Developer Guide.  There are three versions available:

* [Targeted Marketing with Machine Learning in Java](targeted-marketing-java/)
* [Targeted Marketing with Machine Learning in Python](targeted-marketing-python/)
* [Targeted Marketing with Machine Learning in Scala](targeted-marketing-scala/)


## Social Media and Amazon Mechanical Turk

This sample application shows how to use Amazon Mechanical Turk to create a
labeled dataset from raw tweets, and then build a machine learning model
using the Amazon Machine Learning API that predicts whether or not new
tweets should be acted upon by customer service.  The sample shows how to
set up an automated filter using AWS Lambda that monitors tweets on an
Amazon Kinesis stream and sends notifications whenever the ML Model
predicts that a new tweet is actionable.  Notifications go to Amazon SNS,
allowing delivery to email, SMS text messages, or other software services.

* [Machine-Learning based Social Media Filtering (Python & JavaScript)](social-media/)


## Mobile Prediction Samples

These samples show how to use the Amazon Machine Learning API to make
real-time predictions from a mobile device.  There are two versions available:

* [Real-time Machine Learning Predictions from iOS](mobile-ios/)
* [Real-time Machine Learning Predictions from Android](mobile-android/)


## K-fold Cross-validation Sample

This sample shows how to use the Amazon Machine Learning API to evaluate ML models using k-fold cross-validation.

* [K-fold Cross-validation Sample (Python)](k-fold-cross-validation/)


## Other tools

A collection of simple scripts to help with common tasks.

* [Machine Learning Tools (python)](ml-tools-python/)


## Support

For assistance with using the Amazon Machine Learning Service, or these samples, please see the [AWS Forums](https://forums.aws.amazon.com/forum.jspa?forumID=194&start=0).
