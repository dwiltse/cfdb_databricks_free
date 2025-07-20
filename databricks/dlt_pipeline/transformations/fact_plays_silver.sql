-- Databricks DLT Pipeline - Silver Layer
-- File: fact_plays_silver.sql

-- Play-by-play details for FBS games
CREATE OR REFRESH MATERIALIZED VIEW LIVE.fact_plays_silver (
  CONSTRAINT valid_game_id EXPECT (gameId IS NOT NULL),
  CONSTRAINT valid_play_id EXPECT (id IS NOT NULL),
  CONSTRAINT valid_play_number EXPECT (playNumber >= 1),
  CONSTRAINT valid_teams EXPECT (offense IS NOT NULL AND defense IS NOT NULL)
)
COMMENT "Silver layer - Play-by-play data for FBS games with calculated performance metrics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT 
    -- Primary identifiers
    p.gameId as game_id,
    p.id as play_id,
    p.driveId as drive_id,
    p.driveNumber as drive_number,
    p.playNumber as play_number,
    
    -- Team identifiers
    p.offense,
    p.offenseConference as offense_conference,
    p.offenseScore as offense_score,
    p.defense,
    p.defenseConference as defense_conference,
    p.defenseScore as defense_score,
    
    -- Game situation
    p.period,
    p.down,
    p.distance,
    p.yardline,
    p.yardsToGoal as yards_to_goal,
    p.yardsGained as yards_gained,
    
    -- Play details
    p.playType as play_type,
    p.playText as play_text,
    p.scoring,
    p.ppa, -- Predicted Points Added
    
    -- Calculated play categories
    CASE 
      WHEN p.playType LIKE '%Rush%' OR p.playType LIKE '%Run%' THEN 'Rush'
      WHEN p.playType LIKE '%Pass%' THEN 'Pass'
      WHEN p.playType LIKE '%Punt%' THEN 'Punt'
      WHEN p.playType LIKE '%Field Goal%' OR p.playType LIKE '%FG%' THEN 'Field Goal'
      WHEN p.playType LIKE '%Kickoff%' THEN 'Kickoff'
      WHEN p.playType LIKE '%Timeout%' THEN 'Timeout'
      WHEN p.playType LIKE '%Penalty%' THEN 'Penalty'
      ELSE 'Other'
    END as play_category,
    
    -- Success metrics
    CASE 
      WHEN p.down = 1 AND p.yardsGained >= p.distance * 0.5 THEN 1
      WHEN p.down = 2 AND p.yardsGained >= p.distance * 0.7 THEN 1
      WHEN p.down IN (3, 4) AND p.yardsGained >= p.distance THEN 1
      ELSE 0
    END as successful_play,
    
    CASE 
      WHEN p.yardsGained >= 20 AND p.playType LIKE '%Pass%' THEN 1
      WHEN p.yardsGained >= 12 AND p.playType LIKE '%Rush%' THEN 1
      ELSE 0
    END as explosive_play,
    
    -- Situational context
    CASE 
      WHEN p.yardsToGoal <= 20 THEN 'Red Zone'
      WHEN p.yardsToGoal <= 40 THEN 'Scoring Territory'
      ELSE 'Field'
    END as field_zone,
    
    CASE 
      WHEN p.down = 3 THEN 'Third Down'
      WHEN p.down = 4 THEN 'Fourth Down'
      ELSE 'Early Down'
    END as down_situation,
    
    -- Game context from silver games
    g.season,
    g.week,
    g.game_phase,
    g.margin as final_margin
    
  FROM LIVE.plays_bronze p
  INNER JOIN LIVE.fact_games_silver g ON p.gameId = g.game_id
  WHERE p.gameId IS NOT NULL 
    AND p.id IS NOT NULL
    AND p.playType IS NOT NULL
);