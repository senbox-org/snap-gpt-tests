# snap-gpt-tests
GPT tests that will be included in the SNAP testing platform.


## How To Use SNAP-GPT-TESTS

If you are interested to run the GPT tests locally first you needs the following:

 - The test data
 - SNAP
 - JDK and Maven
 - python3, python3-lxml, python3-psutils, python3-matplotlib
 - Clone the repo: https://github.com/senbox-org/snap-gpt-tests

Once you have all the requirements you are ready to start.

### 0. Building the project

The first step of the testing procedure is to build the java testing utility used to compare the results of the tests with the expected one.

To build the utility we use maven from inside the cloned repository:
```
mvn clean package install
```

### 1. Filtering the Tests (optional)

If you know which JSON file tests exactly this step is optional, it only needed if you want to test all the tests that have a specific `TEST_SCOPE`.

The second step of the testing procedure (as with the previous java version) is to filters which tests you want to run using the variable `TEST_SCOPE`. To do so use the `script pygpt/filter_json.py`:

```
python3 pygpt/filter_json.py gpt-tests-resources/tests TEST_SCOPE OUTPUT_DIR
```

This will filter the json containing at least a test with the given `TEST_SCOPE`. The `OUTPUT_DIR` is the directory where the results of the tests will be stored.

The filtering will generate two files (`OUTPUT_DIR/JSONTestFiles.txt` and `OUTPUT_DIR/JSONTestFilesSeq.txt`), the first containing the tests that does not have any JavaVM special configuration and the second one containing special configuration (extra cache...).

### 2. Running the Tests

First create the report directory:

```
mkdir OUTPUT_DIR/report # create the report dir
mkdir OUTPUT_DIR/report/output
```

Then run the run the following command for each JSON file you want to test:
```
python3 pygpt/snap_gpt_test.py JAVA_BIN_PATH 'JAVA_OPTIONS -cp gpt-test-executer/target/TestOutput.jar' org.esa.snap.test.TestOutput GPT_TEST_EXECUTOR_PROPERTIES_PATH TEST_SCOPE JSON_FILE_TO_TEST OUTPUT_DIR/report/output false
```

The parameters are the following:

 - JAVA_BIN_PATH is the path to the java executable (e.g. `/usr/bin/java` or simply `java` if you are using the system version), it will be used to run the TestOutput jar
 - JAVA_OPTIONS are the options to java that will be used to lunch the TestOutput jar (on the test server we use: `-Dncsa.hdf.hdflib.HDFLibrary.hdflib=.../libjhdf.so -Dncsa.hdf.hdf5lib.H5.hdf5lib=.../libjhdf5.so`)
 - GPT_TEST_EXECUTOR_PROPERTIES_PATH is the path to the properties file containing:
 ```
    testFolder=./gpt-tests-resources/tests
    graphFolder=./gpt-tests-resources/graphs
    inputFolder=/data/ssd/testData/
    expectedOutputFolder=./gpt-tests-resources/expectedOutputs
    tempFolder=/home/snap/tmpDir
    snapBin=/home/snap/snap/bin
    TEST_SCOPE is the same as in the previous step
    JSON_FILE_TO_TEST is the JSON file you are currently testing.
 ```

### 3. Report generation (optional)

If you want to generate the HTML report for the tests you have performed first you need to copy the static resources (CSS and icons) and move the previous results in a sub directory:

```
cp -R pygpt/statics OUTPUT_DIR/report/statics
```

Then run the report_utils script:
```
python3 pygpt/report_utils.py pygpt/templates OUTPUT_DIR/report TEST_SCOPE VERSION_NAME
```

Finish!