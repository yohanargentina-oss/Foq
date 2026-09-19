@echo off
title FOQ - Web Showcase
echo ===================================================
echo   FOQ - Site Marketing Machine-Native (Style typesafe.ai)
echo ===================================================
echo.
echo Ouverture directe dans le navigateur par defaut...
start "" "%~dp0site\index.html"
echo.
echo Le site fonctionne en local (fichiers autonomes, zero dependance).
echo Si vous souhaitez le servir via un serveur web local sur le port 8088 :
echo .\venv\Scripts\python.exe -m http.server -d site 8088
pause
