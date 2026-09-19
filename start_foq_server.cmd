@echo off
setlocal
echo =====================================================================
echo ⚡ Foq Engine : System 1 Decision Model (Foq 27B Ternary)
echo 🚀 Moteur : llama.cpp 12.4 -- RTX 4080 Super
echo 🎯 Port dédié : http://127.0.0.1:8089
echo 🧠 Mode : décision instantanée (0 token texte)
echo =====================================================================

if "%PORT%"=="" set "PORT=8089"
if "%MODEL_PATH%"=="" (
    if exist "%USERPROFILE%\.models\foq\foq-juge-27b.gguf" (
        set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-juge-27b.gguf"
    ) else if exist "%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf" (
        set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf"
    ) else if exist ".\models\foq-juge-27b.gguf" (
        set "MODEL_PATH=.\models\foq-juge-27b.gguf"
    ) else (
        set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-juge-27b.gguf"
    )
)

:: Trouver llama-server.exe (PATH ou dossier local)
set "LLAMA_EXE="
where.exe llama-server.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "LLAMA_EXE=llama-server.exe"
) else if exist "%USERPROFILE%\.local\bin\foq-llama\llama-server.exe" (
    set "LLAMA_EXE=%USERPROFILE%\.local\bin\foq-llama\llama-server.exe"
) else if exist "%LOCALAPPDATA%\Programs\llama.cpp\llama-server.exe" (
    set "LLAMA_EXE=%LOCALAPPDATA%\Programs\llama.cpp\llama-server.exe"
)

if "%LLAMA_EXE%"=="" (
    echo [ERREUR] llama-server.exe introuvable dans le PATH ou dans .local\bin\foq-llama.
    echo Installez llama.cpp ou specifiez le chemin via la variable LLAMA_EXE.
    pause
    exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo [ERREUR] Fichier modele introuvable : %MODEL_PATH%
    echo Telechargez le modele GGUF et definissez la variable MODEL_PATH si necessaire.
    pause
    exit /b 1
)

echo [*] Lancement de llama-server avec : %MODEL_PATH% sur le port %PORT%...
"%LLAMA_EXE%" -m "%MODEL_PATH%" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on --port %PORT% --host 127.0.0.1 --alias foq --alias foq-system1
