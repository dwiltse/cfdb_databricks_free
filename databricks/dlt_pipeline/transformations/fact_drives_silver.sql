-- Databricks DLT Pipeline - Silver Layer
-- File: fact_drives_silver.sql

-- Drive-level details linked to FBS games
CREATE OR REFRESH MATERIALIZED VIEW LIVE.fact_drives_silver (
  CONSTRAINT valid_game_id EXPECT (game_id IS NOT NULL),
  CONSTRAINT valid_drive_id EXPECT (drive_id IS NOT NULL),
  CONSTRAINT valid_drive_number EXPECT (driveNumber >= 1),
  CONSTRAINT valid_teams EXPECT (offense IS NOT NULL AND defense IS NOT NULL)
)
COMMENT "Silver layer - Drive details for FBS games with calculated metrics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT 
    -- Primary identifiers
    d.gameId as game_id,
    d.id as drive_id,
    d.driveNumber as drive_number,
    
    -- Team identifiers
    d.offense,
    d.offenseConference as offense_conference,
    d.defense,
    d.defenseConference as defense_conference,
    
    -- Drive characteristics
    d.scoring,
    d.plays,
    d.yards,
    d.driveResult as drive_result,
    d.isHomeOffense as is_home_offense,
    
    -- Field position
    d.startPeriod as start_period,
    d.startYardline as start_yardline,
    d.startYardsToGoal as start_yards_to_goal,
    d.endPeriod as end_period,
    d.endYardline as end_yardline,
    d.endYardsToGoal as end_yards_to_goal,
    
    -- Score progression
    d.startOffenseScore as start_offense_score,
    d.startDefenseScore as start_defense_score,
    d.endOffenseScore as end_offense_score,
    d.endDefenseScore as end_defense_score,
    
    -- Calculated metrics
    CASE 
      WHEN d.plays > 0 THEN d.yards / d.plays
      ELSE 0
    END as yards_per_play,
    
    CASE 
      WHEN d.startYardsToGoal IS NOT NULL AND d.endYardsToGoal IS NOT NULL 
      THEN d.startYardsToGoal - d.endYardsToGoal
      ELSE d.yards
    END as net_field_position_gain,
    
    CASE 
      WHEN d.driveResult IN ('TD', 'TOUCHDOWN') THEN 'Touchdown'
      WHEN d.driveResult IN ('FG', 'FIELD GOAL') THEN 'Field Goal'
      WHEN d.driveResult = 'PUNT' THEN 'Punt'
      WHEN d.driveResult = 'DOWNS' THEN 'Turnover on Downs'
      WHEN d.driveResult IN ('INT', 'INTERCEPTION') THEN 'Interception'
      WHEN d.driveResult IN ('FUMBLE', 'LOST FUMBLE') THEN 'Fumble'
      ELSE 'Other'
    END as drive_outcome_category,
    
    -- Game context from silver games
    g.season,
    g.week,
    g.game_phase
    
  FROM LIVE.game_drives_bronze d
  INNER JOIN LIVE.fact_games_silver g ON d.gameId = g.game_id
  WHERE d.gameId IS NOT NULL 
    AND d.id IS NOT NULL
);