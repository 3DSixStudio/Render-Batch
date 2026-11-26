@echo off
REM Creates a "SCS Batch Render" shortcut on the Desktop pointing to run.bat
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\SCS Batch Render.lnk');" ^
  "$s.TargetPath='%~dp0run.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7;" ^
  "if (Test-Path '%~dp0icon.ico') { $s.IconLocation='%~dp0icon.ico' };" ^
  "$s.Save()"
echo Desktop shortcut created.
pause
