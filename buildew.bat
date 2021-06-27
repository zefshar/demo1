@ECHO OFF

REM CHECK PYTHON
WHERE python
IF %ERRORLEVEL% NEQ 0 (ECHO 'error: Python not available, please install it or add to the PATH variable' && exit 1) ^
ELSE ECHO Python available

REM Check python version, for windows; only to start with 3.6
FOR /F "tokens=2" %%a IN ('python --version') DO SET PYTHON_VERSION=%%a
FOR /F "delims=. tokens=1" %%a IN ('ECHO %PYTHON_VERSION%') DO SET PYTHON_MAJOR_VERSION=%%a
FOR /F "delims=. tokens=2" %%a IN ('ECHO %PYTHON_VERSION%') DO SET PYTHON_MINOR_VERSION=%%a

IF %PYTHON_MAJOR_VERSION% LSS 3 (ECHO 'error: Python version is %PYTHON_VERSION%, but required 3.6 or greater' && exit 1)
IF %PYTHON_MINOR_VERSION% LSS 6 (ECHO 'error: Python version is %PYTHON_VERSION%, but required 3.6 or greater' && exit 1)

ECHO Version: %PYTHON_VERSION%

IF NOT EXIST .venv (
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
)