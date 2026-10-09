@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -c "import sys; print(sys.executable)" >nul 2>nul
  if errorlevel 1 (
    echo Existing .venv cannot run. This usually means the folder was moved.
    echo Rename or remove only this disposable .venv folder, then run this file again.
    pause
    exit /b 1
  )
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo Python 3.11+ was not found. Install Python from python.org and select "Add Python to PATH".
      pause
      exit /b 1
    )
    python -m venv .venv
  )
)
if not exist .venv\Scripts\python.exe (echo Virtual environment creation failed.& pause& exit /b 1)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (echo Setup failed.& pause& exit /b 1)
echo Setup completed. Run run_windows.bat.
pause
