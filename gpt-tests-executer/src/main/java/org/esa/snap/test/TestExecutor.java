package org.esa.snap.test;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Map;
import java.util.regex.Matcher;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import org.esa.snap.core.dataio.ProductIO;
import org.esa.snap.core.datamodel.Product;
import org.esa.snap.dataio.ContentAssert;
import org.esa.snap.dataio.ExpectedDataset;


/**
 * Created by obarrile on 20/02/2019.
 */
public class TestExecutor {
    private static String exportArgs(ArrayList<String> args) {
        String result = "";
        for (String arg : args) {
            result += "\"" + arg + "\" ";
        }
        return result;
    }

    public static boolean executeTest(GraphTest graphTest, Path graphFolder, Path inputFolder, Path expectedOutputFolder, Path tempFolder, Path snapBin, Path basePath) throws IOException {

        boolean testPassed = true;
        //prepare parameters
        ArrayList<String> params = new ArrayList<>();
        if(snapBin != null) {
            params.add(snapBin.resolve("gpt").toString());
        } else {
            params.add("gpt");
        }
        params.add(graphFolder.resolve(graphTest.getGraphPath()).toString());

        //if specific VM, configure gpt
        //set XMX in gpt.vmoption
        if(graphTest.getConfigVM() != null && graphTest.getConfigVM().getXmX() != null) {
            Files.copy(snapBin.resolve("gpt.vmoptions"), snapBin.resolve("gpt.vmoptionsORIGINAL"));
            File fileBackup = snapBin.resolve("gpt.vmoptionsORIGINAL").toFile();
            File fileVM = snapBin.resolve("gpt.vmoptions").toFile();
            String modifiedString = "";
            BufferedReader reader = null;
            FileWriter writer = null;
            try
            {
                reader = new BufferedReader(new FileReader(fileBackup));
                String line = reader.readLine();
                while (line != null)
                {
                    if(line.startsWith("-Xmx")) {
                        modifiedString = modifiedString + "-Xmx" + graphTest.getConfigVM().getXmX() + System.lineSeparator();
                    } else {
                        modifiedString = modifiedString + line + System.lineSeparator();
                    }
                    line = reader.readLine();
                }

                writer = new FileWriter(fileVM);
                writer.write(modifiedString);
            }
            catch (IOException e)
            {
                e.printStackTrace();
            }
            finally
            {
                try
                {
                    reader.close();
                    writer.close();
                }
                catch (IOException e)
                {
                    e.printStackTrace();
                }
            }
        }
        if(graphTest.getConfigVM() != null) {
            params.add("-c");
            params.add(graphTest.getConfigVM().getCacheSize());
            params.add("-q");
            params.add(graphTest.getConfigVM().getParallelism());
        }


        //inputs
        for(Map.Entry<String, String> entry : graphTest.getInputs().entrySet()) {
            String value = entry.getValue();
            value = value.replaceAll("\\$graphFolder", Matcher.quoteReplacement(graphFolder.toString()));
            value = value.replaceAll("\\$inputFolder", Matcher.quoteReplacement(inputFolder.toString()));
            value = value.replaceAll("\\$expectedOutputFolder", Matcher.quoteReplacement(expectedOutputFolder.toString()));
            value = value.replaceAll("\\$tempFolder", Matcher.quoteReplacement(tempFolder.toString()));
            params.add(String.format("-P%s=%s", entry.getKey(), inputFolder.resolve(value).toString()));
        }

        //parameters
        for(Map.Entry<String, String> entry : graphTest.getParameters().entrySet()) {
            String value = entry.getValue();
            value = value.replaceAll("\\$graphFolder", Matcher.quoteReplacement(graphFolder.toString()));
            value = value.replaceAll("\\$inputFolder", Matcher.quoteReplacement(inputFolder.toString()));
            value = value.replaceAll("\\$expectedOutputFolder", Matcher.quoteReplacement(expectedOutputFolder.toString()));
            value = value.replaceAll("\\$tempFolder", Matcher.quoteReplacement(tempFolder.toString()));
            params.add(String.format("-P%s=%s",entry.getKey(),value));
        }

        //outputs
        for(Output output : graphTest.getOutputs()) {
            String value = output.getOutputName();
            value = value.replaceAll("\\$graphFolder", Matcher.quoteReplacement(graphFolder.toString()));
            value = value.replaceAll("\\$inputFolder", Matcher.quoteReplacement(inputFolder.toString()));
            value = value.replaceAll("\\$expectedOutputFolder", Matcher.quoteReplacement(expectedOutputFolder.toString()));
            value = value.replaceAll("\\$tempFolder", Matcher.quoteReplacement(tempFolder.toString()));
            params.add(String.format("-P%s=%s",output.getParameter(), tempFolder.resolve(value).toString()));
        }
        //execute graph
        ArrayList<String> profiler = new ArrayList<String>();
        profiler.add("python3");
        profiler.add(basePath.toString()+"/profiler.py");
        profiler.add(exportArgs(params));
        profiler.add("-o");
        profiler.add(String.format("%s_perf.csv", tempFolder.resolve(graphTest.getId()).toString()));

        ProcessBuilder builder = new ProcessBuilder(profiler);
        builder.environment();

        File redirectOutputFile = new File(tempFolder.resolve(graphTest.getId()).toString() + "_gptOutput.txt");
        builder.redirectErrorStream(true);
        builder.redirectOutput(redirectOutputFile);

        builder.command();
        Process process = builder.start();
        try {

            process.waitFor(); 
        } catch (InterruptedException e) {
            e.printStackTrace();
            if(graphTest.getConfigVM() != null && graphTest.getConfigVM().getXmX() != null) {
                resetVMOptions(snapBin);
            }
            return false;
        }

        //check outputs
        for(Output output : graphTest.getOutputs()) {
            final ObjectMapper mapper = new ObjectMapper();
            boolean expectedIsDefined = true;
            if(output.getExpected() == null || output.getExpected().length() == 0) {
                expectedIsDefined = false;
            }

            String outputNameWithExtension = findOutput(output, tempFolder);
            if(outputNameWithExtension == null) {
                System.out.println("Output not found!!!");
                if(graphTest.getConfigVM() != null && graphTest.getConfigVM().getXmX() != null) {
                    resetVMOptions(snapBin);
                }
                return false;
            }

            if(expectedIsDefined) { //if expected output is not defined, then skip this step
                Product product = ProductIO.readProduct(outputNameWithExtension);
                final ExpectedDataset expectedDataset = mapper.readValue(new File(expectedOutputFolder.resolve(output.getExpected()).toString()), ExpectedDataset.class);
                if(product == null){
                    System.out.println("Cannot read output file: " + outputNameWithExtension);
                    testPassed = false;
                    break;
                }
                final ContentAssert contentAssert = new ContentAssert(expectedDataset.getExpectedContent(), output.getOutputName(), product);
                try {
                    contentAssert.assertProductContent();

                } catch (AssertionError e) {
                    System.out.println("Error in test!!!");
                    System.out.println(e.getMessage());
                    try (BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(tempFolder.resolve(graphTest.getId()).toString() + "_contentError.txt"))) {
                        bufferedWriter.write(e.getMessage());
                    } catch (IOException e2) {
                        System.out.println(e2.getMessage());
                    }
                    testPassed = false;
                }
            }
        }

        //reset VMOptions file
        if(graphTest.getConfigVM() != null && graphTest.getConfigVM().getXmX() != null) {
            resetVMOptions(snapBin);
        }
        return testPassed;
    }
    private static String findOutput (Output output, Path tempFolder) {
        Collection<File> filelist = FileUtils.listFiles(tempFolder.toFile(), new WildcardFileFilter(String.format("%s.*",output.getOutputName())), null);
        if(filelist.size() == 1) {
            File[] files = filelist.toArray(new File[filelist.size()]);
            return files[0].getAbsolutePath();
        }
        Path outPath = tempFolder.resolve(output.getOutputName());
        if(Files.exists(outPath)) {
            return outPath.toAbsolutePath().toString();
        }

        //TODO check
        return null;
    }

    private static void resetVMOptions(Path snapBin) {
        try {
            Files.copy(snapBin.resolve("gpt.vmoptionsORIGINAL"), snapBin.resolve("gpt.vmoptions"), StandardCopyOption.REPLACE_EXISTING);
            Files.deleteIfExists(snapBin.resolve("gpt.vmoptionsORIGINAL"));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
