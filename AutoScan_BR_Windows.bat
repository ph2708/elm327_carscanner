@echo off
title AutoScan BR - Aplicativo Nativo Windows
color 0B

echo ========================================================
echo         AUTOSCAN BR - DESKTOP EDITION (WINDOWS)
echo ========================================================
echo.
echo Iniciando aplicativo nativo...

set PATH=C:\Users\admin\AppData\Local\Python\bin;%PATH%
python app_windows.py

if %errorlevel% neq 0 (
    pause
)

