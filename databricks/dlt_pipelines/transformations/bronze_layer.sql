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
)
CONSTRAINT valid_team_id EXPECT (id IS NOT NULL);

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
)
CONSTRAINT valid_game_id EXPECT (id IS NOT NULL)
CONSTRAINT valid_season EXPECT (season >= 2000 AND season <= 2030);

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
    regexp_extract(input_file_name(), r'plays/(\d)/', 1) as year_partition
FROM cloud_files(
    's3://ncaadata/plays/',
    'parquet',
    map(
        'cloudFiles.inferSchema', 'true',
        'cloudFiles.schemaEvolutionMode', 'addNewColumns',
        'recursiveFileLookup', 'true'  -- Important for nested year folders
    )
)
CONSTRAINT valid_play_game_id EXPECT (gameId IS NOT NULL);

