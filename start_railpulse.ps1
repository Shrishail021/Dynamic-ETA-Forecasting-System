# RailPulse One-Click Application Launcher
# Starts both Backend API (FastAPI) and Frontend UI (Vite + React) in separate windows

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Launching RailPulse Dynamic ETA System (SIH PS 26028)..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start Backend in a new window
Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "cd '$RootPath\backend'; py -3.12 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait 2 seconds for backend to start
Start-Sleep -Seconds 2

# 2. Start Frontend in a new window
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", "cd '$RootPath\frontend'; npm.cmd run dev"

Start-Sleep -Seconds 3

# Open Default Browser
Write-Host "[*] Opening RailPulse Radar in default browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"

Write-Host "`nAll services launched successfully!" -ForegroundColor Green
Write-Host "  - Frontend UI: http://localhost:5173"
Write-Host "  - Backend API: http://localhost:8000"
Write-Host "  - Swagger Docs: http://localhost:8000/docs`n"
