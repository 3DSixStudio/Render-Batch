@echo off
REM Tao shortcut "SCS Batch Render" ngoai Desktop tro toi run.bat
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\SCS Batch Render.lnk');" ^
  "$s.TargetPath='%~dp0run.bat'; $s.WorkingDirectory='%~dp0'; $s.WindowStyle=7;" ^
  "if (Test-Path '%~dp0icon.ico') { $s.IconLocation='%~dp0icon.ico' };" ^
  "$s.Save()"
echo Da tao shortcut ngoai Desktop.
pause
