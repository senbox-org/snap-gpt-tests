setlocal enabledelayedexpansion
REM Retrieve (from Nexus) MD5 checksum of SNAP installer executable file and set into variable
SET "localReturnValue=FALSE"
FOR /F "usebackq tokens=*" %%a IN (`curl "%NEXUS_URL%/%SNAP_INSTALLER_EXE%.md5"`) do (
    SET "SNAP_INSTALLER_MD5=%%a"
)
echo SNAP_INSTALLER_MD5 = %SNAP_INSTALLER_MD5%
REM Compute MD5 checksum of downloaded SNAP installer executable
FOR /F "usebackq skip=1 eol=C tokens=1" %%a IN (`certutil -hashfile "%DL_DIR%\%SNAP_INSTALLER_EXE%" MD5`) do (
    SET "LOCAL_MD5=%%a"
)
echo LOCAL_MD5 = %LOCAL_MD5%
IF /I NOT %SNAP_INSTALLER_MD5%==%LOCAL_MD5% (
    echo "MD5 checksum error - downloaded file 'SNAP installer' (%SNAP_INSTALLER_EXE%) is corrupt."
    echo "ERROR - exit from job / pipeline !"
    SET "localReturnValue=TRUE"
) ELSE (
    echo "MD5 checksum ok - downloaded file 'SNAP installer' (%SNAP_INSTALLER_EXE%) is ok."
    endlocal
    SET "localReturnValue=TRUE"
) 
endlocal & SET "md5RetVal=%localReturnValue%"