package org.esa.snap.test;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Properties;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.apache.commons.lang.time.DateUtils;

public class SnapGPTTest {

    public static void main(String[] args) throws IOException {

        boolean specificJSON = true;
        //TODO check better the arguments
        if(args.length != 4) {
            System.out.println("Required arguments: [properties] [scope] [jsonPath] [reportFolder]");
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

        String scope = args[1];
        Path jsonPath = Paths.get(args[2]);
        if (Files.notExists(jsonPath)) {
            System.out.println("JSON file does not exist: " + jsonPath.toString());
            return;
        }
        String JSONFileName = jsonPath.getFileName().toString().substring(0,jsonPath.getFileName().toString().indexOf("."));

        Path reportFolderPath = Paths.get(args[3]);


        if (Files.notExists(reportFolderPath)) {
            System.out.println("Report folder does not exist: " + reportFolderPath.toString());
            return;
        }

        BufferedWriter writer = null;
        boolean report = true;
        try {
            writer = new BufferedWriter(new FileWriter(reportFolderPath.resolve(String.format("Report_%s.txt", JSONFileName)).toFile(), false));
        } catch (IOException e) {
            System.out.println("Cannot create report file: " + reportFolderPath.resolve(String.format("Report_%s.txt", JSONFileName)).toString());
            report = false;
        }


        Collection<File> fileList = null;
        if(specificJSON) {
            fileList = new ArrayList<>();
            fileList.add(jsonPath.toFile());
        } else {
            fileList = FileUtils.listFiles(testFolder.toFile(), new WildcardFileFilter("*.json"), TrueFileFilter.INSTANCE);
        }


        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");

        for(File file : fileList) {
            GraphTest[] graphTests = GraphTestsUtils.mapGraphTests(file);
            if(graphTests == null || graphTests.length == 0) {
                continue;
            }
            for(GraphTest graphTest : graphTests) {
                if (graphTest.getFrequency().toLowerCase().contains(scope.toLowerCase())) {
                    if(report) {
                        writer.write(graphTest.getId());
                        writer.write(" - ");

                        Date date = new Date();
                        writer.write(formatter.format(date));
                        writer.write(" - ");
                    }
                    boolean passed = TestExecutor.executeTest(graphTest,graphFolder,inputFolder,expectedOutputFolder,tempFolder);
                    if(report) {
                        Date date = new Date();
                        writer.write(formatter.format(date));
                        writer.write(" - ");
                        if(passed) {
                            writer.write("PASSED");
                        } else {
                            writer.write("FAILED");
                        }
                        writer.write("\n");
                    }
                }
            }
        }

        if(writer != null) {
            writer.close();
        }
    }
}