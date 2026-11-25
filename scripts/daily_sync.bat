@echo off
REM Windows Günlük KDS Canlı Veri Senkronizasyonu Batch Betiği
REM Görev Zamanlayıcı (Task Scheduler) tarafından tetiklenir.

set SCRIPT_DIR=%~dp0..
cd /d "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%\logs" mkdir "%SCRIPT_DIR%\logs"
set LOG_FILE=%SCRIPT_DIR%\logs\daily_sync.log

echo ========================================================== >> "%LOG_FILE%"
echo [%DATE% %TIME%] KDS Windows Senkronizasyonu Baslatiliyor... >> "%LOG_FILE%"

if exist "%SCRIPT_DIR%\.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%\.venv\Scripts\activate.bat"
) else if exist "%SCRIPT_DIR%\venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
)

python "%SCRIPT_DIR%\etl\daily_sync.py" >> "%LOG_FILE%" 2>&1
echo [%DATE% %TIME%] Senkronizasyon Tamamlandi. >> "%LOG_FILE%"
