@echo off
rem ---------------------------------------------------------------------------
rem Launch the CLL Initiative Dashboard locally.
rem
rem Run from anywhere: the script resolves its own location, so the working
rem directory is always the app folder. That matters because Config.DB_PATH can
rem be relative ("./cll_initiatives.db") and a wrong working directory would
rem point at a different - and once, an empty - database. The committed .env
rem sets DB_PATH absolutely, but this keeps the default honest too.
rem
rem Usage:
rem   run-dashboard.cmd            start on port 8000
rem   run-dashboard.cmd 8010       start on port 8010
rem   run-dashboard.cmd 8000 --reload
rem ---------------------------------------------------------------------------
setlocal

set "HERE=%~dp0"
set "APP=%HERE%"

if not exist "%APP%\app\main.py" (
  echo [run-dashboard] Cannot find the app at:
  echo     %APP%
  echo Run this script from inside the repository.
  exit /b 1
)

rem The passcode the app reads comes from .env in the app folder. It is
rem gitignored; copy .env.example to .env if it is missing.
if not exist "%APP%\.env" (
  echo [run-dashboard] No .env found in the app folder.
  echo     Copy .env.example to .env and set APP_PASSCODE and APP_SECRET:
  echo         copy "%APP%\.env.example" "%APP%\.env"
  exit /b 1
)

rem Choose an interpreter that has the dependencies. `py -3.12` is the one the
rem project is developed against; fall back to the py launcher, then PATH.
set "PY=py -3.12"
%PY% --version >nul 2>&1
if errorlevel 1 (
  set "PY=py -3"
  %PY% --version >nul 2>&1
)
if errorlevel 1 (
  set "PY=python"
  %PY% --version >nul 2>&1
)
if errorlevel 1 (
  echo [run-dashboard] No Python interpreter found. Install Python 3.12+ or
  echo     add it to PATH, then try again.
  exit /b 1
)

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

rem Free the port first. A previous run (or another uvicorn) can still hold it,
rem and on Windows the new server then dies with "only one usage of each socket
rem address". scripts/free_port.ps1 stops a stale dashboard server but refuses to
rem kill anything else on that port, so this can never take down an unrelated
rem process; if the port is foreign it prints why and we stop here.
powershell -NoProfile -ExecutionPolicy Bypass -File "%APP%\scripts\free_port.ps1" -Port %PORT%
if errorlevel 1 (
  echo [run-dashboard] Could not free port %PORT%. Not starting.
  exit /b 1
)

echo [run-dashboard] App:  %APP%
echo [run-dashboard] Python: %PY%
echo [run-dashboard] Open http://127.0.0.1:%PORT% and use the passcode in .env
echo.

cd /d "%APP%" || exit /b 1
%PY% -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% %2 %3 %4

endlocal
