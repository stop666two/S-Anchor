@echo off
chcp 65001 >nul
echo ========================================
echo   S-Anchor Project Initialization
echo ========================================
echo.

:: ---- Install git hooks ----
echo [1] Installing git hooks...
git config core.hooksPath .githooks
if %ERRORLEVEL% equ 0 (
    echo       Git hooks configured: .githooks/pre-commit
) else (
    echo [WARN] Failed to configure git hooks - run from repo root
)

:: ---- Install Python dev dependencies ----
echo [2] Installing Python dev dependencies...
cd /d "%~dp0..\python-core"
py -3 -m pip install -r requirements-dev.txt 2>&1 | findstr /v "^$"
if errorlevel 1 (
    echo [WARN] Dev dependencies install failed (optional)
) else (
    echo       Dev dependencies installed
)

echo.
echo ========================================
echo  INITIALIZATION COMPLETE
echo ========================================
echo.
pause
