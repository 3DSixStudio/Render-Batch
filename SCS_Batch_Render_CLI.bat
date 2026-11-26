@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM  SCS BATCH RENDER - command line version (no UI)
REM  Uses the same scs_render_core.py as the app.
REM ============================================================
cd /d "%~dp0"

set "CORE=%~dp0scs_render_core.py"
if not exist "%CORE%" (
    echo ERROR: scs_render_core.py is missing next to this .bat file.
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
    echo blender.exe was not found automatically.
    set /p "BLENDER_EXE=Full path to blender.exe: "
    set "BLENDER_EXE=!BLENDER_EXE:"=!"
)
if not exist "!BLENDER_EXE!" (
    echo ERROR: blender.exe not found
    pause
    exit /b 1
)
echo Blender: !BLENDER_EXE!

set "BLEND_FILE="
set /p "BLEND_FILE=Drag and drop or type the .blend path: "
if not defined BLEND_FILE goto :no_blend
set "BLEND_FILE=!BLEND_FILE:"=!"
if not exist "!BLEND_FILE!" goto :no_blend

set "OUTPUT_DIR="
set /p "OUTPUT_DIR=Output folder for images: "
if not defined OUTPUT_DIR (
    echo ERROR: no output folder given.
    pause
    exit /b 1
)
set "OUTPUT_DIR=!OUTPUT_DIR:"=!"
if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"

set "GPU_FLAG="
set /p "USE_GPU=Force GPU rendering? (Y/N): "
if /i "!USE_GPU!"=="Y" set "GPU_FLAG=--gpu"

set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
"!BLENDER_EXE!" --background "!BLEND_FILE!" --python "%CORE%" --python-exit-code 1 -- --output "!OUTPUT_DIR!" !GPU_FLAG!
set "RC=!errorlevel!"

echo ============================================
if "!RC!"=="0" (echo   DONE! Check the images in the output folder.) else (echo   FINISHED WITH ERRORS ^(code !RC!^) - see the log above.)
echo ============================================
pause
exit /b !RC!

:no_blend
echo ERROR: .blend file not found: "!BLEND_FILE!"
pause
exit /b 1
