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
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.amazonaws.services.machinelearning.AmazonMachineLearningClient;
import com.amazonaws.services.machinelearning.model.CreateDataSourceFromS3Request;
import com.amazonaws.services.machinelearning.model.CreateEvaluationRequest;
import com.amazonaws.services.machinelearning.model.CreateMLModelRequest;
import com.amazonaws.services.machinelearning.model.MLModelType;
import com.amazonaws.services.machinelearning.model.S3DataSpec;

/**
 * This class demonstrates all the steps needed to build an ML Model for
 * the targeted marketing example in the Getting Started Guide for 
 * Amazon Machine Learning.
 */
public class BuildModel {

    public static void main(String[] args) throws IOException {
        String trainingDataUrl = "s3://aml-sample-data/banking.csv";
        String schemaFilename = "banking.csv.schema";
        String recipeFilename = "recipe.json";
        String friendlyEntityName = "Java Marketing Sample";
        
        BuildModel builder = new BuildModel(friendlyEntityName, trainingDataUrl, schemaFilename, recipeFilename);
        builder.build();
    }
    
    private AmazonMachineLearningClient client;
    private String friendlyEntityName;
    private String trainDataSourceId;
    private String testDataSourceId;
    private String mlModelId;
    private String evaluationId;
    private int trainPercent=70;
    private String trainingDataUrl;
    private String schemaFilename;
    private String recipeFilename;
    
    public BuildModel(String friendlyName, String trainingDataUrl, String schemaFilename, String recipeFilename) {
        this.client = new AmazonMachineLearningClient();
        this.friendlyEntityName = friendlyName;
        this.trainingDataUrl = trainingDataUrl;
        this.schemaFilename = schemaFilename;
        this.recipeFilename = recipeFilename;
    }

    private void build() throws IOException {
        createDataSources();
        createModel();
        createEvaluation();
    }

    private void createDataSources() throws IOException {
        trainDataSourceId = Identifiers.newDataSourceId();
        // trainDataSourceId = "ds-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        createDataSource(trainDataSourceId, friendlyEntityName + " - training data", 0, trainPercent);
        
        testDataSourceId = Identifiers.newDataSourceId();
        // testDataSourceId = "ds-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        createDataSource(testDataSourceId, friendlyEntityName + " - testing data", trainPercent, 100);
    }

    private void createDataSource(String entityId, String entityName, int percentBegin, int percentEnd) throws IOException {
        String dataSchema = Util.loadFile(schemaFilename);
        String dataRearrangementString = "{\"splitting\":{\"percentBegin\":"+percentBegin+",\"percentEnd\":"+percentEnd+"}}";
        CreateDataSourceFromS3Request request = new CreateDataSourceFromS3Request()
            .withDataSourceId(entityId)
            .withDataSourceName(entityName)
            .withComputeStatistics(true);
        S3DataSpec dataSpec = new S3DataSpec()
            .withDataLocationS3(trainingDataUrl)
            .withDataRearrangement(dataRearrangementString)
            .withDataSchema(dataSchema);
        request.setDataSpec(dataSpec);
        client.createDataSourceFromS3(request);
        System.out.printf("Created DataSource %s with id %s\n",  entityName, entityId);
    }
    
    /**
     * Creates an ML Model object, which begins the training process. 
     * The quality of the model that the training algorithm produces depends 
     * primarily on the data, but also on the hyper-parameters specified in 
     * the parameters map, and the feature-processing recipe.
     * @throws IOException 
     */
    private void createModel() throws IOException {
        mlModelId = Identifiers.newMLModelId();
        // mlModelId = "ml-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        
        Map<String, String> parameters = new HashMap<String,String>();
        parameters.put("sgd.maxPasses", "100");
        parameters.put("sgd.maxMLModelSizeInBytes", "104857600");  // 100 MiB
        parameters.put("sgd.l2RegularizationAmount", "1e-4");
        
        CreateMLModelRequest request = new CreateMLModelRequest()
            .withMLModelId(mlModelId)
            .withMLModelName(friendlyEntityName + " model")
            .withMLModelType(MLModelType.BINARY)
            .withParameters(parameters)
            .withRecipe(Util.loadFile(recipeFilename))
            .withTrainingDataSourceId(trainDataSourceId);
        client.createMLModel(request);
        System.out.printf("Created ML Model with id %s\n", mlModelId);
    }

    /**
     * Creates an Evaluation, which measures the quality of the ML Model
     * by seeing how many predictions it gets correct, when run on a 
     * held-out sample (30%) of the original data.
     */
    private void createEvaluation() {
        evaluationId = Identifiers.newEvaluationId();
        // evaluationId = "ev-" + UUID.randomUUID().toString();  // simpler, a bit more ugly
        CreateEvaluationRequest request = new CreateEvaluationRequest()
            .withEvaluationDataSourceId(testDataSourceId)
            .withEvaluationName(friendlyEntityName + " evaluation")
            .withMLModelId(mlModelId);
        client.createEvaluation(request);
        System.out.printf("Created Evaluation with id %s\n", evaluationId);
    }

}
