@echo off
echo ============================================
echo   Green Campus Alert Map - Setup
echo   ENSEREDD - Batna, Algeria
echo ============================================

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed!
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r backend\requirements.txt

echo Creating directories...
mkdir backend\uploads 2>nul
mkdir backend\ml_models 2>nul
mkdir logs 2>nul

echo Initializing database...
cd backend
python -c "from database import init_db; init_db()"

echo Training ML models...
python ml_module.py
cd ..

echo ============================================
echo   Setup Complete!
echo   Run: scripts\start.bat
echo ============================================
pause