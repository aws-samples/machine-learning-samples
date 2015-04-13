package com.amazonaws.samples.machinelearning

import com.amazonaws.services.machinelearning.AmazonMachineLearningClient
import com.amazonaws.services.machinelearning.model.{GetMLModelRequest, PredictRequest}

import scala.collection.JavaConverters._

/**
 * Simple command-line realtime prediction utility
 *
 * Usage:
 * java RealtimePredict mlModelId attribute1=value1 attribute2=value2 ...
 *
 * Multi-word text attributes can be specified like:
 * java RealtimePredict ml-12345678901 "textVar=Multiple words grouped together" numericVar=123
 */
object RealtimePredict extends App {

  require(args.length > 0, "First command line argument must be the mlModelId")
  val mlModelId = args(0)

  require(args.drop(1).forall(_.count(_ == '=') == 1), "Command line arguments must take form attributeName=value")
  val record = args.drop(1).map(_.split("=")).map(kv => kv(0) -> kv(1)).toMap

  private def predict(mlModelId: String, record: Map[String, String]) = {
    val client = new AmazonMachineLearningClient

    // finds the realtime endpoint for this ML Model
    val modelRequest = new GetMLModelRequest().withMLModelId(mlModelId)
    val predictEndpoint = client.getMLModel(modelRequest).getEndpointInfo.getEndpointUrl

    val predictRequest = new PredictRequest()
      .withMLModelId(mlModelId)
      .withPredictEndpoint(predictEndpoint)
      .withRecord(record.asJava)
    client.predict(predictRequest)
  }

  println("Predict result:\n" + predict(mlModelId, record))
}
