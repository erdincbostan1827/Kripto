@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo ERROR: Git for Windows bulunamadi. Once Git for Windows kurulmalidir.
  exit /b 1
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0IMPORT_PHASE221_EXACT_HISTORY.ps1" ^
  -BundlePath "%~dp0crypto_trading_platform_v5_1_phase220_git.bundle" ^
  -ReferencePath "%~dp0PHASE221_EXACT_REFERENCE.json" ^
  -ResultPath "%~dp0PHASE221_NATIVE_IMPORT_RESULT.json"
exit /b %ERRORLEVEL%
