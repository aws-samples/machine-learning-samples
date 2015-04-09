# Making real-time predictions from Android

Here is sample code showing how to use Amazon Machine Learning to get
real-time predictions from Android.

## How to use

Instantiate the `AndroidRealtimePrediction` with AWS credentials, and the
name of the ML Model that you want to use.  (Note this model must have a
realtime endpoint created.)

Then you can call `.predict(record)` passing in a record as a Java Map from
attribute names to values.

## Example applications

Real-time predictions from mobile devices can be used for a wide variety of
applications.  Some examples include:

* Decide whether or not to show an offer to a customer
* Matching up game players with similar skill levels
* Rank content that is most relevant to current user

