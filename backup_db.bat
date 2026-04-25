@echo off
setlocal

:: ==============================
:: Database Backup Script
:: ==============================

set "BACKUP_DIR=.\backups"
set "DB_NAME=green_campus_db"
set "MYSQLDUMP_EXE=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"

:: Generate safe timestamp
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "TIMESTAMP=%%i"

set "BACKUP_FILE=%BACKUP_DIR%\backup_%TIMESTAMP%.sql"
set "ZIP_FILE=%BACKUP_DIR%\backup_%TIMESTAMP%.zip"

:: Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo Creating backup: %BACKUP_FILE%

:: Prompt for MySQL root password
set /p MYSQL_PASS="Enter MySQL root password: "

:: Run mysqldump
"%MYSQLDUMP_EXE%" -u root -p%MYSQL_PASS% %DB_NAME% > "%BACKUP_FILE%"

if %errorlevel% neq 0 (
    echo [ERROR] Backup failed! Check your MySQL credentials and database name.
    pause
    exit /b 1
)

:: Compress using PowerShell
echo Compressing backup...
powershell -Command "Compress-Archive -Path '%BACKUP_FILE%' -DestinationPath '%ZIP_FILE%' -Force"

if %errorlevel% neq 0 (
    echo [ERROR] Compression failed!
    pause
    exit /b 1
)

del "%BACKUP_FILE%"
echo Backup saved: %ZIP_FILE%

:: Keep only last 10 backups
echo Cleaning old backups...
set /a COUNT=0
for /f "delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\*.zip" 2^>nul') do (
    set /a COUNT+=1
    if !COUNT! gtr 10 (
        del "%BACKUP_DIR%\%%F"
        echo Deleted old backup: %%F
    )
)

echo Old backups cleaned.
echo Done!
pause