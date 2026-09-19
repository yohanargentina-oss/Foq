@echo off
setlocal
echo =====================================================================
echo ⚡ Foq 8B Reflex : serveur de decision rapide (modele de reference Foq 8B)
echo 🎯 Port dedie : http://127.0.0.1:8090
echo 🧠 Optionnel : adaptateur LoRA decision via la variable LORA_PATH
echo =====================================================================

if "%PORT%"=="" set "PORT=8090"
set "MODEL_PATH=%USERPROFILE%\.models\foq\foq-reflex-8b-pq2_0.gguf"
if not exist "%MODEL_PATH%" (
    echo [ERREUR] Modele introuvable : %MODEL_PATH%
    pause
    exit /b 1
)

:: Trouver llama-server.exe (PATH ou dossier local)
set "LLAMA_EXE="
where.exe llama-server.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "LLAMA_EXE=llama-server.exe"
) else if exist "%USERPROFILE%\.local\bin\foq-llama\llama-server.exe" (
    set "LLAMA_EXE=%USERPROFILE%\.local\bin\foq-llama\llama-server.exe"
)

if "%LLAMA_EXE%"=="" (
    echo [ERREUR] llama-server.exe introuvable dans le PATH ou .local\bin\foq-llama.
    pause
    exit /b 1
)

set "LORA_ARGS="
if defined LORA_PATH (
    if exist "%LORA_PATH%" (
        echo [*] Adaptateur LoRA actif : %LORA_PATH%
        set "LORA_ARGS=--lora "%LORA_PATH%""
    ) else (
        echo [!] LORA_PATH defini mais introuvable : %LORA_PATH% — demarrage sans adaptateur.
    )
)

echo [*] Lancement de llama-server avec : %MODEL_PATH% sur le port %PORT%...
%LLAMA_EXE% -m "%MODEL_PATH%" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on --port %PORT% --host 127.0.0.1 --alias foq-8b %LORA_ARGS%
