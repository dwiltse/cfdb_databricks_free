#!/bin/bash
# Setup script for CFDB MCP Server

echo "Setting up CFDB MCP Server..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create .env file from example
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your Databricks credentials"
fi

echo "Setup complete!"
echo ""
echo "To use the MCP server:"
echo "1. Edit .env with your Databricks credentials"
echo "2. Add claude_desktop_config.json contents to your Claude Desktop settings"
echo "3. Restart Claude Desktop"
echo ""
echo "To activate the virtual environment manually:"
echo "source venv/bin/activate"