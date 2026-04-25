@echo off
:: ============================================================
:: Setup Script - Green Campus Alert Map
:: ENREDD Batna, Algeria
:: ============================================================

setlocal EnableDelayedExpansion

echo.
echo  +============================================+
echo  ^|  Green Campus Alert Map - ENREDD Batna    ^|
echo  ^|           Setup Script v1.0               ^|
echo  +============================================+
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python3 not found.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check MySQL
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] MySQL not found.
    echo Please install MySQL from: https://dev.mysql.com/downloads/installer/
    pause
    exit /b 1
)

echo [1/6] Creating Python virtual environment...
cd backend
python -m venv venv
call venv\Scripts\activate.bat

echo [2/6] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [3/6] Creating directories...
if not exist uploads mkdir uploads
if not exist logs mkdir logs
if not exist ml\models mkdir ml\models

echo [4/6] Setting up database...
set /p MYSQL_PASS="Enter MySQL root password: "
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p%MYSQL_PASS% < ..\database\schema.sql
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p%MYSQL_PASS% < ..\database\seed.sql
echo Database initialized!

echo [5/6] Creating .env file...
:: Generate random secret keys using Python
for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%i
for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set JWT_SECRET=%%i

(
    echo FLASK_ENV=development
    echo SECRET_KEY=!SECRET_KEY!
    echo JWT_SECRET_KEY=!JWT_SECRET!
    echo DB_USER=root
    echo DB_PASSWORD=!MYSQL_PASS!
    echo DB_HOST=localhost
    echo DB_PORT=3306
    echo DB_NAME=green_campus_db
    echo DEBUG=True
) > .env
echo .env file created!

echo [6/6] Training ML models...
python ..\backend\ml\train_model.py
echo ML models trained!

echo.
echo  Setup complete!
echo  Run: scripts\start.bat  to launch the application
echo.
pause
