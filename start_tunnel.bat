@echo off
echo ====================================================
echo   Scraper API Tunnel for n8n Cloud
echo ====================================================
echo.
echo This will create a public URL for your local API
echo so n8n Cloud can access it.
echo.
echo Step 1: Make sure scraper_api.py is running
echo Step 2: Run this script to start the tunnel
echo.
echo ====================================================
echo.

REM Check if ngrok exists
if exist "C:\ngrok\ngrok.exe" (
    echo [OK] ngrok found!
    echo.
    echo Starting tunnel on port 5001...
    echo.
    echo After tunnel starts:
    echo   1. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
    echo   2. Update your n8n workflow URL
    echo   3. Keep this window open!
    echo.
    echo ====================================================
    echo.
    cd C:\ngrok
    ngrok http 5001
) else (
    echo [ERROR] ngrok not found!
    echo.
    echo Please install ngrok first:
    echo   1. Download from: https://ngrok.com/download
    echo   2. Extract to C:\ngrok\
    echo   3. Sign up at: https://dashboard.ngrok.com/signup
    echo   4. Get your authtoken: https://dashboard.ngrok.com/get-started/your-authtoken
    echo   5. Run: cd C:\ngrok
    echo   6. Run: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
)
