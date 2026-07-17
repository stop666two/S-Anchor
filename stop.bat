@echo off
chcp 65001 >nul
title S-Anchor :: Shutdown

echo.
echo  [SYS] >>> shutting down S-Anchor services...
echo.

taskkill /f /fi "WINDOWTITLE eq S-Anchor-Python" /t >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Go" /t >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Frontend" /t >nul 2>&1

taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im mediator.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq S-Anchor*" >nul 2>&1

echo  [SYS] >>> all services stopped.
timeout /t 2 /nobreak >nul
