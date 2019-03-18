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

    public static boolean createTestJSONListFile (Path testFolderPath, String scope, String fileName) {

        BufferedWriter writer = null;
        boolean success = true;
        try {
            writer = new BufferedWriter(new FileWriter(fileName, true));

            for (File file : FileUtils.listFiles(testFolderPath.toFile(), new WildcardFileFilter("*.json"), TrueFileFilter.INSTANCE)) {
                GraphTest[] graphTests = null;
                try {
                    graphTests = GraphTestsUtils.mapGraphTests(file);
                } catch (IOException e) {
                    //ignore and continue with following files
                    continue;
                }

                if (graphTests == null || graphTests.length == 0) {
                    continue;
                }
                for (GraphTest graphTest : graphTests) {
                    if (graphTest.getFrequency().contains(scope)) {
                        writer.write(file.getAbsolutePath());
                        writer.write("\n");
                        continue;
                    }
                }
            }
        } catch (IOException e) {
            success = false;
        } finally {
            if(writer != null) {
                try {
                    writer.close();
                } catch (IOException e) {
                    //ignore
                }
            }
        }
        return success;
    }
}
