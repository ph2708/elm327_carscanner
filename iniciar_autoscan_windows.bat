@echo off
title AutoScan BR - Inicializador do Sistema
color 0A

echo ========================================================
echo               AUTOSCAN BR - DIAGNOSTICO AUTOMOTIVO
echo ========================================================
echo.
echo [1/3] Verificando dependencias...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH. Instale o Python 3.
    pause
    exit /b
)

echo [2/3] Iniciando Servidor Web Local (AutoScan Dashboard)...
start /b cmd /c "cd backend && php -S 127.0.0.1:8000 -t public"

timeout /t 2 /nobreak >nul

echo [3/3] Abrindo painel no navegador padrao...
start http://127.0.0.1:8000

echo.
echo ========================================================
echo Escolha o modo de conexao:
echo [1] Iniciar Coletor no Carro (Auto-detectar ELM327 na porta COM)
echo [2] Iniciar Simulador Virtual (Testes sem conectar no carro)
echo ========================================================
set /p opt="Opcao (1 ou 2): "

if "%opt%"=="1" (
    echo [*] Conectando ao adaptador ELM327...
    python -m collector.app.main --mode serial
) else (
    echo [*] Modo simulador ativado!
    python -m collector.app.main --mode simulator
)

pause

