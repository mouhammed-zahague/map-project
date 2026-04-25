@echo off
:: ============================================================
:: Start Script - Green Campus Alert Map
:: ============================================================

setlocal

echo.
echo  Starting Green Campus Alert Map...
echo.

:: Check if MySQL service is running and start it if not
sc query MySQL >nul 2>&1
if %errorlevel% equ 0 (
    sc start MySQL >nul 2>&1
) else (
    :: Try common MySQL service names
    net start MySQL80 >nul 2>&1
    if %errorlevel% neq 0 (
        net start MySQL >nul 2>&1
    )
)

:: Activate venv and start Flask
cd backend

if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo  Starting Flask backend on port 5000...
set FLASK_APP=app.py
set FLASK_ENV=development

:: Start Flask in the same window
echo.
echo  Application running!
echo  Backend:   http://localhost:5000
echo  Frontend:  http://localhost:5000
echo.
echo  Press Ctrl+C to stop...
echo.

python app.py

pause
