@echo off
REM Runs the Smartschool sync in the background ONLY (no window) - for Windows Task Scheduler.
REM To open the app, use start_app.bat (or the .exe) - opening it never syncs by itself.

cd /d "%~dp0"
python sync.py --days-back 14 --days-ahead 30
