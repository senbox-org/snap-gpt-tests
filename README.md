# snap-gpt-tests

GPT test platform, it contains both the gpt tests that will be executed on the jenkins test platform then all the utilities needed to perfrom the tests, compare the results and produce the reports.

The utilities are mostly written in Python3 a part for the output comparator that use the internal java code. 

The main functionality of the test utilities are:

- to filter the test using a `test scope`
- to execute `gpt` with the given parameters and profile the performance of the execution
- to compare the output with an expected output
- to test failing conditions both for the `gpt` process than for the expected output
- to generate HTML report containing all the important informations (results, logs and performances)
- to keep track of the evolution of the performances using an sql database

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
python3 pygpt/snap_gpt_test.py JAVA_BIN_PATH 'JAVA_OPTIONS -cp gpt-test-executer/target/gpt-test-exec.jar' GPT_TEST_EXECUTOR_PROPERTIES_PATH TEST_SCOPE JSON_FILE_TO_TEST OUTPUT_DIR/report/output false
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


### 3. Performance Database support (Optional)

If you want to monitor the evolution of the performance of your project the profiler is able to store the information inside a sqlite data base (and mysql in the future). To do this simply run the script `stat_db.py`:

```
python3 pygpt/stat_db.py DB_PATH SNAP_VERSION TEST_SCOPE OUTPUT_DIR/report JOB_ID BRANCH
``` 

The script will automatically fill and update the database with all the information produced by the profiler

### 4. Report generation (optional)

If you want to generate the HTML report for the tests you have performed first you need to copy the static resources (CSS and icons) and move the previous results in a sub directory:

```
cp -R pygpt/statics/* OUTPUT_DIR/report/
```

Then run the report_utils script:
```
python3 pygpt/report_utils.py pygpt/templates OUTPUT_DIR/report TEST_SCOPE VERSION_NAME (DB_PATH)
```

The `DB_PATH` is optional, but if it is provided the report_utils.py will add to the performance report of each tests the historical average values and the trend of `CPU_TIME` and `AVERAGE_MEMORY`.

## JSON Test structure

Tests are grouped in test sets defined in the same json file as following:

```json5
[//list of tests
    {
        "id": "TEST_UNIQUE_ID",// the test will fail if the same test id is found in multiple tests
        "author": "AUTHOR OF THE TEST",// this is the test author (e.g. BC, CS, CS-RO, SW...)
        "description": "A BRIEF BUT CLEAR DESCRIPTION OF THE TEST", 
        "frequency": "FREQ_TAG1/FREQ_TAG2/...", // list of frequency tags used to filters the test during executions
        "graphPath": "TEST_GRAPH_PATH.xml", // the path to the graph to test 
        "inputs": { // list of inputs
            "INPUT_NAME_1": "INPUT_PRODUCT_PATH_1",//input name and path to be used in the test
            "INPUT_NAME_2": "INPUT_PRODUCT_PATH_2"// more inputs...
        },
        "parameters": {// list of parameters
            "PARAMETER_NAME_1": "PARAMETER_VALUE",// parameter name and value to be used in the test
            "PARAMETER_NAME_2": "PARAMETER_VALUE"// more paramters...
        },
        "outputs": [ // list of output generated by the graph
            { // An output object
                "parameter": "PARAMETER_NAME", // paramter name
                "outputName": "OUTPUT_PRODUCT_NAME",
                "expected": "EXPECTED_OUTPUT_PATH"// OPTIONAL, expected output to compare the resulted output
            }// More outputs if needed
        ],
        "result": { // OPTIONAL
            "status": false, // expected result of the test (true: succeded, false: failed)
            "source": "process|expected", // source of the error  (process: gpt, expected: expected output)
            "message": "EXPECTED_ERROR_MESSAGE"// expected error message generated by gpt or output comparision
        },
        "configVM": { // OPTIONAL
            "xmx": "NG", // Ammount of memory allowed (5G = 5Gb)
            "cacheSize": "N", // Size of the cache allowed
            "parallelism": "N"// max number of   
        },
        "seed": 12345, // OPTIONAL RANDOM SEED VALUE
    }, 
    {
        // another test
    } //...
]
```

The optional parts can be skipped safely.  
The inputs, parameters and outputs will be passed to gpt as `-Pparam_name=param_value`.

## Giltlab runner

### Test data

Test data should have been uploaded to S3 bucket.
A [Confluence page](https://senbox.atlassian.net/wiki/spaces/SENBOX/pages/2490433537/S3+bucket) indicates how to
connect.
Access to confluence and the S3 Bucket is restricted to team members.

The root path of test data in the bucket should be:

`s3://<BUCKET_NAME>/runner/project/43939974/testData`