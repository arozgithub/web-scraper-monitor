@echo off
call venv\Scripts\activate
start "ScraperAPI" python scraper_api.py
python app.py
pause
