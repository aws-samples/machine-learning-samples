//
//  ViewController.m
//  ObjectiveCSample
//
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
//

#import "ViewController.h"

#import "AWSMachineLearning.h"

@interface ViewController ()

@end

// Cache real-time endpoint
NSString *endpoint;

// Amazon Machine Learning Client
AWSMachineLearning *machineLearning;

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    
    machineLearning = [AWSMachineLearning defaultMachineLearning];
    
    // Specify your ML Model
    NSString *MLModelId = @"YOUR-ML-MODEL-ID";
    
    AWSMachineLearningGetMLModelInput *getMLModelInput = [AWSMachineLearningGetMLModelInput new];
    getMLModelInput.MLModelId = MLModelId;
    
    // Call Get ML Model
    [[[machineLearning getMLModel:getMLModelInput] continueWithSuccessBlock:^id(AWSTask *task) {
        AWSMachineLearningGetMLModelOutput *getMLModelOutput = task.result;
        
        if (getMLModelOutput.status != AWSMachineLearningEntityStatusCompleted) {
            NSLog(@"ML Model is not completed");
            return nil;
        }
        if (getMLModelOutput.endpointInfo.endpointStatus != AWSMachineLearningRealtimeEndpointStatusReady) {
            NSLog(@"Real-time endpoint is not ready");
            return nil;
        }
        endpoint = getMLModelOutput.endpointInfo.endpointUrl;
        
        // Since model is complete and real-time endpoint is ready, call predict
        return [self predict:MLModelId withRecord: @{}];

    }] continueWithBlock:^id(AWSTask *task) {
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

- (AWSTask *) predict:(NSString *)mlModelId withRecord:(NSDictionary *)record {
    AWSMachineLearningPredictInput *predictInput = [AWSMachineLearningPredictInput new];
    predictInput.predictEndpoint = endpoint;
    predictInput.MLModelId = mlModelId;
    predictInput.record = record;
    return [machineLearning predict:predictInput];
    
}

- (void)didReceiveMemoryWarning {
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}

@end
