#!/usr/bin/env bash

# ===========================================================
# 📋 Prerequisites for create_db.py on Linux
# ===========================================================
# 1. System packages
#    - Python 3.10+ (with venv)
#    - curl, apt-transport-https, gnupg, software-properties-common
#    - ODBC driver and tools:
#        sudo su
#        curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#        curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list \
#          | tee /etc/apt/sources.list.d/mssql-release.list
#        exit
#        sudo apt-get update
#        sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev
#    - CA certificates (for TLS):
#        sudo apt-get install -y ca-certificates
#        sudo update-ca-certificates
#
# 2. Environment variables
#    - CHAT_SERVER_DEMO_AZURE_SQL_SERVER
#        The FQDN of your Azure SQL Server (e.g. myserver.database.windows.net)
#    - AZURE_KEY_VAULT_NAME
#        The name of your Azure Key Vault (without .vault.azure.net)
#
# 3. Authentication
#    - Azure CLI must be installed and logged in:
#        curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
#        az login
#    - The logged-in Azure AD user must be set as "Active Directory admin"
#      for the SQL Server, OR a service principal/managed identity must be
#      granted access via:
#          CREATE USER [name] FROM EXTERNAL PROVIDER;
#          ALTER ROLE db_owner ADD MEMBER [name];
#
# 4. Python packages (installed in the venv by install.sh)
#    - pyodbc
#    - sqlalchemy
#    - azure-identity
#    - azure-keyvault-secrets
#    - pyyaml
#
# With these prerequisites, create_db.py will be able to:
#    - Fetch app user password from Key Vault
#    - Obtain an AAD access token
#    - Connect securely to Azure SQL using pyodbc/sqlalchemy
#    - Create/drop the chatserverdemo database
#    - Run schema/table/stored procedure setup from yaml_files/sql.yaml
# ===========================================================


set -euo pipefail

CREATE_DB=0
if [[ "${1:-}" == "--with-db" ]]; then
  CREATE_DB=1
fi

echo "📦 Creating environment..."
python3 -m venv env

echo "📦 Activating environment..."
# activate for the current shell
# (shellcheck disable=SC1091)
source env/bin/activate

echo "📦 Upgrading pip in venv..."
python -m pip install --upgrade pip

echo "📦 Installing Chat Server Demo (no deps) into venv..."
pip install . --no-deps

echo "📦 Installing core dependencies into venv..."
pip install streamlit pyyaml azure-identity azure-keyvault-secrets sqlalchemy pyodbc

if [[ $CREATE_DB -eq 1 ]]; then
  echo "🗄️  Creating database..."
  python -m chat_server_demo.database.create_db
fi

echo "✅ Installation complete."
