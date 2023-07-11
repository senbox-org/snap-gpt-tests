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
    if [ ! -a "${TEST_DATA_DIR}/${line}" ] && [ ! -d "${TEST_DATA_DIR}/${line}" ]; then
        if [[ "${line}" =~ (.xml|.XML|.JP2|.zip|.ZIP|.tgz|.NTF|.dim|.DIMA|.h5|.txt|.tif|_OC|.N1)$ ]]; then
            echo "Download file ${line}"
            aws s3 cp "s3://${S3_BUCKET}/testData/${line}" "${TEST_DATA_DIR}/${line}" $S3_ARGS
        else
            echo "Download directory ${line}"
            aws s3 cp "s3://${S3_BUCKET}/testData/${line}" "${TEST_DATA_DIR}/${line}" $S3_ARGS --recursive
        fi
    else
        echo "${line} exists: skip download"
    fi
done < "${REPORT_DIR}/${TEST_DATA_FILE}"
