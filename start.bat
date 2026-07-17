@echo off
chcp 65001 >nul
title S-Anchor :: Frequency Domain Watermark System

set ROOT=%~dp0
set PYTHON_PORT=9001
set GO_PORT=8080
set FRONTEND_PORT=8000

echo.
echo  [S-ANCHOR v1.0]  >>>  INITIALIZING SYSTEM...
echo  ============================================
echo.

:: ---- Check Python ----
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: ---- Install Python dependencies ----
echo  [PY] >>> checking dependencies...
cd /d "%ROOT%python-core"
pip install -r requirements.txt -q 2>nul
if %ERRORLEVEL% neq 0 (
    echo  [PY] >>> installing dependencies...
    pip install -r requirements.txt
)
echo  [PY] >>> dependencies OK

:: ---- Check Go mediator executable ----
echo.
echo  [GO] >>> checking mediator...
cd /d "%ROOT%go-mediator"
if not exist "mediator.exe" (
    echo  [GO] >>> building mediator.exe...
    go build -o mediator.exe .
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Go build failed. Make sure Go is installed.
        pause
        exit /b 1
    )
)
echo  [GO] >>> mediator.exe ready

:: ---- Start Python Backend ----
echo.
echo  [SYS] >>> starting Python engine on port %PYTHON_PORT%...
cd /d "%ROOT%python-core"
start "S-Anchor-Python" /B python -m uvicorn server:app --host 127.0.0.1 --port %PYTHON_PORT% --log-level warning
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Failed to start Python backend.
    pause
    exit /b 1
)
echo  [PY] >>> engine started [PID: %ERRORLEVEL%]

:: Wait for Python to be ready
timeout /t 3 /nobreak >nul

:: ---- Start Go Mediator ----
echo.
echo  [SYS] >>> starting Go mediator on port %GO_PORT%...
cd /d "%ROOT%go-mediator"
set MEDIATOR_PORT=%GO_PORT%
start "S-Anchor-Go" /B mediator.exe
echo  [GO] >>> mediator started on port %GO_PORT%

:: Wait for Go to be ready
timeout /t 1 /nobreak >nul

:: ---- Start Frontend Server ----
echo.
echo  [SYS] >>> starting frontend server on port %FRONTEND_PORT%...
cd /d "%ROOT%frontend"
start "S-Anchor-Frontend" /B python -m http.server %FRONTEND_PORT% --bind 127.0.0.1
echo  [FE] >>> frontend started on port %FRONTEND_PORT%

:: ---- Auto open browser ----
timeout /t 2 /nobreak >nul
echo.
echo  ============================================
echo   SYSTEM ONLINE
echo   Frontend:  http://127.0.0.1:%FRONTEND_PORT%
echo   Go API:    http://127.0.0.1:%GO_PORT%/api/health
echo   Python:    http://127.0.0.1:%PYTHON_PORT%/api/health
echo  ============================================
echo.
start http://127.0.0.1:%FRONTEND_PORT%

echo  [SYS] >>> All services running. Close this window to stop all.
echo.
cmd /k
