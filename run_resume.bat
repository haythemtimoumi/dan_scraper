@echo off
echo Starting Smart Resume Scraper...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the resume scraper with visible browser
python smart_resume_scraper.py --visible

echo.
echo Resume scraper finished. Press any key to exit...
pause > nul