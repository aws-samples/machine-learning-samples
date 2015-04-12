package com.amazonaws.samples.machinelearning

import java.io.{BufferedReader, FileReader, IOException}

object Util {
  /**
   * Reads an entire file
   * @param filename local file to read
   * @return String with entire contents of file
   * @throws IOException
   */
  @deprecated("Simply use Source.fromInputStream(is).mkString", "1.0")
  def loadFile(filename: String): String = {
    val fr = new FileReader(filename)
    val br = new BufferedReader(fr)
    try {
      var strline = ""
      val output = new StringBuffer
      while ( {
        strline = br.readLine
        strline
      } != null) {
        output.append(strline)
      }
      output.toString
    } finally {
      br.close()
      fr.close()
    }
  }
}
