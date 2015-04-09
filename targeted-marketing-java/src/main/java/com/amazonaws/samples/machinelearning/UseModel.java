/*
 * Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * 
 * Licensed under the Amazon Software License (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 * 
 *  http://aws.amazon.com/asl/
 * 
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express
 * or implied. See the License for the specific language governing permissions
 * and limitations under the License.
 */
package com.amazonaws.samples.machinelearning;

import java.io.IOException;
import java.util.Date;
import java.util.Random;
import java.util.UUID;

import com.amazonaws.services.machinelearning.AmazonMachineLearningClient;
import com.amazonaws.services.machinelearning.model.CreateBatchPredictionRequest;
import com.amazonaws.services.machinelearning.model.CreateDataSourceFromS3Request;
import com.amazonaws.services.machinelearning.model.GetMLModelRequest;
import com.amazonaws.services.machinelearning.model.GetMLModelResult;
import com.amazonaws.services.machinelearning.model.S3DataSpec;
import com.amazonaws.services.machinelearning.model.UpdateMLModelRequest;

/**
 * This class demonstrates using a model built by 
 * {@link com.amazonaws.samples.machinelearning.BuildModel}
 * to make batch predictions.
 */
public class UseModel {

    private static final String UNSCORED_DATA_S3_URL = "s3://aml-sample-data/banking-batch.csv";
    private static final String UNSCORED_DATA_LOCAL_SCHEMA = "banking-batch.csv.schema";

    public static void main(String[] args) throws IOException {
        UseModel useModel = new UseModel(args);
        useModel.waitForModel();
        useModel.setThreshold();
        useModel.createBatchPrediction();
    }
    
    private String mlModelId;
    private float threshold;
    private String s3OutputUrl;
    private AmazonMachineLearningClient client;
    private Random random;
    private String schemaFilename;
    
    /**
     * @param args command-line arguments:
     *   mlModelid
     *   score threshhold
     *   s3:// url where output should go
     */
    public UseModel(String[] args) {
        mlModelId = args[0];
        threshold = Float.valueOf(args[1]);
        s3OutputUrl = args[2];
        this.client = new AmazonMachineLearningClient();
        random = new Random();
    }


    /**
     * waits for the model to reach a terminal state.
     */
    private void waitForModel() {
        long delay = 2000;
        while(true) {
            GetMLModelRequest request = new GetMLModelRequest()
                .withMLModelId(mlModelId);
            GetMLModelResult model = client.getMLModel(request);
            System.out.printf("Model %s is %s at %s\n", mlModelId, model.getStatus(), (new Date()).toString());
            switch(model.getStatus()) {
            case "COMPLETED":
            case "FAILED":
            case "INVALID":
                // These are terminal states
                return;
            }
            
            // exponential backoff with Jitter
            delay *= 1.1 + random.nextFloat();
            try {
                Thread.sleep(delay);
            } catch (InterruptedException e) {
                e.printStackTrace();
                return;
            }
        }
        
    }
    
    
    /**
     * Sets the score threshold on the ML Model.
     * This configures the ML Model by picking what raw prediction score
     * is the cut-off between a positive & a negative prediction.
     */
    private void setThreshold() {
        UpdateMLModelRequest request = new UpdateMLModelRequest()
            .withMLModelId(mlModelId)
            .withScoreThreshold(threshold);
        client.updateMLModel(request);
    }
    

    private void createBatchPrediction() throws IOException {
        // First create a datasource for the input data for the batch prediction
        String dataSourceId = Identifiers.newDataSourceId();
        // dataSourceId = "ds-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        S3DataSpec dataSpec = new S3DataSpec()
            .withDataSchema(Util.loadFile(UNSCORED_DATA_LOCAL_SCHEMA))
            .withDataLocationS3(UNSCORED_DATA_S3_URL);
        CreateDataSourceFromS3Request dsRequest = new CreateDataSourceFromS3Request()
            .withDataSourceId(dataSourceId)
            .withDataSourceName("DataSource for batch prediction")
            .withDataSpec(dataSpec)
            .withComputeStatistics(false);
        client.createDataSourceFromS3(dsRequest);
        System.out.printf("Created DataSource for batch prediction with id %s\n", dataSourceId);
        
        String batchPredictionId = Identifiers.newBatchPredictionId();
        // batchPredictionId = "bp-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        CreateBatchPredictionRequest bpRequest = new CreateBatchPredictionRequest()
            .withBatchPredictionId(batchPredictionId)
            .withBatchPredictionName("Java sample Batch Prediction")
            .withMLModelId(mlModelId)
            .withOutputUri(this.s3OutputUrl)
            .withBatchPredictionDataSourceId(dataSourceId);
        client.createBatchPrediction(bpRequest);
        System.out.printf("Created BatchPrediction with id %s\n", batchPredictionId);
    }

}
