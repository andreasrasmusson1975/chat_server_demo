"""
# Install/Uninstall Package for Chat Server Demo

This package provides automated installation and uninstall scripts for the chat_server_demo application.

## Installation Instructions

The chat_server_demo package includes a comprehensive installation script (`install.sh`) that automates the complete setup process including system dependencies, Python environment, database configuration, systemd service, and nginx reverse proxy with TLS.

### Prerequisites

- Ubuntu/Debian Linux system with `sudo` access
- Internet connection for downloading dependencies
- Azure account with appropriate permissions for Key Vault access
- Domain name pointing to your server (for TLS certificate)

### Required Parameters

The installation script requires the following parameters:

- `--sql-server`: Azure SQL Server FQDN (e.g., `myserver.database.windows.net`)
- `--db-name`: Database name (e.g., `chatserverdemo`)
- `--app-user-secret`: Azure Key Vault secret name for app user password
- `--domain`: Domain name for the application (e.g., `myapp.example.com`)

### Optional Parameters

- `--with-db`: Create and initialize the database during installation
- `--fresh`: Remove existing virtual environment before creating a new one
- `--venv DIR`: Specify custom virtual environment directory (default: `env`)

### Basic Installation

```bash
./install.sh --sql-server myserver.database.windows.net \\
             --db-name chatserverdemo \\
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \\
             --domain myapp.example.com
```

### Installation with Database Creation

```bash
./install.sh --sql-server myserver.database.windows.net \\
             --db-name chatserverdemo \\
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \\
             --domain myapp.example.com \\
             --with-db
```

### Fresh Installation

To perform a clean installation (removes existing virtual environment):

```bash
./install.sh --sql-server myserver.database.windows.net \\
             --db-name chatserverdemo \\
             --app-user-secret CHATSERVERDEMO-APP-PASSWORD \\
             --domain myapp.example.com \\
             --fresh
```

### What the Installation Script Does

1. **System Dependencies**: Installs Python 3, build tools, nginx, ODBC drivers, and Azure CLI
2. **Authentication**: Prompts for Azure login if not already authenticated
3. **Python Environment**: Creates and configures a virtual environment with all required packages
4. **Package Installation**: Installs the chat_server_demo package and its dependencies
5. **Database Setup**: Optionally creates and initializes the database (with `--with-db` flag)
6. **System Service**: Creates and enables a systemd service for automatic startup
7. **Web Server**: Configures nginx as a reverse proxy with automatic TLS certificate generation
8. **Security**: Sets up secure HTTPS access using Let's Encrypt certificates

### Post-Installation

After successful installation, you can:

- Check service status: `sudo systemctl status chat_server_demo`
- View logs: `journalctl -u chat_server_demo -f`
- Access the application: `https://yourdomain.com`

### Uninstallation

To remove the chat_server_demo installation:

```bash
# Remove service and nginx config only
./uninstall.sh

# Complete removal including virtual environment
./uninstall.sh --purge
```

### Troubleshooting

- Ensure all required parameters are provided
- Verify your Azure credentials are valid
- Check that your domain DNS is properly configured
- Review installation logs for any error messages
- Ensure your system meets all prerequisites

For additional help, use: `./install.sh --help`
"""