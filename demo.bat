
REM Change directory to the location of this script
cd /d %~dp0

REM Activate the Python virtual environment
call env\Scripts\activate.bat

REM Start the main application (should be available in the virtual environment)
start_app

REM Keep the command window open after the app exits
pause

