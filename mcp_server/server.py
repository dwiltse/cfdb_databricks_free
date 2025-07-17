#!/usr/bin/env python3
"""
CFDB MCP Server - Provides Claude Desktop access to CFDB data insights
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from databricks import sql
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfdb-mcp-server")

class CFDBServer:
    def __init__(self):
        self.server = Server("cfdb-data-server")
        self.connection = None
        self.cursor = None
        
        # Databricks connection parameters
        self.databricks_config = {
            "server_hostname": os.getenv("DATABRICKS_SERVER_HOSTNAME"),
            "http_path": os.getenv("DATABRICKS_HTTP_PATH"),
            "access_token": os.getenv("DATABRICKS_ACCESS_TOKEN"),
            "catalog": "cfdb_dev",
            "schema": "bronze"
        }
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools for CFDB data analysis"""
            return [
                types.Tool(
                    name="query_cfdb_data",
                    description="Execute SQL queries against CFDB bronze layer data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute against CFDB data"
                            },
                            "limit": {
                                "type": "integer", 
                                "description": "Maximum number of rows to return (default 100)",
                                "default": 100
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_table_schema",
                    description="Get schema information for CFDB tables",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table to describe (teams, games, plays, etc.)"
                            }
                        },
                        "required": ["table_name"]
                    }
                ),
                types.Tool(
                    name="get_data_summary",
                    description="Get summary statistics and record counts for all CFDB tables",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.Tool(
                    name="suggest_silver_layer",
                    description="Analyze bronze data and suggest silver layer transformations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "description": "Specific area to focus on (games, teams, plays, stats)",
                                "enum": ["games", "teams", "plays", "stats", "all"]
                            }
                        },
                        "required": ["focus_area"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any] | None
        ) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if not arguments:
                arguments = {}
            
            try:
                if name == "query_cfdb_data":
                    return await self._query_cfdb_data(
                        arguments.get("query", ""),
                        arguments.get("limit", 100)
                    )
                
                elif name == "get_table_schema":
                    return await self._get_table_schema(
                        arguments.get("table_name", "")
                    )
                
                elif name == "get_data_summary":
                    return await self._get_data_summary()
                
                elif name == "suggest_silver_layer":
                    return await self._suggest_silver_layer(
                        arguments.get("focus_area", "all")
                    )
                
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    async def _connect_databricks(self):
        """Establish connection to Databricks"""
        if self.connection is None:
            try:
                self.connection = sql.connect(
                    server_hostname=self.databricks_config["server_hostname"],
                    http_path=self.databricks_config["http_path"],
                    access_token=self.databricks_config["access_token"]
                )
                self.cursor = self.connection.cursor()
                logger.info("Connected to Databricks")
            except Exception as e:
                logger.error(f"Failed to connect to Databricks: {str(e)}")
                raise
    
    async def _query_cfdb_data(self, query: str, limit: int) -> List[types.TextContent]:
        """Execute SQL query against CFDB data"""
        await self._connect_databricks()
        
        # Add catalog/schema context and limit
        full_query = f"""
        USE CATALOG {self.databricks_config['catalog']};
        USE SCHEMA {self.databricks_config['schema']};
        {query}
        LIMIT {limit};
        """
        
        try:
            self.cursor.execute(full_query)
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            # Format results as JSON
            formatted_results = []
            for row in results:
                formatted_results.append(dict(zip(columns, row)))
            
            response = {
                "query": query,
                "row_count": len(results),
                "columns": columns,
                "data": formatted_results[:50]  # Limit display for readability
            }
            
            return [types.TextContent(
                type="text", 
                text=f"Query Results:\n{json.dumps(response, indent=2, default=str)}"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Query failed: {str(e)}"
            )]
    
    async def _get_table_schema(self, table_name: str) -> List[types.TextContent]:
        """Get schema for specified table"""
        await self._connect_databricks()
        
        schema_query = f"DESCRIBE TABLE {self.databricks_config['catalog']}.{self.databricks_config['schema']}.{table_name}_bronze"
        
        try:
            self.cursor.execute(schema_query)
            schema_info = self.cursor.fetchall()
            
            schema_text = f"Schema for {table_name}_bronze:\n\n"
            for row in schema_info:
                schema_text += f"{row[0]}: {row[1]} ({row[2] or 'nullable'})\n"
            
            return [types.TextContent(type="text", text=schema_text)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Failed to get schema for {table_name}: {str(e)}"
            )]
    
    async def _get_data_summary(self) -> List[types.TextContent]:
        """Get summary of all CFDB data"""
        await self._connect_databricks()
        
        summary_query = f"SELECT * FROM {self.databricks_config['catalog']}.{self.databricks_config['schema']}.bronze_summary"
        
        try:
            self.cursor.execute(summary_query)
            summary_data = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            summary_text = "CFDB Data Summary:\n\n"
            for row in summary_data:
                row_dict = dict(zip(columns, row))
                summary_text += f"Table: {row_dict['table_name']}\n"
                summary_text += f"  Records: {row_dict['record_count']:,}\n"
                summary_text += f"  Files: {row_dict['file_count']}\n"
                summary_text += f"  Latest Ingestion: {row_dict['latest_ingestion']}\n\n"
            
            return [types.TextContent(type="text", text=summary_text)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Failed to get data summary: {str(e)}"
            )]
    
    async def _suggest_silver_layer(self, focus_area: str) -> List[types.TextContent]:
        """Suggest silver layer transformations based on bronze data analysis"""
        suggestions = {
            "games": """
Silver Layer Suggestions for Games:

1. **Clean Game Data**
   - Standardize team names and conference affiliations
   - Add derived fields like game_margin, total_score
   - Handle neutral site games properly
   
2. **Time Dimensions**
   - Create game_date dimension with season, week, day_of_week
   - Add playoff/bowl game indicators
   
3. **Sample SQL:**
   ```sql
   CREATE OR REFRESH LIVE TABLE games_silver AS
   SELECT 
     id as game_id,
     season,
     week,
     CASE WHEN neutral_site THEN 'Neutral' ELSE home_team END as venue_type,
     home_score + away_score as total_score,
     ABS(home_score - away_score) as margin,
     CASE WHEN week > 15 THEN 'Postseason' ELSE 'Regular' END as game_type
   FROM LIVE.games_bronze
   WHERE id IS NOT NULL
   ```
            """,
            "teams": """
Silver Layer Suggestions for Teams:

1. **Team Standardization**
   - Create master team dimension with consistent naming
   - Add current/historical conference mappings
   - Include geographic and classification data

2. **Sample SQL:**
   ```sql
   CREATE OR REFRESH LIVE TABLE teams_silver AS
   SELECT DISTINCT
     id as team_id,
     school as team_name,
     conference,
     division,
     classification,
     current_timestamp() as effective_date
   FROM LIVE.teams_bronze
   ```
            """,
            "plays": """
Silver Layer Suggestions for Plays:

1. **Play Categorization**
   - Standardize play types (rush, pass, kick, etc.)
   - Add success indicators based on down/distance
   - Calculate EPA (Expected Points Added) if possible

2. **Performance Metrics**
   - Yards after contact for rush plays
   - Air yards vs YAC for pass plays
   - Situational context (red zone, third down, etc.)

3. **Sample SQL:**
   ```sql
   CREATE OR REFRESH LIVE TABLE plays_silver AS
   SELECT 
     gameId as game_id,
     driveId as drive_id,
     playNumber as play_number,
     CASE 
       WHEN playType LIKE '%Rush%' THEN 'Rush'
       WHEN playType LIKE '%Pass%' THEN 'Pass'
       ELSE 'Other'
     END as play_category,
     yardsGained as yards_gained,
     CASE WHEN down <= 2 AND yardsGained >= yardsToGo THEN 1 ELSE 0 END as successful_play
   FROM LIVE.plays_bronze
   WHERE gameId IS NOT NULL
   ```
            """
        }
        
        if focus_area == "all":
            response = "Complete Silver Layer Architecture:\n\n"
            for area, suggestion in suggestions.items():
                response += f"{suggestion}\n\n---\n\n"
        else:
            response = suggestions.get(focus_area, f"No suggestions available for {focus_area}")
        
        return [types.TextContent(type="text", text=response)]
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="cfdb-data-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

if __name__ == "__main__":
    server = CFDBServer()
    asyncio.run(server.run())