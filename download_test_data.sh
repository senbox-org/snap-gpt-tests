#! /bin/bash

if [[ $# -ne 5 ]]; then
    echo "Illegal number of parameters: ${#}"
    echo "download_test_data.sh REPORT_DIR TEST_DATA_DIR TEST_DATA_FILE S3_BUCKET S3_ARGS"
    exit 2
fi

REPORT_DIR=$1
TEST_DATA_DIR=$2
TEST_DATA_FILE=$3
S3_BUCKET=$4
S3_ARGS=$5

while IFS="" read -r line || [ -n "$line" ]
do
    echo "Download directory ${line}"
    /usr/local/bin/aws s3 cp "s3://${S3_BUCKET}/testData/${line}" "${TEST_DATA_DIR}/${line}" --recursive $S3_ARGS
    ls "${TEST_DATA_DIR}/${line}"
    # Create empty DATASTRIP folder needed by GPT tests
    mkdir -p "${TEST_DATA_DIR}/${line}/DATASTRIP"
done < "${REPORT_DIR}/${TEST_DATA_FILE}"
