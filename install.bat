:: ===========================================================
:: 📋 Prerequisites for create_db.py on Windows
:: ===========================================================
:: 1. System requirements
::    - Windows 10/11 with Python 3.10+ installed
::    - Visual C++ Redistributable (required by pyodbc / ODBC driver)
::      https://aka.ms/vs/17/release/vc_redist.x64.exe
::
:: 2. ODBC Driver for SQL Server
::    - Install ODBC Driver 18 for SQL Server:
::      https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
::    - After install, verify with:
::         odbcconf /Lv
::      and ensure "ODBC Driver 18 for SQL Server" appears.
::
:: 3. Environment variables
::    - CHAT_SERVER_DEMO_AZURE_SQL_SERVER
::        The FQDN of your Azure SQL Server (e.g. myserver.database.windows.net)
::    - AZURE_KEY_VAULT_NAME
::        The name of your Azure Key Vault (without .vault.azure.net)
::
:: 4. Authentication
::    - Install Azure CLI:
::        https://aka.ms/installazurecliwindows
::    - Run "az login" in a terminal before installation, or ensure that
::      the account is already logged in.
::    - The Azure AD account you use must be set as "Active Directory admin"
::      for the SQL Server, OR you must configure a service principal /
::      managed identity with access:
::          CREATE USER [name] FROM EXTERNAL PROVIDER;
::          ALTER ROLE db_owner ADD MEMBER [name];
::
:: 5. Python packages (installed automatically by install.bat into the venv)
::    - pyodbc
::    - sqlalchemy
::    - azure-identity
::    - azure-keyvault-secrets
::    - pyyaml
::    - streamlit
::
:: With these prerequisites, create_db.py will:
::    - Fetch the app user password from Key Vault
::    - Obtain an Azure AD access token
::    - Connect securely to Azure SQL using pyodbc/sqlalchemy
::    - Create/drop the chatserverdemo database
::    - Run schema/table/stored procedure setup from yaml_files/sql.yaml
:: ===========================================================


echo Creating environment...
echo Upgrading pip in venv...
echo Installing Chat Server Demo (no deps) into venv...
echo Installing core dependencies into venv...

@echo off
setlocal

REM Parse optional parameter
set CREATE_DB=0
if "%1"=="--with-db" set CREATE_DB=1

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
env\Scripts\python.exe -m pip install streamlit pyaml pyodbc azure-identity azure-keyvault-secrets sqlalchemy

REM Optionally create database
if %CREATE_DB%==1 (
    echo Creating database...
    env\Scripts\python.exe -m chat_server_demo.database.create_db
)

echo Installation complete.
pause
endlocal
