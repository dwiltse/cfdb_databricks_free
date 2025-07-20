-- Databricks DLT Pipeline - Silver Layer
-- File: fact_games_silver.sql

-- Core game results fact table with FBS filtering
CREATE OR REFRESH MATERIALIZED VIEW LIVE.fact_games_silver (
  CONSTRAINT valid_game_id EXPECT (game_id IS NOT NULL),
  CONSTRAINT valid_season EXPECT (season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1),
  CONSTRAINT fbs_teams_only EXPECT (home_classification = 'fbs' OR away_classification = 'fbs'),
  CONSTRAINT completed_games EXPECT (home_points IS NOT NULL AND away_points IS NOT NULL),
  CONSTRAINT valid_scores EXPECT (home_points >= 0 AND away_points >= 0)
)
COMMENT "Silver layer - FBS game results with calculated performance metrics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT 
    -- Primary identifiers
    id as game_id,
    season,
    week,
    start_date,
    
    -- Team identifiers
    home_team_id,
    away_team_id,
    home_team,
    away_team,
    
    -- Scores and calculated metrics
    home_points,
    away_points,
    ABS(home_points - away_points) as margin,
    home_points + away_points as total_score,
    
    -- Game characteristics
    CASE 
      WHEN week > 15 THEN 'Postseason'
      WHEN week >= 14 THEN 'Late Season' 
      ELSE 'Regular Season'
    END as game_phase,
    
    CASE 
      WHEN ABS(home_points - away_points) <= 3 THEN 'Close'
      WHEN ABS(home_points - away_points) <= 14 THEN 'Moderate'
      ELSE 'Blowout'
    END as game_competitiveness,
    
    neutral_site as is_neutral_site,
    conference_game as is_conference_game,
    
    -- Conference and classification
    home_conference,
    away_conference,
    home_classification,
    away_classification,
    
    -- Venue and attendance
    venue_id,
    attendance,
    
    -- Advanced metrics
    excitement,
    home_postgame_win_prob,
    away_postgame_win_prob,
    home_start_elo,
    home_end_elo,
    away_start_elo,
    away_end_elo,
    
    -- Derived date fields
    DATE(start_date) as game_date,
    DAYOFWEEK(start_date) as day_of_week,
    MONTH(start_date) as game_month,
    
    -- Winner identification
    CASE 
      WHEN home_points > away_points THEN home_team_id
      WHEN away_points > home_points THEN away_team_id
      ELSE NULL
    END as winner_team_id,
    
    CASE 
      WHEN home_points > away_points THEN 'home'
      WHEN away_points > home_points THEN 'away'
      ELSE 'tie'
    END as winner_location
    
  FROM LIVE.games_bronze
  WHERE (home_classification = 'fbs' OR away_classification = 'fbs')
    AND home_points IS NOT NULL 
    AND away_points IS NOT NULL
    AND id IS NOT NULL
);