@echo off
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 goto usar_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 goto usar_python
echo.
echo Santo Bigode precisa de Python 3.10 ou superior.
echo Instale em https://www.python.org/downloads/
echo Marque Add Python to PATH na instalacao e abra este arquivo novamente.
pause
exit /b 1
:usar_py
py -3 server.py
if errorlevel 1 pause
exit /b
:usar_python
python server.py
if errorlevel 1 pause
