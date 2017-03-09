#!/usr/bin/python

# select AWS cmd profile by using env var AWS_PROFILE, otherwise will rely on defaults
import sys
import zlib
import boto3
import numpy as np
from datetime import datetime
from urlparse import urlparse
from cStringIO import StringIO
import matplotlib.pyplot as plt
from optparse import OptionParser

def utc_now_str():
	return str(datetime.utcnow()).replace(" ", "-").replace(":", "-").split(".", 1)[0] + "Z"

# kick off a batch prediction for a given test dataset and save the results to the specified location in S3
def complete_batch_prediction(ml_model_id, test_datasource_id, output_uri_s3):
	ml = boto3.client('machinelearning')
	ts = utc_now_str() 
	batch_prediction_id = "bp-cost-based-{ts}".format(ts=ts)
	print >> sys.stderr, "Creating --batch-prediction-id={}\n".format(batch_prediction_id)
	batch_prediction_name = "BP Cost Based {ts}".format(ts=ts)
	result = ml.create_batch_prediction(MLModelId=ml_model_id, BatchPredictionDataSourceId=test_datasource_id, BatchPredictionId=batch_prediction_id, BatchPredictionName=batch_prediction_name, OutputUri=output_uri_s3)
	ml.get_waiter('batch_prediction_available').wait()
# TODO add error checking, assuming success
	return batch_prediction_data_bucket_key(output_uri_s3, batch_prediction_id)

# convert S3 URI and batch prediction id to a combination of bucket and key
def batch_prediction_data_bucket_key(output_uri_s3, batch_prediction_id):
	ml = boto3.client('machinelearning')
	input_data_location_s3 = ml.get_batch_prediction(BatchPredictionId=batch_prediction_id)['InputDataLocationS3']
	uri_components = urlparse(input_data_location_s3)
	datasource_filename = uri_components.path.split('/')[-1]
        uri_components = urlparse(output_uri_s3)
        bucket, key = uri_components.netloc, uri_components.path[1:]
	key += "batch-prediction/result/{}-{}.gz".format(batch_prediction_id, datasource_filename)
	return bucket, key

# read batch prediction results from S3 and turn them into an numpy array
def read_test_predictions(bucket, key):
	s3 = boto3.resource('s3')
	obj = s3.Object(bucket, key)
	predictions_str = zlib.decompress(obj.get()['Body'].read(), 15+32).decode('utf-8')
        names = predictions_str.split('\n', 1)[0].split(',')
#	print names
	# TODO a bit hacky, find a better way to parse
	# if tag column is present, skip it
	cols = (1, 3) if names[0] == 'tag' else (0, 2)
 	formats = ('bool', 'float')
	names = [names[index] for index in cols]
	data = np.loadtxt(StringIO(predictions_str), dtype = {'names': names, 'formats': formats}, delimiter=',', skiprows=1, usecols=cols)
	return data

# this historgram replicates what the Amazon ML console is showing for model evaluation
def plot_class_histograms(score_n_true_label):
	class_1_scores = [score for (score, true_label) in score_n_true_label if true_label == 1]
	class_0_scores = [score for (score, true_label) in score_n_true_label if true_label == 0]

        class_1_score_histogram, bins       = np.histogram(class_1_scores, bins=100, range=(0.,1.))
        class_0_score_histogram, _dont_care = np.histogram(class_0_scores, bins=100, range=(0.,1.))
        mean = (np.mean(class_1_score_histogram) + np.mean(class_0_score_histogram)) / 2.0

	plt.figure()
	plt.plot(bins[:-1], class_1_score_histogram, c='blue', label='class 1')
	plt.plot(bins[:-1], class_0_score_histogram, c='green', label='class 0')
	plt.axis([0, 1, 0, mean*3])
	plt.legend()
	plt.title('Distribution of scores for each class')
	plt.xlabel('score')
	plt.ylabel('test samples')
	plt.draw()

# compute the cost for a particular threshold
def apply_costs(costs, true_neg, true_pos, false_neg, false_pos):
	return (costs['tn']*true_neg + costs['tp']*true_pos + costs['fn']*false_neg + costs['fp']*false_pos)/float(true_neg + true_pos + false_neg + false_pos)

# find the first optimal threshold (aka cutoff) score that tunes the ML model to produce lowest cost results
def find_optimal_threshold(score_n_true_label, costs):
	just_labels = list(zip(*score_n_true_label)[1])
	class_0_count, class_1_count = np.bincount(just_labels)

	sum_class_0 = 0
	sum_class_1 = 0
	lowest_cost = sys.float_info.max
	best_threshold = 0.0
	threshold_costs = []
	for score, true_label in score_n_true_label:
		true_neg  = sum_class_0
		true_pos  = class_1_count - sum_class_1
		false_neg = sum_class_1
		false_pos = class_0_count - sum_class_0
		threshold_cost = apply_costs(costs, true_neg, true_pos, false_neg, false_pos)
		threshold_costs.append((score, threshold_cost))
		if threshold_cost < lowest_cost:
			best_threshold = score
			lowest_cost = threshold_cost
		if true_label == 0:
			sum_class_0 += 1
		else:
			sum_class_1 += 1
	return best_threshold, lowest_cost, threshold_costs

