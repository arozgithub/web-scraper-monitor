@echo off
echo ============================================================
echo Starting Enterprise Web Scraper
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

echo [1/2] Starting API Server (Port 5001)...
start "Scraper API Server" python scraper_api.py
timeout /t 3 /nobreak > nul

echo [2/2] Starting UI Server (Port 5000)...
start "Scraper UI Server" python app.py
timeout /t 2 /nobreak > nul

echo.
echo ============================================================
echo Servers Started!
echo ============================================================
echo.
echo UI:  http://localhost:5000
echo API: http://localhost:5001
echo.
echo Press any key to check server status...
pause > nul

REM Check if servers are running
netstat -ano | findstr "5000 5001"

echo.
echo Both servers should be LISTENING above.
echo If not, check the opened windows for errors.
echo.
pause
