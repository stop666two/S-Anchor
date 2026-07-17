@echo off
chcp 65001 >nul
title S-Anchor :: Shutdown

echo.
echo  Shutting down S-Anchor services...
echo.

taskkill /f /fi "WINDOWTITLE eq S-Anchor-Python"  >nul 2>&1 && echo  [OK] Python engine stopped   || echo  [--] Python engine not found
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Go"      >nul 2>&1 && echo  [OK] Go mediator stopped      || echo  [--] Go mediator not found
taskkill /f /fi "WINDOWTITLE eq S-Anchor-Frontend" >nul 2>&1 && echo  [OK] Frontend server stopped   || echo  [--] Frontend server not found

taskkill /f /im uvicorn.exe >nul 2>&1
taskkill /f /im mediator.exe >nul 2>&1

echo.
echo  Done.
timeout /t 2 /nobreak >nul
