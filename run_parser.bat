@echo off
set executable=.\venv\Scripts\python.exe

:begin
start "" /w "%executable%" parser.py
timeout /t 3 /nobreak >nul
goto :begin