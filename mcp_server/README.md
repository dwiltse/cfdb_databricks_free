# CFDB MCP Server

A Model Context Protocol (MCP) server that provides Claude Desktop with secure access to CFDB (College Football Database) data stored in Databricks.

## Features

- 🏈 Query college football data directly from Claude
- 🔒 Secure credential management using environment variables
- 🔄 Connection pooling with automatic cleanup to prevent session handle issues
- 🧪 Independent testing capabilities
- 📊 Support for teams, games, plays, drives, and season statistics

## Setup

### 1. Initial Setup
```bash
cd mcp_server
chmod +x setup.sh
./setup.sh
```

### 2. Configure Databricks Credentials
Edit the `.env` file with your Databricks credentials:
```env
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your-access-token
```

### 3. Test the Server
```bash
./test.sh
# OR manually:
source venv/bin/activate
python test_server.py
```

### 4. Add to Claude Desktop
Copy the contents of `claude_desktop_config.json` to your Claude Desktop configuration file.

## Security Features

- **No credential exposure**: Credentials are loaded from `.env` file, not passed through MCP configuration
- **Environment validation**: Server validates all required environment variables on startup  
- **Connection cleanup**: Automatic cleanup after each query to prevent persistent session issues
- **Working directory isolation**: Server runs in its own directory with proper Python environment

## Available Tools

### `query_cfdb_data`
Execute SQL queries against CFDB bronze layer data.
```sql
SELECT team, wins, losses FROM teams_bronze WHERE classification = 'fbs' LIMIT 10
```

### `get_table_schema`
Get schema information for CFDB tables.
```
get_table_schema(table_name="teams")
```

### `get_data_summary`
Get summary statistics for all CFDB tables.

### `suggest_silver_layer`
Get suggestions for silver layer transformations based on bronze data analysis.

## Troubleshooting

### "Invalid SessionHandle" Error
This was caused by persistent database connections. The server now:
- Creates fresh connections for each query
- Properly closes connections after each operation  
- Cleans up cursors and sessions automatically

### "Module not found" Error
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`

### Connection Issues
- Verify Databricks warehouse is running
- Check `.env` file contains valid credentials
- Test connection independently: `python test_server.py`

## Architecture

```
MCP Client (Claude Code) 
    ↓
MCP Server (this server)
    ↓ 
Databricks SQL Warehouse
    ↓
CFDB Bronze Layer Tables
```

The server maintains a clean separation between the MCP protocol and database connections, ensuring reliable operation and preventing credential exposure.