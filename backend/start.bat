@echo off
setlocal
cd /d "%~dp0"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    echo %%A | findstr /b "#" >nul
    if errorlevel 1 if not "%%A"=="" set "%%A=%%B"
  )
)
if "%APP_HOST%"=="" set "APP_HOST=127.0.0.1"
if "%APP_PORT%"=="" set "APP_PORT=8000"
if exist ".venv\Scripts\activate.bat" (
  call .venv\Scripts\activate.bat
) else if exist "..\.venv\Scripts\activate.bat" (
  call ..\.venv\Scripts\activate.bat
) else (
  echo Python virtual environment not found.
  exit /b 1
)
python -m uvicorn app.main:app --reload --host %APP_HOST% --port %APP_PORT%
