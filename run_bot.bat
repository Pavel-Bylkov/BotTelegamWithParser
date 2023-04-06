@echo off
set executable=.\venv\Scripts\python.exe

:begin
start "bot_process" /w "%executable%" bot.py
timeout /t 3 /nobreak >nul
goto :begin