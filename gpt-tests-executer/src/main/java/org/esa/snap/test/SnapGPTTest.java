package org.esa.snap.test;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Properties;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;

public class SnapGPTTest {

    public static void main(String[] args) throws IOException {

        boolean specificJSON = false;
        String JSONFileName = null;

        //TODO check better the arguments
        if(args.length == 2) {
            System.out.println("Only one JSON test file will be executed.");
            specificJSON = true;
            JSONFileName = args[1];
        } else if (args.length == 1) {
            System.out.println("Every JSON test file in the testFolder defined in the property file will be executed.");
        } else {
            System.out.println("It is required one or two arguments....");//TODO explain better
            //System.out.println("The expected properties are: testFolder, graphFolder, inputFolder, expectedOutputFolder and tempFolder.");
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

        Collection<File> fileList = null;
        if(specificJSON) {
            fileList = new ArrayList<>();
            fileList.add(new File(JSONFileName));
        } else {
            fileList = FileUtils.listFiles(testFolder.toFile(), new WildcardFileFilter("*.json"), TrueFileFilter.INSTANCE);
        }
        for(File file : fileList) {
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