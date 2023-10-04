#! /bin/bash

if [[ $# -ne 6 ]]; then
    echo "Illegal number of parameters: ${#}"
    echo "prepare.sh REPORT_DIR TEST_DATA_DIR TEST_DATA_FILE S3_BUCKET S3_ARGS CI_PROJECT_DIR"
    exit 2
fi

REPORT_DIR=$1
TEST_DATA_DIR=$2
TEST_DATA_FILE=$3
S3_BUCKET=$4
S3_ARGS=$5
CI_PROJECT_DIR=$6

while IFS="" read -r test || [ -n "$test" ]
do
    echo "Start get test data for ${test}"
    python3 pygpt/get_test_data_list.py "${test}" "${REPORT_DIR}"
    cat "${REPORT_DIR}/${TEST_DATA_LIST}"
    # Download test data
    download_test_data.sh "${REPORT_DIR}" "${TEST_DATA_DIR}" "${TEST_DATA_LIST}" "${S3_BUCKET}" "${S3_ARGS}"

    echo "Running ${test}"
    python3 pygpt/snap_gpt_test.py "${JAVA_HOME}/bin/java" "${JAVA_OPTIONS} -cp gpt-tests-executer/target/gpt-test-exec.jar" \
        org.esa.snap.test.TestOutput "${PROPERTIES_PATH}" ${SCOPE} ${test} ${REPORT_DIR}/report/output true --profiling off
done < ${REPORT_DIR}/JSONTestFiles.txt
