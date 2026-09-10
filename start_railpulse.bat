@echo off
title RailPulse Dynamic ETA Launcher
echo ============================================================
echo  Starting RailPulse Dynamic ETA Forecasting Engine...
echo ============================================================

start "RailPulse Backend (FastAPI)" powershell -ExecutionPolicy Bypass -NoExit -Command "cd '%~dp0backend'; py -3.12 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul
start "RailPulse Frontend (Vite)" powershell -ExecutionPolicy Bypass -NoExit -Command "cd '%~dp0frontend'; npm.cmd run dev"
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Application launched!
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000
echo.
