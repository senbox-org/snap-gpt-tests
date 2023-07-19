@echo off
echo "Start"
FOR /F "usebackq tokens=1,2* delims=" %%x in (%REPORT_DIR%\%TEST_DATA_LIST%) DO (
	IF NOT EXIST %TEST_DATA_DIR%\%%x (
        echo %%x|findstr /r ".xml$ .XML$ .JP2$ .zip$ .ZIP$ .tgz$ .NTF$ .dim$ .DIMA$ .h5$ .txt$ .tif$ .TIF$ .img$ .hdr$ _OC$ .N1$ .nc$ .dbf$ .prj$ .qix$ .shp$ .shx$ .qpj$"
        IF %errorlevel% == 0 (
          echo "Download file %%x"
          "C:\Program Files\Amazon\AWSCLIV2\aws.exe" s3 cp s3://%S3_BUCKET%/testData/%%x %TEST_DATA_DIR%\%%x %S3_ARGS%
        ) ELSE (
          echo "Download directory %%x"
          "C:\Program Files\Amazon\AWSCLIV2\aws.exe" s3 cp s3://%S3_BUCKET%/testData/%%x %TEST_DATA_DIR%\%%x %S3_ARGS% --recursive
        )
      ) ELSE ( echo "%%x exists: skip download" )
)