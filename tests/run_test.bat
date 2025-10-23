@echo off
REM Run the interactive test as a Python module to handle imports correctly
cd /d "%~dp0"
python -m pytest test_interactive_search.py %*
