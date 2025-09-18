import pyodbc
import yaml
import textwrap
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
import struct
from struct import pack
from sqlalchemy import create_engine, text
from azure.identity import AzureCliCredential


# -------------------------------
# Settings
# -------------------------------
SERVER = os.getenv("CHAT_SERVER_DEMO_AZURE_SQL_SERVER")
DB_NAME = "chatserverdemo"
KEYVAULT_NAME = os.getenv("AZURE_KEY_VAULT_NAME")
APP_USER_SECRET_NAME = "chat-app-user-password"  

# -------------------------------
# Azure identity
# -------------------------------
#credential = DefaultAzureCredential()

credential = AzureCliCredential()
token = credential.get_token("https://database.windows.net/.default")



# Fetch app user password from Key Vault
kv_uri = f"https://{KEYVAULT_NAME}.vault.azure.net/"
kv_client = SecretClient(vault_url=kv_uri, credential=credential)
APP_USER_PASSWORD = kv_client.get_secret(APP_USER_SECRET_NAME).value

# -------------------------------
# Helpers
# -------------------------------
def to_utf16le(token: str) -> bytes:
    return b"".join(pack("<H", ord(c)) for c in token)

def get_engine(database="master"):
    #token = credential.get_token("https://database.windows.net/.default")
    exptoken = b''.join(pack('<H', ord(c)) for c in token.token)
    tokenstruct = struct.pack('<I', len(exptoken)) + exptoken

    connection_string = (
        f"mssql+pyodbc:///?odbc_connect="
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={database};"
        f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
    )

    return create_engine(
        connection_string,
        connect_args={"attrs_before": {1256: tokenstruct}},
    )



def run_sql(engine, sql: str, autocommit=False):
    if autocommit:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql(sql)
            conn.commit()  # explicit commit for good measure
    else:
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)



# -------------------------------
# Main setup
# -------------------------------
def main():
    # Load YAML
    yaml_file = Path(__file__).parent.parent / "yaml_files" / "sql.yaml"
    with open(yaml_file, "r") as f:
        yaml_text = f.read()

    yaml_text = yaml_text.replace("{APP_USER_PASSWORD}", APP_USER_PASSWORD)
    config = yaml.safe_load(yaml_text)

    db_tasks = config["sql"]["db_creation_and_deletion"]
    sp_tasks = config["sql"]["stored_procedures"]

    # 1. Drop DB if exists
    print("Dropping database if exists...")
    run_sql(get_engine("master"), db_tasks["drop_db_if_exists"], autocommit=True)

    # 2. Create DB
    print("Creating database...")
    run_sql(get_engine("master"), db_tasks["create_db"], autocommit=True)

    # 3. Create schemas, tables, app user
    print("Creating schemas, tables, app user...")
    for key, sql_block in db_tasks.items():
        if key in ("drop_db_if_exists", "create_db"):
            continue
        run_sql(get_engine(DB_NAME), sql_block)

    # 4. Create stored procedures
    print("Creating stored procedures...")
    for _, sql_block in sp_tasks.items():
        run_sql(get_engine(DB_NAME), sql_block)

    print("✅ Database setup complete.")


if __name__ == "__main__":
    main()
