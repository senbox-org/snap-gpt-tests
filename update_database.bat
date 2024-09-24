setlocal enabledelayedexpansion
set CI_PROJECT_DIR=%CI_PROJECT_DIR%
set CI_JOB_ID=%CI_JOB_ID%
set DB_PATH=%DB_PATH%
set SCOPE=%SCOPE%
set JOB=%CI_JOB_ID:~6,10%
set REPORT_DIR=%REPORT_DIR%
IF %SCOPE%==daily (
    @REM ::Get next job id (only works for master)
    @REM ::curl https://reports-api.snap-ci.ovh/api/job/last | %APPDATA%\jq.exe .ID >> %CI_PROJECT_DIR%\jobid.txt
    @REM ::set /p JOB=<%CI_PROJECT_DIR%\jobid.txt
    @REM ::set /a JOB=%JOB%+1
    @REM ::echo "Saving results for test job %JOB%"
    @REM ::Update reports database (for performance comparison)
    @REM example (command executed on Windows VM)
    @REM python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% <tag_name> %SCOPE% <base_path> %JOB% <test_branch>
    @REM   REPORT_DIR = result_snap-10
    @REM   CI_PROJECT_DIR = C:\builds\TPp69-DL\0\senbox-org\snap-gpt-tests\
    @REM   DB_PATH = mysql://<user:passwd>@mysql.snap-ci.ovh:3306/snap_reports_2024 
    @REM   tag_name = snap:9.0.8-RC2
    @REM   SCOPE = daily 
    @REM   base_path = %CI_PROJECT_DIR%\%REPORT_DIR%\report
    @REM   JOB = 126 
    @REM   test_branch = 9.0.8-reference
    python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% "snap:10.0.0" %SCOPE% %CI_PROJECT_DIR%\%REPORT_DIR%\report %JOB% "10.0.0-reference"
    @REM DEL %CI_PROJECT_DIR%\jobid.txt
    echo "done"
)