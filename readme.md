# CFDB Databricks Project - Claude Code

## Quick Overview
- **Goal**: Ingest CFDB data from S3 → Bronze → Silver → Gold for performance prediction
- **Workspace**: `https://dbc-08c10e87-023f.cloud.databricks.com/`
- **Catalog**: `cfdb_dev` with schemas `bronze`, `silver`, `gold`
- **S3 Path**: `s3://ncaadata/`

## Data Sources (7 datasets)
- `teams` (JSON, single folder)
- `games, game_stats, season_stats, game_drives, conferences` (CSV, single folders)  
- `plays` (Parquet, partitioned by year: `s3://ncaadata/plays/2024/`)

## Current Status
✅ Bronze layer DLT pipeline ready  
🔄 Need to set up MCP server for Claude chat with data  
⏳ Silver/Gold layers to be designed with Claude's help

## Next Steps
1. Deploy bronze DLT pipeline
2. Create MCP server for data exploration
3. Design silver/gold transformations
4. Build performance prediction features

## Key Files
- `databricks/sql/unity_catalog_setup.sql` - Run first
- `databricks/dlt_pipelines/bronze_layer.sql` - Main DLT pipeline
- `mcp_server/` - For Claude Desktop integration (to build)

## Performance Prediction Focus
Target metrics: game outcomes, point spreads, team ratings using play-by-play and game statistics.