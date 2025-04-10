@echo off
setlocal enabledelayedexpansion
FOR /F "usebackq tokens=1,2* delims=" %%t in ("%CI_PROJECT_DIR%\%REPORT_DIR%\JSONTestFiles.txt") DO (
    echo "Get test data for %%t"
    python %CI_PROJECT_DIR%\pygpt\get_test_data_list.py "%CI_PROJECT_DIR%\%%t" "%CI_PROJECT_DIR%\%REPORT_DIR%" "%TEST_DATA_DIR%"
    @REM type %REPORT_DIR%\%TEST_DATA_LIST%
    echo "Download test data"
    "%CI_PROJECT_DIR%\download_test_data.bat"
    :: Run test
    echo "Running %%t"
    set CI_PROJECT_DIR=%CI_PROJECT_DIR%
    set JAVA_HOME=%JAVA_HOME%
    echo  java args: "%JAVA_OPTIONS% -cp %CLASSPATH%"
    echo %USERPROFILE%
    python "%CI_PROJECT_DIR%\pygpt\snap_gpt_test.py" "%JAVA_HOME%\bin\java.exe" "-cp %CLASSPATH%" org.esa.snap.test.TestOutput "%CI_PROJECT_DIR%\%PROPERTIES_PATH%" %SCOPE% "%CI_PROJECT_DIR%\%%t" "%CI_PROJECT_DIR%\%REPORT_DIR%\report\output" true
)
endlocal