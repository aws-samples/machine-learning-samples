# Social Media Filtering with Amazon Machine Learning

Amazon Machine Learning can help your company make better use of social
media.  This example application will automatically analyze Twitter content
to identify customer support issues.  This application will continuously
monitor all tweets that mention your company's Twitter handle, and predict
whether or not your company's customer support team should reach out to the
poster.  By using a machine learning (ML) model as your first tier of
support you can lower support costs and increase customer satisfaction. The
same application integrates Amazon Machine Learning with Amazon Mechanical
Turk, Amazon Kinesis, AWS Lambda, and Amazon Simple Notification Service
(Amazon SNS).

The example walks through the following steps:

1. [Gather training data](#step1)
2. [Label training data with Amazon Mechanical Turk](#step2)
3. [Create the ML Model](#step3)
4. [Configure the model](#step4)
5. [Set up continuous monitoring](#step5)

## Skipping ahead

That this repository includes examples of the output of the first two steps
(gathering and labeling training data), so if you're anxious to get going,
and see ML working, you can jump ahead to step 3.  Just download a sample
of labelled training data from the `@awscloud` account which is on S3 at
[`https://aml-sample-data.s3.amazonaws.com/social-media/aml_training_dataset.csv`](https://aml-sample-data.s3.amazonaws.com/social-media/aml_training_dataset.csv)
(Its S3 URL is `s3://aml-sample-data/social-media/aml_training_dataset.csv`.)
Copy that file to your local directory named `aml_training_dataset.csv`, which is the
final output of step 2.

You might be tempted to try using a model trained on our example data for
your own application, but we don't recommend it.  In ML, the quality of
data is the most important thing.  So if you use somebody else's data to
analyze your customers, it's probably not going to work very well.

## Step 0: Setting up your environment

You will need python `virtualenv` and the `npm` node.js package manager.
On linux machines with `apt-get`, you can install them with the commands:

    sudo apt-get update
    sudo apt-get install python-virtualenv python-dev libffi-dev npm

Once those are installed, execute

    source setup.sh

The script uses `npm` and python's `virtualenv` to setup the required dependencies
and environment variables in the current shell.

The following scripts depend on the python boto library. See
[instructions](http://boto.readthedocs.org/en/latest/boto_config_tut.html)
on how setup credentials for boto in ~/.aws/credentials. See
[instructions](http://blogs.aws.amazon.com/security/post/Tx1R9KDN9ISZ0HF/Where-s-my-secret-access-key)
on how to get AWS credentials. The AWS user that you choose, needs
access to a subset of the following policy to run the scripts:

    {
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:*",
                    "machinelearning:*",
                    "kinesis:*",
                    "lambda:*",
                    "s3:*",
                    "sns:*"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }

## <a name="step1"></a> Step 1: Gathering training data

To gather the training data, run the following command:

    python gather-data.py @awscloud

Substitute your company's twitter handle instead of @awscloud and
configure your Twitter API credentials in config.py. Learn how to
obtain your credentials
[https://dev.twitter.com/oauth/overview/application-owner-access-tokens](here).

This will produce a file called `line_separated_tweets_json.txt` that
other scripts will read later.

## <a name="step2"></a> Step 2: Label training data with Mechanical Turk

In this application, as in many ML applications, we're trying to
build an ML model that mimics the behavior or opinions of humans.
Building a good model requires lots of examples of the choices that
humans would make.  Doing this yourself is always an option, but
often too slow or expensive to be practical.  In supervised machine
learning, these opinions are called the labels, or the target of
the model.

Amazon Mechanical Turk (Mturk) is a great way to quickly and
economically label large quantities of data.  This section will
walk through that process.

### Step 2a: Prepare tweets for labelling with MTurk

The first step is to take the raw JSON data that we have received from the Twitter API and
convert it to a CSV format that Mechanical Turk can use.  Do this by running:

    python build-mturk-csv.py

This will consume the `line_separated_tweets_json.txt` file and output a file called
`mturk_unlabeled_dataset.csv`.

### Step 2b: Submit the job to MTurk

Use the [Mechanical Turk Console](https://www.mturk.com/mturk/welcome) to create a set
of Human Intelligence Tasks (HITs) to assign labels to these tweets.  Turkers will be
asked to pick which label best applies to the tweet amongst:

* Request
* Question
* Problem Report
* Angry
* None of the above (i.e. non-actionable)

These different categories will be collapsed into a single binary attribute of
actionable / non-actionable.  But asking for more detail can help the Turkers focus
on the content better, and raises the opportunity to create more sophisticated ML
Models later with the same data.

For each tweet, we will create 3 HITs so that we can automatically figure out consensus
between three different human opinions on the tweet.

#### Detailed steps for generating training labels using MTurk
1. Create an account with [Mechanical Turk](https://requester.mturk.com/begin_signin)
1. [Start a new project](https://requester.mturk.com/create/projects/new)
1. Select *Other* from the options and click *Create Project*
1. Enter properties on next page. Suggested values (unless you know better):
  * *Project Name*: Labeling of tweets
  * *Title*: Categorize the tweet (WARNING: This HIT may contain adult content. Worker discretion is advised.)
  * *Description*: Categorize the tweet into 1 of 5 categories.
  * *Keywords*: tweet, tweets, categorization, labeling, sentiment
  * *Checkbox for adult content*: Select as checked because content may contain offensive tweets. [See details](https://requester.mturk.com/help/faq#can_explicit_offensive)
  * *Rewards per assignment*: Higher values can fetch faster results.
  * *Number of assignments per HIT*: 3
  * *Time allotted per assignment*: 2
  * *HIT expires in*: 7 days
  * *Auto-approve and pay Workers in*: 2 Hours
1. On the page for design layout, click the *Source* button and cut paste contents from mturk-project-template.xml. You may preview and edit as deemed fit. Parameter value ${tweet} and checkbox values should be left unmodified as the later steps depend on them.
1. Preview and finish. This creates the Project template.
1. Goto [Create New Batch with an Existing Project](https://requester.mturk.com/create/projects)
1. Select *Publish Batch* for the project you just created.
1. Follow instructions on the following screen. You will be using the csv file produced by build-mturk-csv.py as part of them.
1. Preview the HITs and submit the batch for labeling. *This step will cost you money*

### Step 2c: Processing the output from MTurk

Once all of your Turk HITs are complete, [download the results](https://requester.mturk.com/batches) into a file
called `mturk_labeled_dataset.csv`.  Then run the script

    python build-aml-training-dataset.py

to convert the 3 HIT responses for each tweet into a single dataset with a binary attribute.

## <a name="step3"></a> Step 3: Create the ML Model

Once you have your labelled training data in CSV format, creating the ML model requires a few
API calls, which are automated in this script:

    python create-aml-model.py aml_training_dataset.csv aml_training_dataset.csv.schema s3-bucket-name s3-key-name

This utility creates a machine learning model that performs binary classification.
Requires input dataset and corresponding scheme specified through file names in
the parameter. This utility splits the dataset into two pieces, 70% of the
dataset is used for training and 30% of the dataset is used for evaluation.
Once training and evaluation is successful, AUC is printed which indicates the
quality of the model -- the closer to 1.0 the better.


### <a name="step4"></a> Step 4: Configuring the model

Once your model is built, you need to decide how sensitive your model should be. The
model summary page provides the configuration options to modify the model's
sensitivity. A link to the model summary is printed when you run the tool in the
previous step. You can also lookup the model from the
[Amazon ML web console](https://console.aws.amazon.com/machinelearning). Here you can
set the score threshold.  A lower value means more tweets will be classified as
actionable, but there will also be more "false positives" where the model predicts
something is actionable that isn't. And vice versa.

## <a name="step5"></a> Step 5: Set up continuous monitoring

Continuous monitoring requires following parts:

1. Receiver of tweets from Twitter streaming api.
1. Kinesis stream to which the previous receiver pushes the tweets.
1. Lambda function that process records from Kinesis stream.
1. Realtime machine learning endpoint which is called by the Lambda function to
   make predictions on the incoming tweets.
1. SNS Topic to which the Lambda function pushes notifications in case a tweet
   requires response from the customer service.

*NOTE: Components being setup in this step have ONGOING costs associated
with them. Please check respective pricing schemes for details.*

### Step 5a: Setting up Kinesis/Lambda/Machine Learning realtime endpoint/SNS

Use the following script to automate the creation of Kinesis Stream, Lambda
function, the machine learning realtime endpoint, and the SNS Topic.

    python create-lambda-function.py

This script requires that `create-lambda-function.config` is present and contains
appropriate values. Description of the configuration required in
`create-lambda-function.config` is as follows:

* *awsAccountId* : The AWS Account Id corresponding to the credentials being used
  with boto. See [docs](http://docs.aws.amazon.com/general/latest/gr/acct-identifiers.html)
  for details.
* *kinesisStream* : The name being given to the Kinesis stream. See
  [docs](http://docs.aws.amazon.com/kinesis/latest/APIReference/API_CreateStream.html) for
  constraints.
* *lambdaFunctionName* : The name being given to the Lambda function. See
  [docs](http://docs.aws.amazon.com/lambda/latest/dg/API_UploadFunction.html) for constraints.
* *lambdaExecutionRole* : The name being given to the execution role
  used by the lambda function. See
  [docs](http://docs.aws.amazon.com/lambda/latest/dg/lambda-introduction.html#lambda-intro-execution-role)
  for details. See
  [docs](http://docs.aws.amazon.com/IAM/latest/APIReference/API_CreateRole.html)
  for constraints.
* *mlModelId* : The name of the machine learning model id which is used to
  perform predictions on the tweets. This is the id of the model that is
  generated as part of Step 3.
* *region* : AWS region used for each of the service. See
  [docs](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
  for details.
* *snsTopic* : The name of the topic that is created with Simple Notification
  Service. See [docs](http://docs.aws.amazon.com/sns/latest/APIReference/API_CreateTopic.html)
  for constraints.

### Step 5b: Testing the continuous monitoring setup

After the successful execution of this script the Kinesis stream is ready to accept
tweets data. Use the following script to test that the setup works.

    python push-json-to-kinesis.py line_separated_json.txt kinesisStreamName interval

The following parameters are needed to run this script

* *line_separated_json.txt* : File that contains line separated json data.
* *kinesisStreamName*       : Name of the stream to which the data is pushed to.
* *interval*                : Interval in milli-seconds between two calls to kinesis stream.

This script merely pushes json data to the given Kinesis stream. As at this step, we have the file
from previous steps that contains line separated tweets json data, we reuse it for testing.

### Step 5c: Pushing tweets into Kinesis using Twitter's Streaming APIs

This project includes a sample app to push into Kinesis tweets that
match a simple filter using Twitter's
[public stream API](https://dev.twitter.com/streaming/public). For a
production system, you can work with [GNIP](http://www.gnip.com) to
consume streams. Refer to their
[blog post](http://support.gnip.com/code/gnip-kinesis-ami.html) on the
subject, or their
[open source code on github](https://github.com/gnip/sample-kinesis-connector).

You'll need a twitter library that supports streaming:

    pip install twitter

Modify `config.py` to add a kinesis partition name, the twitter text
filter you'd like to search for, and your twitter credentials if you
haven't already done so. Then simply call the sample scanner.

    python scanner.py

Tweets that match your filter will be processed in real time and
pushed to the kinesis stream. The lambda function will use the ML
model to classify these tweets and publish a notification to the
configured SNS topic with a link to any tweet that is considered
actionable. The easiest way to get these notifications is to
[subscribe your email address to the SNS topic](http://docs.aws.amazon.com/sns/latest/dg/SubscribeTopic.html).
