@echo off
REM ===== SCS Batch Render - app launcher =====
cd /d "%~dp0"

set "PY="
set "PYW="
where py >nul 2>nul && (set "PY=py -3" & set "PYW=pyw -3")
if not defined PY (
    where python >nul 2>nul && (set "PY=python" & set "PYW=pythonw")
)
if not defined PY (
    echo Python was not found on this computer.
    echo Please install Python 3.10+ from https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^)
    pause
    exit /b 1
)

%PY% -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo First run: installing PySide6, please wait...
    %PY% -m pip install --user -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Installing PySide6 failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

start "" %PYW% "%~dp0scs_batch_render_app.py"
exit /b 0
