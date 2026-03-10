@echo off
setlocal
set "_out="
for /f "delims=" %%i in ('"{{TP_CLI}}" %*') do set "_out=%%i"
if errorlevel 1 exit /b %errorlevel%
if not "%_out%"=="" cd /d "%_out%"
