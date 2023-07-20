@echo off
echo "Start"
FOR /F "usebackq tokens=1,2* delims=" %%x in (%REPORT_DIR%\%TEST_DATA_LIST%) DO (
	IF NOT EXIST %TEST_DATA_DIR%\%%x (
        echo "Download directory %%x"
        "C:\Program Files\Amazon\AWSCLIV2\aws.exe" s3 cp s3://%S3_BUCKET%/testData/%%x %TEST_DATA_DIR%\%%x %S3_ARGS% --recursive
    ) ELSE ( echo "%%x exists: skip download" )
)