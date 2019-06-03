package org.esa.snap.test;

import org.junit.Assert;
import org.junit.Test;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Created by obarrile on 15/03/2019.
 */
public class GraphTestsUtilsTests {

    @Test
    public void testMapGraphTests() throws Exception {

        GraphTest[] graphTests =  GraphTestsUtils.mapGraphTests (new File(getClass().getResource("exampleTest.json").getFile()));
        Assert.assertEquals(graphTests.length,2);

        GraphTest[] graphOptionsTests =  GraphTestsUtils.mapGraphTests (new File(getClass().getResource("exampleWithVMconfig.json").getFile()));
        Assert.assertTrue(graphOptionsTests[0].getAuthor().contentEquals("CS"));
        Assert.assertTrue(graphOptionsTests[1].getAuthor() == null);

        Assert.assertTrue(graphOptionsTests[0].getConfigVM() == null);

        String expectedXmx = "5G";
        String expectedCacheSize = "107374824M";
        String expectedParallelism = "4";
        Assert.assertTrue(graphOptionsTests[1].getConfigVM().getXmX().contentEquals(expectedXmx));
        Assert.assertTrue(graphOptionsTests[1].getConfigVM().getCacheSize().contentEquals(expectedCacheSize));
        Assert.assertTrue(graphOptionsTests[1].getConfigVM().getParallelism().contentEquals(expectedParallelism));

    }

    @Test
    public void testCreateTestJSONListFile() throws Exception {

        Assert.assertTrue(GraphTestsUtils.createTestJSONListFile(Paths.get("D:/GPTTests/snap-gpt-tests/gpt-tests-resources/tests"), "DAILY", Paths.get("d:/borrar/listOfTests.txt")));

    }

    @Test
    public void testCreateTestJSONListFiles() throws Exception {
        Assert.assertTrue(GraphTestsUtils.createTestJSONListFiles(Paths.get("D:/GPTTests/snap-gpt-tests/gpt-tests-resources/tests"), "regular", Paths.get("d:/borrar/listOfTests.txt"), Paths.get("d:/borrar/listOfTestsSeq.txt")));
    }
}
