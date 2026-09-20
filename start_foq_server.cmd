@echo off
setlocal
echo =====================================================================
echo ⚡ Foq Engine : System 1 Decision Model (Foq 8B Ternary PQ2_0)
echo 🚀 Runtime : Foq llama.cpp (PQ2_0 kernels)
echo 🎯 Port    : http://127.0.0.1:8089
echo 🧠 Mode    : Instant typed decision (0 tokens generated)
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

:: Locate llama-server.exe: LLAMA_EXE var, then Foq build in ~/.local/bin/foq-llama, then PATH.
:: The Foq build is prioritized over PATH: official llama.cpp cannot read PQ2_0 format.
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
    echo [ERROR] llama-server not found (checked LLAMA_EXE, .local\bin\foq-llama, PATH).
    echo The Foq model requires the PQ2_0 llama.cpp build:
    echo https://github.com/yohanargentina-oss/Foq/releases
    pause
    exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found: %MODEL_PATH%
    echo Run 'foq setup' or set the MODEL_PATH environment variable.
    pause
    exit /b 1
)

echo [*] Starting llama-server with: %MODEL_PATH% on port %PORT%...
"%LLAMA_EXE%" -m "%MODEL_PATH%" -ngl 99 -c 4096 -b 2048 -ub 512 -np 4 --flash-attn on --port %PORT% --host 127.0.0.1 --alias foq --alias foq-system1
