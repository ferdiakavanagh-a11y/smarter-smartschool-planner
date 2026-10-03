@echo off
REM Background sync only, for Task Scheduler. Opening the app (start_app.bat / exe) never syncs.

cd /d "%~dp0"
python sync.py --days-back 14 --days-ahead 30
