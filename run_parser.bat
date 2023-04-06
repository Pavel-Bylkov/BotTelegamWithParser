@echo off
set executable=.\venv\Scripts\python.exe

:begin
start "parser_process" /w "%executable%" parser.py
timeout /t 3 /nobreak >nul
goto :begin