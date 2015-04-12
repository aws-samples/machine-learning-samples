package com.amazonaws.samples.machinelearning

import java.util.Date

import com.amazonaws.services.machinelearning.AmazonMachineLearningClient
import com.amazonaws.services.machinelearning.model._

import scala.concurrent.duration._
import scala.io.Source

/**
 * This object demonstrates using a model built by
 * {@link com.amazonaws.samples.machinelearning.BuildModel}
 * to make batch predictions.
 *
 * command-line arguments:
 * mlModelid scoreThreshhold s3://url-where-output-should-go
 */
object UserModel extends App {
  val unscoredDataUrl = "s3://aml-sample-data/banking-batch.csv"
  val dataSchema = getClass.getResourceAsStream("/banking-batch.csv.schema")

  require(args.length == 3, "command-line arguments: mlModelid scoreThreshhold s3://url-where-output-should-go")
  val mlModelId = args(0)
  val threshold = args(1).toFloat
  val s3OutputUrl = args(2)

  val client = new AmazonMachineLearningClient

  /**
   * waits for the model to reach a terminal state.
   */
  private def waitForModel(mlModelId: String, delay: FiniteDuration = 2.seconds): Unit = {
    var terminated = false
    while (!terminated) {
      val request = new GetMLModelRequest().withMLModelId(mlModelId)
      val model = client.getMLModel(request)
      println(s"Model $mlModelId is ${model.getStatus} at ${new Date()}")

      model.getStatus match {
        case "COMPLETED" | "FAILED" | "INVALID" => terminated = true
      }

      try if (!terminated) Thread.sleep(delay.toMillis)
      catch {
        case e: InterruptedException =>
          e.printStackTrace()
          terminated = true
      }
    }
  }

  /**
   * Sets the score threshold on the ML Model.
   * This configures the ML Model by picking what raw prediction score
   * is the cut-off between a positive & a negative prediction.
   */
  private def setThreshold(mlModelId: String, threshold: Float): Unit = {
    val request = new UpdateMLModelRequest().withMLModelId(mlModelId).withScoreThreshold(threshold)
    client.updateMLModel(request)
  }

  private def createBatchPrediction(mlModelId: String, s3OutputUrl: String): Unit = {
    val dataSourceId = Identifiers.newDataSourceId
    val dataSpec = new S3DataSpec()
      .withDataSchema(Source.fromInputStream(dataSchema).mkString)
      .withDataLocationS3(s3OutputUrl)
    val dsRequest = new CreateDataSourceFromS3Request()
      .withDataSourceId(dataSourceId)
      .withDataSourceName("DataSource for batch prediction")
      .withDataSpec(dataSpec)
      .withComputeStatistics(false)
    client.createDataSourceFromS3(dsRequest)
    println(s"Created DataSource for batch prediction with id $dataSourceId")

    val batchPredictionId = Identifiers.newBatchPredictionId
    val bpRequest = new CreateBatchPredictionRequest()
      .withBatchPredictionId(batchPredictionId)
      .withBatchPredictionName("Scala sample Batch Prediction")
      .withMLModelId(mlModelId)
      .withOutputUri(s3OutputUrl)
      .withBatchPredictionDataSourceId(dataSourceId)
    client.createBatchPrediction(bpRequest)
    println(s"Created BatchPrediction with id $batchPredictionId")
  }

  waitForModel(mlModelId)
  setThreshold(mlModelId, threshold)
  createBatchPrediction(mlModelId, s3OutputUrl)
}
