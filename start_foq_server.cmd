@echo off
setlocal
echo =====================================================================
echo ⚡ Foq Engine : System 1 Decision Model (Foq 8B Ternary PQ2_0)
echo 🚀 Moteur : build llama.cpp Foq (PQ2_0) -- RTX 4080 Super
echo 🎯 Port dédié : http://127.0.0.1:8089
echo 🧠 Mode : décision instantanée (0 token texte)
echo =====================================================================

if "%PORT%"=="" set "PORT=8089"
if "%MODEL_PATH%"=="" (
    if exist "%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf" (
        set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf"
    ) else if exist ".\models\foq-reflex-8b-pq2_0.gguf" (
        set "MODEL_PATH=.\models\foq-reflex-8b-pq2_0.gguf"
    ) else (
        set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf"
    )
)

:: Trouver llama-server.exe : variable LLAMA_EXE, puis build Foq, puis PATH.
:: La build Foq est prioritaire sur le PATH : le format PQ2_0 du modèle
:: est illisible par un llama.cpp officiel (PATH ou installateur LOCALAPPDATA).
set "LLAMA_CANDIDAT=%LLAMA_EXE%"
if "%LLAMA_CANDIDAT%"=="" (
    if exist "%USERPROFILE%\.local\bin\foq-llama\llama-server.exe" (
        set "LLAMA_CANDIDAT=%USERPROFILE%\.local\bin\foq-llama\llama-server.exe"
    )
)
if "%LLAMA_CANDIDAT%"=="" (
    where.exe llama-server.exe >nul 2>&1
    if not errorlevel 1 set "LLAMA_CANDIDAT=llama-server.exe"
)
set "LLAMA_EXE=%LLAMA_CANDIDAT%"

if "%LLAMA_EXE%"=="" (
    echo [ERREUR] llama-server introuvable — LLAMA_EXE, .local\bin\foq-llama, PATH.
    echo Le modele Foq utilise le format PQ2_0 : il faut la build llama.cpp Foq
    echo https://github.com/yohanargentina-oss/Foq/releases
    echo Un llama.cpp officiel ne peut pas charger ce modele.
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
