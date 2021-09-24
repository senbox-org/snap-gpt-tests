package org.esa.snap.test;

import java.io.File;
import java.io.IOException;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.esa.snap.core.dataio.ProductIO;
import org.esa.snap.core.datamodel.Product;
import org.esa.snap.dataio.ContentAssert;
import org.esa.snap.dataio.ExpectedDataset;

public class TestOutput {
    public static void main(String[] args) throws IOException {
        System.setProperty("file.encoding","UTF-8");
        if (args.length != 3) {
            System.out.println("OUTPUT_PATH EXPECTED_OUTPUT_PATH OUTPUT_NAME");
            System.exit(1);
        }
        String outputNameWithExtension = args[0];
        String expectedOutput = args[1];
        String outputName = args[2];
        Product product = ProductIO.readProduct(outputNameWithExtension);
        final ObjectMapper mapper = new ObjectMapper();
        final ExpectedDataset expectedDataset = mapper.readValue(new File(expectedOutput), ExpectedDataset.class);
        if(product == null){
            System.out.println("Cannot read output file: " + outputNameWithExtension);
            System.exit(1);
        }
        final ContentAssert contentAssert = new ContentAssert(expectedDataset.getExpectedContent(), outputName, product);
        try {
            contentAssert.assertProductContent();
        } catch (AssertionError e) {
            System.out.println("\n\n---------------------------------------------------------------------\n\n");
            System.out.println("Error when comparing expected output:\n");
            System.out.println(e.getMessage());
            System.exit(1);
        }
        System.exit(0);
    }
}