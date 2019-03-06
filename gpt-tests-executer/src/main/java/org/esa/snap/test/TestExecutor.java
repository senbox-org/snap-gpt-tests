package org.esa.snap.test;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;


/**
 * Created by obarrile on 20/02/2019.
 */
public class TestExecutor {
    public static boolean executeTest(GraphTest graphTest, Path graphFolder, Path inputFolder, Path expectedOutputFolder, Path tempFolder) throws IOException {

        //prepare parameters
        ArrayList<String> params = new ArrayList<>();
        params.add("gpt");
        params.add(graphFolder.resolve(graphTest.getGraphPath()).toString());

        //inputs
        for(Map.Entry<String, String> entry : graphTest.getInputs().entrySet()) {
            params.add(String.format("-P%s=%s", entry.getKey(), inputFolder.resolve(entry.getValue()).toString()));
        }

        //parameters
        for(Map.Entry<String, String> entry : graphTest.getParameters().entrySet()) {
            params.add(String.format("-P%s=%s",entry.getKey(),entry.getValue()));
        }

        //outputs
        for(Output output : graphTest.getOutputs()) {
            params.add(String.format("-P%s=%s",output.getParameter(), tempFolder.resolve(output.getOutputName()).toString()));
        }

        //execute graph
        ProcessBuilder builder = new ProcessBuilder(params);

        Map<String, String> environ = builder.environment();
        builder.inheritIO();
        List<String> command = builder.command();
        Process process = builder.start();
        try {
            process.waitFor();
        } catch (InterruptedException e) {
            e.printStackTrace();
            return false;
        }

        //todo check outputs
        //final ContentAssert contentAssert = new ContentAssert(expectedContent, productId, product);
        //contentAssert.assertProductContent();

        return true;
    }
}
