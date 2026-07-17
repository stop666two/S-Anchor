@echo off
chcp 65001 >nul
title S-Anchor Control Panel

set ROOT=%~dp0
set PY_PORT=9001
set GO_PORT=8080
set FE_PORT=8000

echo.
echo ========================================
echo   S-ANCHOR v1.0
echo   Frequency Domain Watermark System
echo ========================================
echo.

:: ---- Kill orphaned processes ----
echo [0] Cleaning up previous instances...
taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im mediator.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-*" >nul 2>&1
echo       done
timeout /t 1 /nobreak >nul

:: ---- Check Python ----
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python not found. Install Python 3.10+.
    pause
    exit /b 1
)

:: ---- Install deps ----
echo [1] Installing Python packages...
echo      (this may take a minute on first run)
cd /d "%ROOT%python-core"
pip install -r requirements.txt 2>&1 | findstr /v "^$"
if errorlevel 1 (
    echo [FAIL] pip install failed.
    pause
    exit /b 1
)
echo       done

:: ---- Build Go ----
echo [2] Building Go mediator...
cd /d "%ROOT%go-mediator"
if exist "mediator.exe" del /f "mediator.exe" >nul 2>&1
go build -o mediator.exe . 2>&1
if errorlevel 1 (
    echo [FAIL] Go build failed. Install Go from https://go.dev/dl/
    pause
    exit /b 1
)
echo       done

:: ---- Start Python backend ----
echo [3] Starting services...
start "S-Anchor-Python" /MIN /D "%ROOT%python-core" python -m uvicorn server:app --host 127.0.0.1 --port %PY_PORT% --log-level warning
echo       Python engine   [port %PY_PORT%]
timeout /t 4 /nobreak >nul

:: ---- Start Go mediator ----
set MEDIATOR_PORT=%GO_PORT%
start "S-Anchor-Go" /MIN /D "%ROOT%go-mediator" mediator.exe
echo       Go mediator     [port %GO_PORT%]
timeout /t 2 /nobreak >nul

:: ---- Start Frontend ----
start "S-Anchor-Frontend" /MIN /D "%ROOT%frontend" python -m http.server %FE_PORT% --bind 127.0.0.1
echo       Frontend        [port %FE_PORT%]
timeout /t 3 /nobreak >nul

:: ---- Verify ----
echo [4] Verifying...
cd /d "%ROOT%"
python "%ROOT%python-core\check_services.py"

:: ---- Done ----
echo.
echo ========================================
echo  SYSTEM ONLINE
echo  Frontend:  http://127.0.0.1:%FE_PORT%
echo  Go:        http://127.0.0.1:%GO_PORT%
echo  Python:    http://127.0.0.1:%PY_PORT%
echo ========================================
echo.
timeout /t 1 /nobreak >nul
start http://127.0.0.1:%FE_PORT%
echo.
echo Press any key to stop all services...
pause >nul

:: ---- Shutdown ----
echo.
echo Stopping...
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Python" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Go" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Frontend" >nul 2>&1
taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im mediator.exe >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul
