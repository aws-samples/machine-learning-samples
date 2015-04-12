package com.amazonaws.samples.machinelearning

import java.io.IOException

import com.amazonaws.services.machinelearning.AmazonMachineLearningClient
import com.amazonaws.services.machinelearning.model._

import scala.collection.JavaConverters._
import scala.io.Source

object BuildModel extends App {
  val trainingDataUrl = "s3://aml-sample-data/banking.csv"
  val dataSchema = getClass.getResourceAsStream("/banking.csv.schema")
  val recipe = getClass.getResourceAsStream("/recipe.json")
  val friendlyPrefix = "Scala Marketing Sample"
  val trainPercent = 70

  val client = new AmazonMachineLearningClient

  private def createDataSource(entityId: String, entityName: String, percentBegin: Int, percentEnd: Int): Unit = {
    val dataRearrangementString = """{"splitting":{"percentBegin":""" + percentBegin + ""","percentEnd":""" + percentEnd + """}}"""
    val dataSpec = new S3DataSpec()
      .withDataLocationS3(trainingDataUrl)
      .withDataRearrangement(dataRearrangementString)
      .withDataSchema(Source.fromInputStream(dataSchema).mkString)
    val request = new CreateDataSourceFromS3Request()
      .withDataSourceId(entityId)
      .withDataSourceName(entityName)
      .withComputeStatistics(true)
      .withDataSpec(dataSpec)

    client.createDataSourceFromS3(request)
    println(s"Created DataSource $entityName with id $entityId")
  }

  /**
   * Creates an ML Model object, which begins the training process.
   * The quality of the model that the training algorithm produces depends
   * primarily on the data, but also on the hyper-parameters specified in
   * the parameters map, and the feature-processing recipe.
   * @throws IOException
   */
  private def createModel(mlModelId: String, trainDataSourceId: String): Unit = {
    val parameters = Map(
      "sgd.maxPasses" -> "100",
      "sgd.maxMLModelSizeInBytes" -> "104857600",
      "sgd.l2RegularizationAmount" -> "1e-4")
    val request = new CreateMLModelRequest()
      .withMLModelId(mlModelId)
      .withMLModelName(friendlyPrefix + " model")
      .withMLModelType(MLModelType.BINARY)
      .withParameters(parameters.asJava)
      .withRecipe(Source.fromInputStream(recipe).mkString)
      .withTrainingDataSourceId(trainDataSourceId)
    client.createMLModel(request)
    println(s"Created ML Model with id $mlModelId")
  }

  /**
   * Creates an Evaluation, which measures the quality of the ML Model
   * by seeing how many predictions it gets correct, when run on a
   * held-out sample (30%) of the original data.
   */
  private def createEvaluation(mlModelId: String): Unit = {
    val evaluationId = Identifiers.newEvaluationId
    val request = new CreateEvaluationRequest()
      .withEvaluationDataSourceId(testDataSourceId)
      .withEvaluationName(friendlyPrefix + " evaluation")
      .withMLModelId(mlModelId)
    client.createEvaluation(request)
    println(s"Created Evaluation with id $evaluationId")
  }

  val trainDataSourceId = Identifiers.newDataSourceId
  val testDataSourceId = Identifiers.newDataSourceId
  val mlModelId = Identifiers.newMLModelId

  createDataSource(trainDataSourceId, friendlyPrefix + " - training data", 0, trainPercent)
  createDataSource(testDataSourceId, friendlyPrefix + " - testing data", trainPercent, 100)
  createModel(mlModelId, trainDataSourceId)
  createEvaluation(mlModelId)
}
