#!/usr/bin/env python3
"""
Test script for CFDB MCP Server - Run independently to verify setup
"""
import asyncio
import json
from server import CFDBServer

async def test_server():
    """Test the CFDB server functionality"""
    print("🚀 Testing CFDB MCP Server...")
    
    try:
        # Initialize server
        server = CFDBServer()
        print("✅ Server initialized successfully")
        
        # Test database connection by running a simple query
        test_query = "SELECT * FROM teams_bronze LIMIT 5"
        print(f"🔍 Running test query: {test_query}")
        
        result = await server._query_cfdb_data(test_query, 5)
        
        if result and len(result) > 0:
            print("✅ Database connection successful!")
            print("📊 Sample result:")
            # Parse the JSON response from the text content
            result_text = result[0].text
            if "Query Results:" in result_text:
                json_part = result_text.split("Query Results:\n", 1)[1]
                parsed_result = json.loads(json_part)
                print(f"   - Found {parsed_result['row_count']} rows")
                print(f"   - Columns: {', '.join(parsed_result['columns'][:5])}{'...' if len(parsed_result['columns']) > 5 else ''}")
            else:
                print(f"   - {result_text[:200]}...")
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check that your .env file exists and contains valid Databricks credentials")
        print("2. Verify your Databricks warehouse is running")
        print("3. Confirm the bronze tables exist in your catalog")
        return False
    
    print("\n🎉 Server test completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_server())
    exit(0 if success else 1)