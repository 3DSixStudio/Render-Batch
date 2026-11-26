@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  SCS BATCH RENDER - ban dong lenh (khong can UI)
REM  Dung chung file scs_render_core.py voi app.
REM ============================================================
cd /d "%~dp0"

set "CORE=%~dp0scs_render_core.py"
if not exist "%CORE%" (
    echo LOI: thieu file scs_render_core.py canh file bat nay.
    pause
    exit /b 1
)

set "BLENDER_EXE=C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
if not exist "!BLENDER_EXE!" (
    for /d %%D in ("C:\Program Files\Blender Foundation\Blender*") do (
        if exist "%%D\blender.exe" set "BLENDER_EXE=%%D\blender.exe"
    )
)
if not exist "!BLENDER_EXE!" (
    echo Khong tu tim thay blender.exe.
    set /p "BLENDER_EXE=Nhap duong dan day du toi blender.exe: "
    set "BLENDER_EXE=!BLENDER_EXE:"=!"
)
if not exist "!BLENDER_EXE!" (
    echo LOI: khong tim thay blender.exe
    pause
    exit /b 1
)
echo Blender: !BLENDER_EXE!

set "BLEND_FILE="
set /p "BLEND_FILE=Keo tha hoac nhap duong dan file .blend: "
if not defined BLEND_FILE goto :no_blend
set "BLEND_FILE=!BLEND_FILE:"=!"
if not exist "!BLEND_FILE!" goto :no_blend

set "OUTPUT_DIR="
set /p "OUTPUT_DIR=Nhap thu muc luu anh: "
if not defined OUTPUT_DIR (
    echo LOI: chua nhap thu muc output.
    pause
    exit /b 1
)
set "OUTPUT_DIR=!OUTPUT_DIR:"=!"
if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"

set "GPU_FLAG="
set /p "USE_GPU=Ep dung GPU? (Y/N): "
if /i "!USE_GPU!"=="Y" set "GPU_FLAG=--gpu"

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
"!BLENDER_EXE!" --background "!BLEND_FILE!" --python "%CORE%" --python-exit-code 1 -- --output "!OUTPUT_DIR!" !GPU_FLAG!
set "RC=!errorlevel!"

echo ============================================
if "!RC!"=="0" (echo   XONG! Kiem tra anh trong thu muc output.) else (echo   KET THUC VOI LOI ^(code !RC!^) - xem log phia tren.)
echo ============================================
pause
exit /b !RC!

:no_blend
echo LOI: khong tim thay file .blend: "!BLEND_FILE!"
pause
exit /b 1
