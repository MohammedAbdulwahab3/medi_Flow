@echo off
echo ========================================
echo MediFlow - Restarting Django Server
echo ========================================
echo.

echo Stopping any running Django servers...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo Checking Django configuration...
python manage.py check

echo.
echo Starting Django server...
echo Server will be available at: http://127.0.0.1:8000
echo Admin panel: http://127.0.0.1:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver
