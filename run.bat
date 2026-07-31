@echo off
REM Run the AI Workflow Waste Detector Streamlit app.
setlocal
cd /d "%~dp0"

REM Prefer a local virtual environment if one exists.
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo Checking dependencies...
"%PYTHON%" -m streamlit --version >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    "%PYTHON%" -m pip install -r requirements.txt
)

echo Starting AI Workflow Waste Detector...
"%PYTHON%" -m streamlit run app.py

endlocal
