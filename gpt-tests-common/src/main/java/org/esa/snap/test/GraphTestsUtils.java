package org.esa.snap.test;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;

/**
 * Created by obarrile on 06/03/2019.
 */
public class GraphTestsUtils {

    public static GraphTest[] mapGraphTests (File file) throws IOException {
        if(!file.toString().endsWith(".json")) {
            return null;
        }
        byte[] jsonData = Files.readAllBytes(file.toPath());
        //create ObjectMapper instance
        ObjectMapper objectMapper = new ObjectMapper();
        //convert json string to object
        return objectMapper.readValue(jsonData, GraphTest[].class);
    }

}
