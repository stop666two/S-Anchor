@echo off
chcp 65001 >nul
title S-Anchor :: Control Panel

set ROOT=%~dp0
set PYTHON_PORT=9001
set GO_PORT=8080
set FE_PORT=8000

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║       S-ANCHOR v1.0  CONTROL PANEL       ║
echo  ║   Frequency Domain Watermark System       ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: ----- Check Python -----
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [FAIL] Python not found. Install Python 3.10+ then re-run.
    echo.
    pause
    exit /b 1
)

:: ----- Check Go -----
where go >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [WARN] Go not found. Will use pre-built mediator.exe if available.
    echo.
)

:: ----- Install Python deps -----
echo  [1/4] Installing Python dependencies...
cd /d "%ROOT%python-core"
pip install -r requirements.txt -q 2>nul
if %ERRORLEVEL% neq 0 (
    pip install -r requirements.txt
)
echo         done.

:: ----- Build Go mediator -----
echo  [2/4] Preparing Go mediator...
cd /d "%ROOT%go-mediator"
if not exist "mediator.exe" (
    go build -o mediator.exe . >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo  [FAIL] Go build failed.
        pause
        exit /b 1
    )
)
echo         done.

:: ----- Start Python backend -----
echo  [3/4] Starting services...
cd /d "%ROOT%python-core"
start "S-Anchor-Python" /MIN cmd /c "python -m uvicorn server:app --host 127.0.0.1 --port %PYTHON_PORT% --log-level warning ^& pause"
echo         Python engine     [port %PYTHON_PORT%]
timeout /t 3 /nobreak >nul

:: ----- Start Go mediator -----
cd /d "%ROOT%go-mediator"
set MEDIATOR_PORT=%GO_PORT%
start "S-Anchor-Go" /MIN cmd /c "mediator.exe ^& pause"
echo         Go mediator       [port %GO_PORT%]
timeout /t 2 /nobreak >nul

:: ----- Start frontend -----
cd /d "%ROOT%frontend"
start "S-Anchor-Frontend" /MIN cmd /c "python -m http.server %FE_PORT% --bind 127.0.0.1 ^& pause"
echo         Frontend server   [port %FE_PORT%]
timeout /t 2 /nobreak >nul

:: ----- Verify -----
echo.
echo  [4/4] Verifying services...
cd /d "%ROOT%"
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:%GO_PORT%/api/health'); print('         Go mediator:      ONLINE')" 2>nul || echo         Go mediator:      OFFLINE
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:%PYTHON_PORT%/api/health'); print('         Python engine:    ONLINE')" 2>nul || echo         Python engine:    OFFLINE

:: ----- Open browser -----
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║  SYSTEM ONLINE                            ║
echo  ║                                           ║
echo  ║  Frontend   http://127.0.0.1:%FE_PORT%    ║
echo  ║  Go API     http://127.0.0.1:%GO_PORT%    ║
echo  ║  Python     http://127.0.0.1:%PYTHON_PORT% ║
echo  ║                                           ║
echo  ║  Close this window to keep services running║
echo  ╚═══════════════════════════════════════════╝
echo.
start http://127.0.0.1:%FE_PORT%
echo.
echo  Press any key to stop all services...
pause >nul

:: ----- Shutdown -----
echo.
echo  Stopping services...
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Python" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Go" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Frontend" >nul 2>&1
echo  All services stopped.
timeout /t 2 /nobreak >nul
