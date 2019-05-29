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

    public static boolean createTestJSONListFile (Path testFolderPath, String scope, Path outputPath) {

        BufferedWriter writer = null;
        boolean success = true;
        try {
            writer = new BufferedWriter(new FileWriter(outputPath.toFile(), false));

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
                    if(scope.toLowerCase().equals("release")) {
                        if (graphTest.getFrequency().toLowerCase().contains("release") ||
                                graphTest.getFrequency().toLowerCase().contains("weekly") ||
                                graphTest.getFrequency().toLowerCase().contains("daily")) {
                            writer.write(file.getPath());
                            writer.write("\n");
                            break; //Once the file is included in the list, it is not needed to continue
                        }
                    } else if (scope.toLowerCase().equals("weekly")) {
                        if (graphTest.getFrequency().toLowerCase().contains("weekly") ||
                                graphTest.getFrequency().toLowerCase().contains("daily")) {
                            writer.write(file.getPath());
                            writer.write("\n");
                            break; //Once the file is included in the list, it is not needed to continue
                        }
                    } else {
                        if (graphTest.getFrequency().toLowerCase().contains(scope.toLowerCase())) {
                            writer.write(file.getPath());
                            writer.write("\n");
                            break; //Once the file is included in the list, it is not needed to continue
                        }
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

    public static void createTestSummary (Path testFolderPath, Path outputPath) {
        BufferedWriter writer = null;
        try {
            writer = new BufferedWriter(new FileWriter(outputPath.toFile(), false));

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
                    writer.write(graphTest.getId());
                    writer.write(";");
                    writer.write(graphTest.getDescription());
                    writer.write(";");
                    writer.write(graphTest.getFrequency());
                    writer.write(";");
                    writer.write(graphTest.getGraphPath());
                    writer.write(";");
                    writer.write(graphTest.getInputs().values().iterator().next());
                    writer.write(";");
                    writer.write(graphTest.getAuthor());
                    writer.write(";");
                    writer.write(graphTest.getDate());
                    writer.write("\n");
                }
            }
        } catch (IOException e) {
        } finally {
            if(writer != null) {
                try {
                    writer.close();
                } catch (IOException e) {
                    //ignore
                }
            }
        }
    }

}
