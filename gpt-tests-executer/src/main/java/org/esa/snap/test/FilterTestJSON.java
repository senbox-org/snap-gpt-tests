package org.esa.snap.test;

import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;

/**
 * Created by obarrile on 18/03/2019.
 */
public class FilterTestJSON {
    public static void main(String[] args) throws IOException {

        if (args.length != 3) {
            System.out.println("The expected arguments are: [testFolder] [scope] [outputFolder] ");
            return;
        }

        Path testFolder = Paths.get(args[0]);
        Path outputFolder = Paths.get(args[2]);
        String scope = args[1];

        if (testFolder == null || outputFolder == null) {
            System.out.println("Some folder is null");
            return;
        }

        if (Files.notExists(testFolder)) {
            System.out.println("Test folder does not exist");
            return;
        }

        if (Files.notExists(outputFolder)) {
            System.out.println("Output folder does not exist");
            return;
        }


        //TODO check scope valid?

        //if (GraphTestsUtils.createTestJSONListFile(testFolder, scope, outputFolder.resolve("JSONTestFiles.txt"))) {
        //    System.out.println("Filtered JSON created in " + outputFolder.resolve("JSONTestFiles.txt").toString());
        // }

        if (GraphTestsUtils.createTestJSONListFiles(testFolder, scope, outputFolder.resolve("JSONTestFiles.txt"),outputFolder.resolve("JSONTestFilesSeq.txt"))) {
            System.out.println("Filtered JSON created in " + outputFolder.resolve("JSONTestFiles.txt").toString());
            System.out.println("Seq filtered JSON created in " + outputFolder.resolve("JSONTestFilesSeq.txt").toString());
        }

        return;
    }
}