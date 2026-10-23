@echo off
cd /d "%~dp0"
python run.py
if errorlevel 1 (
  echo.
  echo JASS LifeOS stopped with an error. Read the traceback above.
  pause
)
