@echo off
echo Starting Stock Data Scraper...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the main scraper
python run_all_in_one.py

echo.
echo Scraper finished. Press any key to exit...
pause > nul