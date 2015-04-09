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

import java.util.HashMap;
import java.util.Map;
 
import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.services.machinelearning.AmazonMachineLearningClient;
import com.amazonaws.services.machinelearning.model.EntityStatus;
import com.amazonaws.services.machinelearning.model.GetMLModelRequest;
import com.amazonaws.services.machinelearning.model.GetMLModelResult;
import com.amazonaws.services.machinelearning.model.PredictRequest;
import com.amazonaws.services.machinelearning.model.PredictResult;
import com.amazonaws.services.machinelearning.model.RealtimeEndpointStatus;

/**
 * Android code to make realtime predictions from Android
 * using Amazon Machine Learning.
 * 
 * Instantiate this class with an mlModelId, and then call
 * predict() method with your record.
 */
public class AndroidRealtimePrediction {
 
    // Model id
    private final String mlModelId;
      
    // Real-time endpoint for your model
    private String endpoint;
      
    // AML Client
    private AmazonMachineLearningClient client;
      
    public AndroidRealtimePrediction(String mlModelId, AWSCredentials credentials) {
        this.mlModelId = mlModelId;
        this.client = new AmazonMachineLearningClient(credentials);
        getRealtimeEndpoint();  // look up and cache the realtime endpoint for this model
    }
      
    /**
     * Calls GetMLModel. 
     * Checks if the model is completed and real-time endpoint is ready for predict calls
     */
    private void getRealtimeEndpoint() {
        GetMLModelRequest request = new GetMLModelRequest();
        request.setMLModelId(mlModelId);
        GetMLModelResult result = client.getMLModel(request);
          
        if (!result.getStatus().equals(EntityStatus.COMPLETED.toString())) {
            throw new IllegalStateException("ML model " + mlModelId + " needs to be completed.");
        }
        if (!result.getEndpointInfo().getEndpointStatus().equals(RealtimeEndpointStatus.READY.toString())) {
            throw new IllegalStateException("ML model " + mlModelId + "'s real-time endpoint is not yet ready or needs to be created.");
        }
          
        this.endpoint = result.getEndpointInfo().getEndpointUrl();
    }
      
    /**
     * Once the real-time endpoint is acquired, we can start calling predict for our model
     * Pass in a Map with attribute=value pairs.  Render numbers as strings.
     */
    public PredictResult predict(Map<String, String> record) {
        PredictRequest request = new PredictRequest();
        request.setMLModelId(mlModelId);
        request.setPredictEndpoint(endpoint);
          
        // Populate record with data relevant to the ML model
        request.setRecord(record);
        PredictResult result = client.predict(request);

        return result;
    }
      
}
