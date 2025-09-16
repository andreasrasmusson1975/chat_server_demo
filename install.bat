echo Creating environment...
echo Upgrading pip in venv...
echo Installing Chat Server Demo (no deps) into venv...
echo Installing core dependencies into venv...

@echo off
setlocal

REM Create a new Python virtual environment in the 'env' folder
echo Creating environment...
call python -m venv env

REM Activate the virtual environment
call env\Scripts\activate.bat

REM Upgrade pip to the latest version inside the virtual environment
echo Upgrading pip in venv...
env\Scripts\python.exe -m pip install --upgrade pip

REM Install the Chat Server Demo package (without installing dependencies)
echo Installing Chat Server Demo (no deps) into venv...
env\Scripts\python.exe -m pip install . --no-deps

REM Install core dependencies (Streamlit and PyYAML) into the virtual environment
echo Installing core dependencies into venv...
env\Scripts\python.exe -m pip install streamlit pyaml

echo Installation complete.
pause
endlocal
