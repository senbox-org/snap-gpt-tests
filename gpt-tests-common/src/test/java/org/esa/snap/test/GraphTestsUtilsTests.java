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

    }

    @Test
    public void testCreateTestJSONListFile() throws Exception {

        Assert.assertTrue(GraphTestsUtils.createTestJSONListFile(Paths.get("D:/GPTTests/snap-gpt-tests/gpt-tests-resources/tests"), "DAILY", Paths.get("d:/borrar/listOfTests.txt")));

    }
}
