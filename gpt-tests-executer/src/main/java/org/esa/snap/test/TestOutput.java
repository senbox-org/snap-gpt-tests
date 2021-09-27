package org.esa.snap.test;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;

import com.fasterxml.jackson.databind.ObjectMapper;

import org.esa.snap.core.dataio.ProductIO;
import org.esa.snap.core.datamodel.Product;
import org.esa.snap.dataio.ContentAssert;
import org.esa.snap.dataio.ExpectedDataset;

public class TestOutput {
    public static void main(String[] args) throws IOException {
        String outputNameWithExtension = args[0];
        String expectedOutput = args[1];
        String outputName = args[2];
        Product product = ProductIO.readProduct(outputNameWithExtension);
        final ObjectMapper mapper = new ObjectMapper();
        String jsonStr="";
        String OS = System.getProperty("os.name").toLowerCase();
        Charset encoding = StandardCharsets.UTF_8;
        // if((OS.indexOf("win") >= 0))
        //     encoding = StandardCharsets.ISO_8859_1;
        try (FileInputStream fis = new FileInputStream(expectedOutput);
                InputStreamReader isr = new InputStreamReader(fis, encoding);
                BufferedReader reader = new BufferedReader(isr)
        ) {
            String str;
            while ((str = reader.readLine()) != null) {
                jsonStr+=str+"\n";
            }
        
        } catch (Exception e) {
            e.printStackTrace();
        }
        final ExpectedDataset expectedDataset = mapper.readValue(jsonStr, ExpectedDataset.class);
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