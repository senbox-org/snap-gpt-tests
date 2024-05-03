setlocal enabledelayedexpansion
set CI_PROJECT_DIR=%CI_PROJECT_DIR%
set CI_JOB_ID=%CI_JOB_ID%
set DB_PATH=%DB_PATH%
set SCOPE=%SCOPE%
IF %CI_COMMIT_BRANCH%==master IF %SCOPE%==daily (
    ::Get next job id (only works for master)
    ::curl https://reports-api.snap-ci.ovh/api/job/last | %APPDATA%\jq.exe .ID >> %CI_PROJECT_DIR%\jobid.txt
    ::set /p JOB=<%CI_PROJECT_DIR%\jobid.txt
    ::set /a JOB=%JOB%+1
    ::echo "Saving results for job %JOB%"
    ::Update reports database
    python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% "snap:master" %SCOPE% %CI_PROJECT_DIR%\result\report %CI_JOB_ID:6,10% master
    DEL %CI_PROJECT_DIR%\jobid.txt
    echo "done"
)