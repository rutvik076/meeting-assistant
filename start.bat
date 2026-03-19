@echo off
cd /d %~dp0
echo Activating environment...
call .venv\Scripts\activate
echo Starting Meeting Assistant...
python pipeline.py
pause