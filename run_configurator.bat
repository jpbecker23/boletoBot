@echo off
setlocal
cd /d %~dp0

echo ==========================================
echo    BoletoBot - Inicializador Automatico
echo ==========================================

:: Verifica se o venv existe, se nao existir, cria e instala tudo
if not exist "venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Iniciando configuracao...
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python nao encontrado! 
        echo Por favor, instale o Python em python.org e marque 'Add to PATH'.
        pause
        exit /b
    )
    
    echo [1/3] Criando ambiente virtual...
    python -m venv venv
    
    echo [2/3] Instalando bibliotecas (aguarde...)
    .\venv\Scripts\python.exe -m pip install --upgrade pip >nul
    .\venv\Scripts\pip.exe install -r requirements.txt
    
    echo [3/3] Instalando dependencias do navegador...
    .\venv\Scripts\python.exe -m playwright install chromium
    
    echo Tudo pronto!
    cls
)

echo Abrindo Configurador...
.\venv\Scripts\python.exe configurator.py

if errorlevel 1 (
    echo.
    echo [AVISO] O configurador foi fechado ou ocorreu um erro.
    pause
)

endlocal
