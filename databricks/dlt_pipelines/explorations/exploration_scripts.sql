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