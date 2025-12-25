@echo off
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment
    exit /b 1
)

echo Installing dependencies...
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip
    exit /b 1
)

venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    exit /b 1
)

echo Setup complete! Run 'run.bat' to start the application.

