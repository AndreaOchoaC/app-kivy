@echo off
rem Prepara el entorno despues de clonar el repo (ver README.md). Se puede ejecutar varias veces.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 scripts\bootstrap.py %*
) else (
    python scripts\bootstrap.py %*
)
if errorlevel 1 (
    echo.
    echo Algo fallo. Lee el mensaje de arriba.
    pause
    exit /b 1
)
