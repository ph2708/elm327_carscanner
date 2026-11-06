@echo off
title Compilador AutoScan BR
color 0B
echo ========================================================
echo       COMPILANDO NOVA VERSAO DO AUTOSCAN BR
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/3] Finalizando processos anteriores...
taskkill /F /IM AutoScanBR.exe >nul 2>&1

echo [2/3] Compilando executavel nativo (PyInstaller)...
"C:\Users\admin\AppData\Local\Python\bin\python.exe" -m PyInstaller --noconfirm --onedir --windowed --name "AutoScanBR" app_windows.py

if %errorlevel% neq 0 (
    echo [ERRO] Falha na compilacao com PyInstaller!
    pause
    exit /b
)

echo.
echo [3/3] Gerando Instalador Windows Oficial (Inno Setup)...
"C:\Users\admin\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer.iss

if %errorlevel% neq 0 (
    echo [ERRO] Falha ao gerar o instalador!
    pause
    exit /b
)

echo.
echo ========================================================
echo SUCESSO! APLICACAO ATUALIZADA E PRONTA!
echo Iniciando AutoScan BR...
echo ========================================================
start "" "dist\AutoScanBR\AutoScanBR.exe"
pause

