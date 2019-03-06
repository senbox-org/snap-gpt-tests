package org.esa.snap.test;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;

public class SnapGPTTest {

    public static void main(String[] args) throws IOException {

        if (args.length != 1) {
            System.out.println("Only one argument is required indicating the path to a properties file.");
            System.out.println("The expected properties are: testFolder, graphFolder, inputFolder, expectedOutputFolder and tempFolder.");
            return;
        }

        Path testFolder = null;
        Path graphFolder= null;
        Path inputFolder = null;
        Path expectedOutputFolder = null;
        Path tempFolder = null;

        Properties properties = new Properties();

        try (FileReader in = new FileReader(args[0])){
            properties.load(in);
        } catch (IOException e) {
            System.out.println("Unable to load property file");
            return;
        }

        testFolder = Paths.get(properties.getProperty("testFolder"));
        graphFolder= Paths.get(properties.getProperty("graphFolder"));
        inputFolder = Paths.get(properties.getProperty("inputFolder"));
        expectedOutputFolder = Paths.get(properties.getProperty("expectedOutputFolder"));
        tempFolder = Paths.get(properties.getProperty("tempFolder"));


        if(testFolder == null || graphFolder == null || inputFolder == null || expectedOutputFolder == null || tempFolder == null) {
            System.out.println("Some folder is null");
            return;
        }

        for(File file : FileUtils.listFiles(testFolder.toFile(), new WildcardFileFilter("*.json"), TrueFileFilter.INSTANCE)) {
            GraphTest[] graphTests = GraphTestsUtils.mapGraphTests(file);
            if(graphTests == null || graphTests.length == 0) {
                continue;
            }
            for(GraphTest graphTest : graphTests) {
                TestExecutor.executeTest(graphTest,graphFolder,inputFolder,expectedOutputFolder,tempFolder);
            }
        }
    }
}