package org.esa.snap.test;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.TrueFileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.esa.snap.dataio.netcdf.NetCdfActivator;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Properties;

public class SnapGPTTest {

    public static void main(String[] args) throws IOException {

        final String PROPERTYNAME_FAIL_ON_MISSING_DATA = "snap.gpt.tests.failOnMissingData";
        final boolean FAIL_ON_MISSING_DATA = Boolean.parseBoolean(System.getProperty(PROPERTYNAME_FAIL_ON_MISSING_DATA, "true"));


        boolean specificJSON = true;
        boolean success = true;
        //TODO check better the arguments
        if (args.length != 4) {
            System.out.println("Required arguments: [properties] [scope] [jsonPath] [reportFolder]");
            return;
        }

        Path testFolder = null;
        Path graphFolder = null;
        Path inputFolder = null;
        Path expectedOutputFolder = null;
        Path tempFolder = null;
        Path snapBinFolder = null;

        Properties properties = new Properties();

        try (FileReader in = new FileReader(args[0])) {
            properties.load(in);
        } catch (IOException e) {
            System.out.println("Unable to load property file");
            return;
        }

        if (!FAIL_ON_MISSING_DATA) {
            System.out.println("Tests will not fail if test data is missing!");
        }

        testFolder = Paths.get(properties.getProperty("testFolder"));
        graphFolder = Paths.get(properties.getProperty("graphFolder"));
        inputFolder = Paths.get(properties.getProperty("inputFolder"));
        expectedOutputFolder = Paths.get(properties.getProperty("expectedOutputFolder"));
        tempFolder = Paths.get(properties.getProperty("tempFolder"));
        snapBinFolder = Paths.get(properties.getProperty("snapBin"));

        if (testFolder == null || graphFolder == null || inputFolder == null || expectedOutputFolder == null || tempFolder == null) {
            System.out.println("Some folder is null");
            return;
        }

        String scope = args[1];
        Path jsonPath = Paths.get(args[2]);
        if (Files.notExists(jsonPath)) {
            System.out.println("JSON file does not exist: " + jsonPath.toString());
            return;
        }
        String JSONFileName = jsonPath.getFileName().toString().substring(0, jsonPath.getFileName().toString().indexOf("."));

        Path reportFolderPath = Paths.get(args[3]);


        if (Files.notExists(reportFolderPath)) {
            System.out.println("Report folder does not exist: " + reportFolderPath.toString());
            return;
        }

        boolean reportHtml = true; //todo add this option as parameter
        if (reportHtml) {
            //create html folder structure
            reportFolderPath.resolve("html").toFile().mkdir();
            reportFolderPath.resolve("html").resolve("images").toFile().mkdir();
            reportFolderPath.resolve("html").resolve("json").toFile().mkdir();
            reportFolderPath.resolve("html").resolve("icons").toFile().mkdir();
            reportFolderPath.resolve("html").resolve("css").toFile().mkdir();
            //copy icons and css
            ReportUtils.copyResource("css/gptTest.css", reportFolderPath.resolve("html").resolve("css").resolve("gptTest.css"));
            ReportUtils.copyResource("icons/blue.png", reportFolderPath.resolve("html").resolve("icons").resolve("blue.png"));
            ReportUtils.copyResource("icons/duration.png", reportFolderPath.resolve("html").resolve("icons").resolve("duration.png"));
            ReportUtils.copyResource("icons/green.png", reportFolderPath.resolve("html").resolve("icons").resolve("green.png"));
            ReportUtils.copyResource("icons/orange.png", reportFolderPath.resolve("html").resolve("icons").resolve("orange.png"));
            ReportUtils.copyResource("icons/percent.png", reportFolderPath.resolve("html").resolve("icons").resolve("percent.png"));
            ReportUtils.copyResource("icons/red.png", reportFolderPath.resolve("html").resolve("icons").resolve("red.png"));
            ReportUtils.copyResource("icons/SNAP_Icon_16.png", reportFolderPath.resolve("html").resolve("icons").resolve("SNAP_Icon_16.png"));
            ReportUtils.copyResource("icons/SNAP_Icon_32.png", reportFolderPath.resolve("html").resolve("icons").resolve("SNAP_Icon_32.png"));
            ReportUtils.copyResource("icons/SNAP_Icon_48.png", reportFolderPath.resolve("html").resolve("icons").resolve("SNAP_Icon_48.png"));
            ReportUtils.copyResource("icons/SNAP_Icon_60.png", reportFolderPath.resolve("html").resolve("icons").resolve("SNAP_Icon_60.png"));
            ReportUtils.copyResource("icons/SNAP_Icon_128.png", reportFolderPath.resolve("html").resolve("icons").resolve("SNAP_Icon_128.png"));
            ReportUtils.copyResource("icons/yellow.png", reportFolderPath.resolve("html").resolve("icons").resolve("yellow.png"));
        }

        BufferedWriter writer = null;
        boolean report = true; //todo add this option as parameter
        try {
            writer = new BufferedWriter(new FileWriter(reportFolderPath.resolve(String.format("Report_%s.txt", JSONFileName)).toFile(), false));
        } catch (IOException e) {
            System.out.println("Cannot create report file: " + reportFolderPath.resolve(String.format("Report_%s.txt", JSONFileName)).toString());
            report = false;
        }


        Collection<File> fileList = null;
        if (specificJSON) {
            fileList = new ArrayList<>();
            fileList.add(jsonPath.toFile());
        } else {
            fileList = FileUtils.listFiles(testFolder.toFile(), new WildcardFileFilter("*.json"), TrueFileFilter.INSTANCE);
        }


        SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");


        ArrayList<JsonTestResult> jsonTestResultList = new ArrayList<>();
        for (File file : fileList) { //do for every json
            JsonTestResult jsonTestResult = new JsonTestResult(org.esa.snap.core.util.io.FileUtils.getFilenameWithoutExtension(file));
            GraphTest[] graphTests = GraphTestsUtils.mapGraphTests(file);
            //ArrayList<GraphTestResult> graphTestResultList = new ArrayList<>();
            if (graphTests == null || graphTests.length == 0) {
                continue;
            }
            for (GraphTest graphTest : graphTests) { //do for every test inside a json
                if (!graphTest.inputExists(inputFolder) && !FAIL_ON_MISSING_DATA) {
                    System.out.println(graphTest.getId() + " is missing input data in input folder '" + inputFolder + "'. Skipping test.");
                    continue;
                }

                boolean hasToBeExecuted = false;
                if (scope.toLowerCase().equals("release")) {
                    if (graphTest.getFrequency().toLowerCase().contains("release") ||
                            graphTest.getFrequency().toLowerCase().contains("weekly") ||
                            graphTest.getFrequency().toLowerCase().contains("daily")) {
                        hasToBeExecuted = true;
                    }
                } else if (scope.toLowerCase().equals("weekly")) {
                    if (graphTest.getFrequency().toLowerCase().contains("weekly") ||
                            graphTest.getFrequency().toLowerCase().contains("daily")) {
                        hasToBeExecuted = true;
                    }
                } else {
                    if (graphTest.getFrequency().toLowerCase().contains(scope.toLowerCase())) {
                        hasToBeExecuted = true;
                    }
                }

                GraphTestResult testResult = new GraphTestResult(graphTest);

                if (reportHtml) {
                    //create graph png in html folder
                    Path graphPath = graphFolder.resolve(graphTest.getGraphPath());
                    Path imagePath = reportFolderPath.resolve("html").resolve("images").resolve(graphTest.getGraphPath());
                    String stringPNG = org.esa.snap.core.util.io.FileUtils.exchangeExtension(imagePath.toString(), ".png");
                    File filePNG = new File(stringPNG);
                    filePNG.getParentFile().mkdirs();
                    if (!filePNG.exists()) {
                        ReportUtils.generateGraphImage(graphPath.toFile(), filePNG);
                    }

                    //create specific json in html folder
                    ObjectMapper objectMapper = new ObjectMapper();
                    Path jsonReportPath = reportFolderPath.resolve("html").resolve("json").
                            resolve(org.esa.snap.core.util.io.FileUtils.getFilenameWithoutExtension(jsonPath.toFile()));
                    Path json = jsonReportPath.resolve(graphTest.getId() + ".json");
                    json.getParent().toFile().mkdirs();
                    objectMapper.writeValue(json.toFile(), graphTest);
                }

                if (hasToBeExecuted) {
                    Date startDate = null;
                    Date endDate = null;
                    if (report) {
                        writer.write(graphTest.getId());
                        writer.write(" - ");

                        startDate = new Date();
                        writer.write(formatter.format(startDate));
                        writer.write(" - ");
                    }

                    boolean passed = false;
                    try {
                        passed = TestExecutor.executeTest(graphTest, graphFolder, inputFolder, expectedOutputFolder, tempFolder, snapBinFolder);
                    } catch (Exception e) {
                        System.out.println(String.format("CException when executing test: %s", e.getMessage()));
                    }

                    endDate = new Date();
                    if (report) {

                        //txt basic report
                        writer.write(formatter.format(endDate));
                        writer.write(" - ");
                        if (passed) {
                            writer.write("PASSED");
                        } else {
                            writer.write("FAILED");
                            success = false;

                            //copy  output product to report
                            if (!scope.toLowerCase().equals("release") && !scope.toLowerCase().equals("weekly") && !scope.toLowerCase().equals("daily") && !scope.toLowerCase().equals("regular")) {
                                for (Output output : graphTest.getOutputs()) {
                                    Collection<File> outputFiles = FileUtils.listFilesAndDirs(tempFolder.toFile(), new WildcardFileFilter(String.format("%s*", output.getOutputName())), new WildcardFileFilter(String.format("%s*", output.getOutputName())));
                                    for (File outputFile : outputFiles) {
                                        if (outputFile.toString().equals(tempFolder.toString())) {
                                            continue;
                                        }
                                        Files.copy(outputFile.toPath(), reportFolderPath.resolve(outputFile.getName()));
                                        if (outputFile.isDirectory()) {
                                            FileUtils.copyDirectory(outputFile, reportFolderPath.resolve(outputFile.getName()).toFile());
                                        }
                                    }
                                }
                            }

                            //copy output of gpt to report (perhaps it has been copied before, so try-catch)
                            try {
                                Path reportGPT = Paths.get(tempFolder.resolve(graphTest.getId()).toString() + "_gptOutput.txt");
                                Files.copy(reportGPT, reportFolderPath.resolve(reportGPT.getFileName()));
                            } catch (Exception e) {
                                System.out.println(String.format("Cannot copy gptOutput: %s", e.getMessage()));
                            }

                            //copy output of content to report (perhaps it has been copied before, so try-catch) Do not exist anymore
                            /*try {
                                Path reportContent = Paths.get(tempFolder.resolve(graphTest.getId()).toString() + "_contentError.txt");
                                Files.copy(reportContent, reportFolderPath.resolve(reportContent.getFileName()));
                            } catch (Exception e) {
                                System.out.println(String.format("Cannot copy contentOutput: %s",e.getMessage()));
                            }*/

                        }
                        writer.write("\n");
                    }

                    if (reportHtml) {
                        testResult.setStartDate(startDate);
                        testResult.setEndDate(endDate);
                        if (passed) {
                            testResult.setStatus("PASSED");
                        } else {
                            testResult.setStatus("FAILED");
                        }
                    }
                } else {
                    testResult.setStatus("SKIPPED");
                }
                //graphTestResultList.add(testResult);
                jsonTestResult.addGraphTestResults(testResult);

            }

            jsonTestResultList.add(jsonTestResult);
            if (reportHtml) {
                //create html report with velocity
                ReportUtils.createHtmlReportForJson(jsonTestResult.getGraphTestResultArray(),
                        jsonTestResult.getJsonName(),
                        reportFolderPath.resolve("html").resolve(org.esa.snap.core.util.io.FileUtils.exchangeExtension(file.getName(), ".html")),
                        scope);
            }
        }

        if (writer != null) {
            writer.close();
        }

        if (!success) {
            System.exit(1);
        }
    }
}