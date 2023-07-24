@echo off
FOR /F "usebackq tokens=1,2* delims=" %%x in (%REPORT_DIR%\JSONTestFiles.txt) DO (
    echo "Get test data for %%x"
    python %CI_PROJECT_DIR%\pygpt\get_test_data_list.py %%x %REPORT_DIR%
    type %REPORT_DIR%\%TEST_DATA_LIST%
    :: Download test data
    %CI_PROJECT_DIR%\download_test_data.bat
    :: Run test
    echo "Running %test%"
    python pygpt\snap_gpt_test.py java "-cp gpt-tests-executer\target\gpt-test-exec.jar" org.esa.snap.test.TestOutput %PROPERTIES_PATH% %SCOPE% %%x "%CI_PROJECT_DIR%\%REPORT_DIR%\report\output" true
)