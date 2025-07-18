\# CFDB Databricks Project



\## Project Context

I'm building a college football data pipeline using Databricks Delta Live Tables to predict team performance. Data comes from S3, goes through bronze→silver→gold layers in Unity Catalog.



\## Environment

\- \*\*Databricks\*\*: `https://dbc-08c10e87-023f.cloud.databricks.com/`

\- \*\*Unity Catalog\*\*: `cfdb\_dev` with schemas `bronze`, `silver`, `gold`

\- \*\*S3 Source\*\*: `s3://ncaadata/` (already mapped as external location)



\## Data Sources (7 datasets)

1\. `teams` - JSON format, single folder

2\. `games` - CSV format, single folder  

3\. `game\_stats` - CSV format, single folder

4\. `season\_stats` - CSV format, single folder

5\. `game\_drives` - CSV format, single folder

6\. `conferences` - CSV format, single folder

7\. `plays` - Parquet format, partitioned by year (`s3://ncaadata/plays/2024/`)



\## Current Status

\- ✅ Bronze layer DLT pipeline designed (in `databricks/dlt\_pipelines/bronze\_layer.sql`)

\- ✅ Unity Catalog setup script ready (in `databricks/sql/unity\_catalog\_setup.sql`)

\- 🔄 Need MCP server for Claude Desktop integration

\- ⏳ Silver/Gold layers to be designed based on data exploration



\## Goals

1\. \*\*Immediate\*\*: Deploy bronze DLT pipeline to ingest raw S3 data

2\. \*\*Next\*\*: Build MCP server so I can chat with Claude Desktop about the data

3\. \*\*Future\*\*: Design silver/gold transformations for performance prediction features



\## Technical Preferences

\- SQL-first approach (I'm more comfortable with SQL than Python)

\- Use Python only where needed (like play-by-play text parsing)

\- Batch processing (one-time demo, not continuous streaming)



\## Prediction Focus

Build features for predicting:

\- Game outcomes (win/loss)

\- Point spreads

\- Team performance ratings

\- Using play-by-play data, game stats, and historical performance



\## Help Needed

1\. Review and optimize the bronze DLT pipeline

2\. Create MCP server for data exploration with Claude Desktop

3\. Plan silver/gold layer transformations based on actual data schemas

4\. Design ML-ready feature engineering



\## Key Technical Learnings

### DLT Constraint Syntax
**IMPORTANT**: Use inline constraint syntax, NOT ALTER TABLE statements:

```sql
-- ✅ CORRECT - Inline constraints
CREATE OR REFRESH STREAMING LIVE TABLE table_name
COMMENT "Description"
TBLPROPERTIES (...)
CONSTRAINT constraint_name EXPECT (condition) ON VIOLATION DROP ROW
AS SELECT ...

-- ❌ INCORRECT - ALTER TABLE not supported in DLT
ALTER TABLE LIVE.table_name 
ADD CONSTRAINT constraint_name 
EXPECT (condition) ON VIOLATION DROP ROW;
```

### Lakeflow Pipeline Structure
- **Pipeline Root**: `databricks/dlt_pipeline/`
- **Transformations**: Flat structure in `transformations/` (DLT prefers no subfolders)
- **Explorations**: Data analysis and monitoring views in `explorations/`
- **Utilities**: Reusable Python modules in `utilities/`

**Note**: DLT pipelines work better with a flat file structure in transformations rather than bronze/silver/gold subfolders.

## Documentation

I have PDF files with information about how the CFDB datasets relate to each other and field definitions.

