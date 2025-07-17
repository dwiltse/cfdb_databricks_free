-- CFDB Bronze Layer DLT Pipeline
-- Target: cfdb_dev.bronze schema
-- Source: S3 external location s3://ncaadata/

-- Set target schema for all tables
USE CATALOG cfdb_dev;
USE SCHEMA bronze;

-- =====================================================
-- TEAMS (JSON format, single folder)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE teams_bronze
COMMENT "Raw teams data from S3 in JSON format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "id,school"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/teams/',
    'json',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'multiline', 'true'
    )
);

-- =====================================================
-- GAMES (CSV format, single folder) 
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE games_bronze
COMMENT "Raw games data from S3 in CSV format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "id,season,week"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/games/',
    'csv',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'header', 'true'
    )
);

-- =====================================================
-- GAME_STATS (CSV format, single folder)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE game_stats_bronze
COMMENT "Raw game statistics data from S3 in CSV format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "gameId,teamId"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/game_stats/',
    'csv',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'header', 'true'
    )
);

-- =====================================================
-- SEASON_STATS (CSV format, single folder)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE season_stats_bronze
COMMENT "Raw season statistics data from S3 in CSV format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "season,teamId"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/season_stats/',
    'csv',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'header', 'true'
    )
);

-- =====================================================
-- GAME_DRIVES (CSV format, single folder)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE game_drives_bronze
COMMENT "Raw game drives data from S3 in CSV format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "gameId,driveId"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/game_drives/',
    'csv',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'header', 'true'
    )
);

-- =====================================================
-- CONFERENCES (CSV format, single folder)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE conferences_bronze
COMMENT "Raw conferences data from S3 in CSV format"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "id,name"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file
FROM cloud_files(
    's3://ncaadata/conferences/',
    'csv',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'header', 'true'
    )
);

-- =====================================================
-- PLAYS (Parquet format, partitioned by year)
-- =====================================================
CREATE OR REFRESH STREAMING LIVE TABLE plays_bronze
COMMENT "Raw play-by-play data from S3 in Parquet format, partitioned by year"
TBLPROPERTIES (
  "quality" = "bronze",
  "pipelines.autoOptimize.zOrderCols" = "gameId,driveId,playNumber"
)
AS SELECT 
    *,
    current_timestamp() as ingestion_timestamp,
    input_file_name() as source_file,
    -- Extract year from file path for partitioning
    regexp_extract(input_file_name(), r'plays/(\d{4})/', 1) as year_partition
FROM cloud_files(
    's3://ncaadata/plays/',
    'parquet',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'recursiveFileLookup', 'true'  -- Important for nested year folders
    )
);

-- =====================================================
-- DATA QUALITY EXPECTATIONS (Optional but Recommended)
-- =====================================================

-- Add data quality constraints to key tables
ALTER TABLE LIVE.teams_bronze 
ADD CONSTRAINT valid_team_id 
EXPECT (id IS NOT NULL) ON VIOLATION DROP ROW;

ALTER TABLE LIVE.games_bronze 
ADD CONSTRAINT valid_game_id 
EXPECT (id IS NOT NULL) ON VIOLATION DROP ROW;

ALTER TABLE LIVE.games_bronze 
ADD CONSTRAINT valid_season 
EXPECT (season >= 2000 AND season <= 2030) ON VIOLATION DROP ROW;

ALTER TABLE LIVE.plays_bronze 
ADD CONSTRAINT valid_play_game_id 
EXPECT (gameId IS NOT NULL) ON VIOLATION DROP ROW;

-- =====================================================
-- UTILITY VIEWS FOR DATA EXPLORATION
-- =====================================================

-- Create a view to see record counts by table
CREATE OR REFRESH LIVE VIEW bronze_summary
COMMENT "Summary of record counts and data freshness across bronze tables"
AS 
SELECT 
    'teams' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.teams_bronze
UNION ALL
SELECT 
    'games' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.games_bronze
UNION ALL
SELECT 
    'game_stats' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.game_stats_bronze
UNION ALL
SELECT 
    'season_stats' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.season_stats_bronze
UNION ALL
SELECT 
    'game_drives' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.game_drives_bronze
UNION ALL
SELECT 
    'conferences' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.conferences_bronze
UNION ALL
SELECT 
    'plays' as table_name,
    count(*) as record_count,
    max(ingestion_timestamp) as latest_ingestion,
    count(distinct source_file) as file_count
FROM LIVE.plays_bronze;

-- Create a view to see plays data by year
CREATE OR REFRESH LIVE VIEW plays_by_year
COMMENT "Play counts by year partition for monitoring data completeness"
AS
SELECT 
    year_partition,
    count(*) as play_count,
    count(distinct gameId) as unique_games,
    min(ingestion_timestamp) as first_ingested,
    max(ingestion_timestamp) as last_ingested
FROM LIVE.plays_bronze
WHERE year_partition IS NOT NULL
GROUP BY year_partition
ORDER BY year_partition DESC;