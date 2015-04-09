// Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// 
// Licensed under the Amazon Software License (the "License").
// You may not use this file except in compliance with the License.
// A copy of the License is located at
// 
//  http://aws.amazon.com/asl/
// 
// or in the "license" file accompanying this file. This file is distributed
// on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express
// or implied. See the License for the specific language governing permissions
// and limitations under the License.

- (void)viewDidLoad {
    [super viewDidLoad];
    
    AWSMachineLearning *MachineLearning = [AWSMachineLearning defaultMachineLearning];
    
    NSString *MLModelId = @"ml-DONRnkB55jJ";
    
    AWSMachineLearningGetMLModelInput *getMLModelInput = [AWSMachineLearningGetMLModelInput new];
    getMLModelInput.MLModelId = MLModelId;
    
    
    [[[MachineLearning getMLModel:getMLModelInput] continueWithSuccessBlock:^id(BFTask *task) {
        AWSMachineLearningGetMLModelOutput *getMLModelOutput = task.result;
        
        if (getMLModelOutput.status != AWSMachineLearningEntityStatusCompleted) {
            NSLog(@"ML Model is not completed");
            return nil;
        }
        if (getMLModelOutput.endpointInfo.endpointStatus != AWSMachineLearningRealtimeEndpointStatusReady) {
            NSLog(@"Realtime endpoint is not ready");
            return nil;
        }
        
        AWSMachineLearningPredictInput *predictInput = [AWSMachineLearningPredictInput new];
        predictInput.predictEndpoint = getMLModelOutput.endpointInfo.endpointUrl;
        predictInput.MLModelId = MLModelId;
        predictInput.record = @{};
        
        return [MachineLearning predict:predictInput];
    }] continueWithBlock:^id(BFTask *task) {
        if (task.error) {
            NSLog(@"Error %@", task.error);
        }
        if (task.exception) {
            NSLog(@"Exception %@", task.exception);
        }
        if (task.result) {
            AWSMachineLearningPredictOutput *predictOutput = task.result;
            NSLog(@"Prediction: %@", predictOutput.prediction);
        }
        return nil;
    }];
}