# the plot shows the cost curve and draws the position and the level of the lowest cost and best threshold
def plot_threshold_costs(threshold_costs, best_threshold, lowest_cost):
	plt.figure()

	thresholds = list(zip(*threshold_costs)[0])
	costs = list(zip(*threshold_costs)[1])
	plt.plot(thresholds, costs, c='red', label='cost')
	mean = np.mean(costs)
	plt.axis([0, 1, 0, mean*3])

	plt.plot([0, 1], [lowest_cost, lowest_cost], 'k-', label='lowest cost')
	plt.plot([best_threshold, best_threshold], [0, lowest_cost], 'k-')

	plt.legend()
	plt.title('Threshold cost')
	plt.xlabel('score threshold')
	plt.ylabel('cost')
	plt.draw()

def parse_options():
	parser = OptionParser(usage="usage: %prog [options]")
	parser.add_option("-m", "--ml-model-id", dest="ml_model_id", help="use Amazon ML model with ML_MODEL_ID")
	parser.add_option("-d", "--test-datasource-id", dest="test_datasource_id", help="use test datasource with TEST_DATASOURCE_ID")
	parser.add_option("-o", "--output-uri-s3", dest="output_uri_s3", help="write model predictions for test dataset to OUTPUT_URI_S3, read from there for cost analysis") 
	parser.add_option("-b", "--batch-prediction-id", dest="batch_prediction_id", help="BATCH_PREDICTION_ID of the already computed batch of predictions for test datasource") 
	parser.add_option("--true-pos", dest="true_pos", help="true positives have cost COST units, 0.0 by default", default=0.0, type='float', metavar='COST') 
	parser.add_option("--true-neg", dest="true_neg", help="true negatives have cost COST units, 0.0 by default", default=0.0, type='float', metavar='COST') 
	parser.add_option("--false-pos", dest="false_pos", help="false positives have cost COST units, 0.0 by default", default=0.0, type='float', metavar='COST') 
	parser.add_option("--false-neg", dest="false_neg", help="false negatives have cost COST units, 0.0 by default", default=0.0, type='float', metavar='COST') 
	(options, args) = parser.parse_args()
	if not options.output_uri_s3:
		print >> sys.stderr, "--output-uri-s3 is required"
		parser.print_help()
		sys.exit(1)
	return (parser, options)

def batch_predictions_already_evaluated(parser, options):
	if not options.ml_model_id or not options.test_datasource_id:
		print >> sys.stderr, "Model id and/or datasource id is not supplied, assuming batch prediction results for test datasource are already available"
		if not options.batch_prediction_id:
			print >> sys.stderr, "--batch-prediction-id not specified, exiting"
			parser.print_help()
			sys.exit(1)
		else:
			return True
	else:
		return False

def main():
	(parser, options) = parse_options()
	output_uri_s3 = options.output_uri_s3
	costs = { 'tn': options.true_neg, 'tp': options.true_pos, 'fn': options.false_neg, 'fp': options.false_pos }

	bucket, key = None, None
	if not batch_predictions_already_evaluated(parser, options):
		ml_model_id = options.ml_model_id
		test_datasource_id = options.test_datasource_id
		print >> sys.stderr, "Generating batch predictions with model {} and datasource {} => {}\n".format(ml_model_id, test_datasource_id, output_uri_s3)
		print >> sys.stderr, "This may take a few minutes, please, wait ...\n"
		bucket, key = complete_batch_prediction(ml_model_id, test_datasource_id, output_uri_s3)
	else:
		batch_prediction_id = options.batch_prediction_id
		bucket, key = batch_prediction_data_bucket_key(output_uri_s3, batch_prediction_id)

	print >> sys.stderr, "Reading prediction data from s3://{}/{}\n".format(bucket, key)

	test_predictions = read_test_predictions(bucket, key)
	test_predictions = np.sort(test_predictions, order='score')
#	print test_predictions
#	print "predictions data shape = {}\n".format(test_predictions.shape)

	score_n_true_label = np.array([(e2, int(e1)) for e1, e2 in test_predictions])
#	print score_n_true_label

	plot_class_histograms(score_n_true_label)

	best_threshold, lowest_cost, threshold_costs = find_optimal_threshold(score_n_true_label, costs)
	print "best_threshold = {}, lowest cost = {}\n".format(best_threshold, lowest_cost)
	plot_threshold_costs(threshold_costs, best_threshold, lowest_cost)

	plt.show()
	return threshold_costs

main()
