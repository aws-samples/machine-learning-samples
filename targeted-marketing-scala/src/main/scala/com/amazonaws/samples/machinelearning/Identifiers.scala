package com.amazonaws.samples.machinelearning

import scala.util.Random

/**
 * Utility class to generate random identifiers with prefixes
 * that indicate which type of entity they are for.
 */
object Identifiers {
  private val BASE62_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".toCharArray

  private def base62RandomChar(): Char = BASE62_CHARS(Random.nextInt(BASE62_CHARS.length))

  private def generateEntityId(prefix: String): String = {
    val rand = List.fill(11)(base62RandomChar()).mkString
    s"$prefix-$rand"
  }

  def newDataSourceId: String = generateEntityId("ds")

  def newMLModelId: String = generateEntityId("ml")

  def newEvaluationId: String = generateEntityId("ev")

  def newBatchPredictionId: String = generateEntityId("bp")
}
