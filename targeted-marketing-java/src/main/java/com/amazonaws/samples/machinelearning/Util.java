package com.amazonaws.samples.machinelearning;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class Util {

    /**
     * Reads an entire file
     * @param filename local file to read
     * @return String with entire contents of file
     * @throws IOException 
     */
    static String loadFile(String filename) throws IOException {
        FileReader fr = new FileReader(filename);
        BufferedReader br = new BufferedReader(fr);
        try {
            String strline;
            StringBuffer output = new StringBuffer();
            while((strline=br.readLine())!=null)
            {
                output.append(strline);
            }
            return output.toString();
        } finally {
            br.close();
            fr.close();
        }
    }

}
