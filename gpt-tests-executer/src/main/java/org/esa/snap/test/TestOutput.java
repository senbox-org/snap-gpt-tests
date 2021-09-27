package org.esa.snap.test;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

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
        String str="";
        try (FileInputStream fis = new FileInputStream(expectedOutput);
                InputStreamReader isr = new InputStreamReader(fis, StandardCharsets.UTF_8);
                BufferedReader reader = new BufferedReader(isr)
        ) {
            
            while ((str = reader.readLine()) != null) {
                str+=str+"\n";
            }
        
        } catch (IOException e) {
            e.printStackTrace();
        }
        final ExpectedDataset expectedDataset = mapper.readValue(str, ExpectedDataset.class);
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