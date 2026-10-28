@echo off
REM Source-folder sync for Task Scheduler; normal app startup shows cached data.

cd /d "%~dp0"
python sync.py --days-back 14 --days-ahead 30
