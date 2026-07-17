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

:: Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FAIL] Python not found. Install Python 3.10+.
    pause
    exit /b 1
)

:: Install deps
echo [1] Installing Python packages...
echo      (this may take a minute on first run)
cd /d "%ROOT%python-core"
pip install -r requirements.txt 2>&1 | findstr /v "^$"
if errorlevel 1 (
    echo [FAIL] pip install failed. Check network connection.
    pause
    exit /b 1
)
echo       done

:: Build Go
echo [2] Building Go mediator...
cd /d "%ROOT%go-mediator"
if not exist "mediator.exe" (
    go build -o mediator.exe . 2>nul
    if errorlevel 1 (
        echo [FAIL] Go build failed.
        pause
        exit /b 1
    )
)
echo       done

:: Start Python
echo [3] Starting services...
cd /d "%ROOT%python-core"
start /MIN "S-Anchor-Python" python -m uvicorn server:app --host 127.0.0.1 --port %PY_PORT% --log-level warning
echo       Python engine  [port %PY_PORT%]
timeout /t 3 /nobreak >nul

:: Start Go
cd /d "%ROOT%go-mediator"
set MEDIATOR_PORT=%GO_PORT%
start /MIN "S-Anchor-Go" mediator.exe
echo       Go mediator    [port %GO_PORT%]
timeout /t 2 /nobreak >nul

:: Start Frontend
cd /d "%ROOT%frontend"
start /MIN "S-Anchor-Frontend" python -m http.server %FE_PORT% --bind 127.0.0.1
echo       Frontend       [port %FE_PORT%]
timeout /t 2 /nobreak >nul

:: Verify
echo [4] Verifying...
python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:%GO_PORT%/api/health'); print('      Go: OK')" 2>nul || echo      Go: OFFLINE
python -c "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:%PY_PORT%/api/health'); print('      Python: OK')" 2>nul || echo      Python: OFFLINE

:: Done
echo.
echo ========================================
echo  SYSTEM ONLINE
echo  Frontend:  http://127.0.0.1:%FE_PORT%
echo  Go:        http://127.0.0.1:%GO_PORT%
echo  Python:    http://127.0.0.1:%PY_PORT%
echo ========================================
echo.
start http://127.0.0.1:%FE_PORT%
echo Press any key to stop all services...
pause >nul

:: Stop
echo.
echo Stopping...
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Python" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Go" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Frontend" >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul
