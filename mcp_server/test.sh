#!/bin/bash
# Test script for CFDB MCP Server

cd "$(dirname "$0")"

echo "🧪 Testing CFDB MCP Server..."
echo "📂 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your Databricks credentials."
    exit 1
fi

# Activate virtual environment and run test
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "🚀 Running server test..."
python test_server.py

echo "✨ Test complete!"