@echo off
REM ===== SCS Batch Render - khoi dong app =====
cd /d "%~dp0"

set "PY="
set "PYW="
where py >nul 2>nul && (set "PY=py -3" & set "PYW=pyw -3")
if not defined PY (
    where python >nul 2>nul && (set "PY=python" & set "PYW=pythonw")
)
if not defined PY (
    echo Khong tim thay Python tren may.
    echo Hay cai Python 3.10+ tai https://www.python.org/downloads/  ^(nho tick "Add python.exe to PATH"^)
    pause
    exit /b 1
)

%PY% -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo Lan dau chay: dang cai PySide6, vui long doi...
    %PY% -m pip install --user -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Cai PySide6 that bai. Kiem tra mang roi chay lai.
        pause
        exit /b 1
    )
)

start "" %PYW% "%~dp0scs_batch_render_app.py"
exit /b 0
