package org.esa.snap.test;

import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;

/**
 * Created by obarrile on 18/03/2019.
 */
public class FilterTestJSON {
    public static void main(String[] args) throws IOException {

        if (args.length != 2) {
            System.out.println("Only one argument is required indicating the path to a properties file.");
            System.out.println("The expected properties are: testFolder, graphFolder, inputFolder, expectedOutputFolder and tempFolder.");
            return;
        }

        Path testFolder = null;
        Path tempFolder = null;
        Properties properties = new Properties();

        try (FileReader in = new FileReader(args[0])) {
            properties.load(in);
        } catch (IOException e) {
            System.out.println("Unable to load property file");
            return;
        }


        testFolder = Paths.get(properties.getProperty("testFolder"));
        tempFolder = Paths.get(properties.getProperty("tempFolder"));


        if (testFolder == null || tempFolder == null) {
            System.out.println("Some folder is null");
            return;
        }

        String scope = args[1];
        //TODO check scope

        if (GraphTestsUtils.createTestJSONListFile(testFolder, scope, tempFolder.resolve("JSONTestFiles.txt"))) {
            System.out.println("Filtered JSON created in " + tempFolder.resolve("JSONTestFiles.txt").toString());
        }
        return;
    }
}
