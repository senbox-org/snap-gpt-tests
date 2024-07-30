setlocal enabledelayedexpansion
set CI_PROJECT_DIR=%CI_PROJECT_DIR%
set CI_JOB_ID=%CI_JOB_ID%
set DB_PATH=%DB_PATH%
set SCOPE=%SCOPE%
set JOB=%CI_JOB_ID:~6,10%
IF %SCOPE%==daily (
    @REM ::Get next job id (only works for master)
    @REM ::curl https://reports-api.snap-ci.ovh/api/job/last | %APPDATA%\jq.exe .ID >> %CI_PROJECT_DIR%\jobid.txt
    @REM ::set /p JOB=<%CI_PROJECT_DIR%\jobid.txt
    @REM ::set /a JOB=%JOB%+1
    @REM ::echo "Saving results for job %JOB%"
    @REM ::Update reports database
    python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% "snap:11.0.0" %SCOPE% %CI_PROJECT_DIR%\result\report %JOB% "11.0.0"
    @REM DEL %CI_PROJECT_DIR%\jobid.txt
    echo "done"
)
