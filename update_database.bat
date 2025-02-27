setlocal enabledelayedexpansion
set CI_PROJECT_DIR=%CI_PROJECT_DIR%
set CI_JOB_ID=%CI_JOB_ID%
set DB_PATH=%DB_PATH%
set SCOPE=%SCOPE%
:: compute job number for performance reports
set JOB=%CI_JOB_ID:~6,10%
IF %SCOPE%==daily (
    @REM example (command executed on Windows VM):
    @REM python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% <display_version> %SCOPE% <base_path> %JOB% <branch>
    @REM   CI_PROJECT_DIR = C:\builds\TPp69-DL\0\senbox-org\snap-gpt-tests\
    @REM   DB_PATH = mysql://<user:passwd>@mysql.snap-ci.ovh:3306/snap_reports_2024
    @REM                    (defined as variable into 'snap-gpt-tests' project from Gitlab)
    @REM   display_version = snap:9.0.8-RC2 (with this (branch or tag) name will be saved into performance database on https://reports.snap-ci.ovh/?#/branches)
    @REM                       (it always contains the prefix 'snap:')
    @REM   SCOPE = daily (or CItest for pipeline test purposes)
    @REM   base_path = %CI_PROJECT_DIR%\result\report
    @REM   JOB = 126 
    @REM   branch = 11.0.0 (with this version the results are saved into 'GPT Test Report' on https://snap-reports.s3.sbg.io.cloud.ovh.net/windows/index.html)
    @REM Update reports database
    python %CI_PROJECT_DIR%\pygpt\stats_db.py %DB_PATH% "snap:12.0.0" %SCOPE% %CI_PROJECT_DIR%\result\report %JOB% 12.0.0
    echo "done"
)