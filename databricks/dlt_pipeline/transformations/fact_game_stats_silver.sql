-- Databricks DLT Pipeline - Silver Layer
-- File: fact_game_stats_silver.sql

-- Team performance statistics per game for FBS teams
CREATE OR REFRESH MATERIALIZED VIEW LIVE.fact_game_stats_silver (
  CONSTRAINT valid_game_id EXPECT (game_id IS NOT NULL),
  CONSTRAINT valid_team_id EXPECT (team_id IS NOT NULL),
  CONSTRAINT valid_home_away EXPECT (home_away IN ('home', 'away')),
  CONSTRAINT non_negative_stats EXPECT (totalYards >= 0 AND rushingYards >= 0)
)
COMMENT "Silver layer - Team statistics per game for FBS teams with calculated efficiency metrics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  SELECT 
    -- Primary identifiers
    gs.game_id,
    gs.team_id,
    gs.team,
    gs.opponent_id,
    gs.opponent,
    gs.home_away,
    
    -- Game context
    gs.season,
    gs.week,
    gs.season_type,
    gs.conference,
    gs.opponent_conference,
    
    -- Core offensive stats
    gs.totalYards as total_yards,
    gs.rushingYards as rushing_yards,
    gs.netPassingYards as net_passing_yards,
    gs.rushingAttempts as rushing_attempts,
    gs.firstDowns as first_downs,
    
    -- Efficiency metrics
    gs.yardsPerPass as yards_per_pass,
    gs.yardsPerRushAttempt as yards_per_rush,
    CASE 
      WHEN gs.rushingAttempts + CAST(SPLIT(gs.completionAttempts, '-')[1] AS INT) > 0 
      THEN gs.totalYards / (gs.rushingAttempts + CAST(SPLIT(gs.completionAttempts, '-')[1] AS INT))
      ELSE 0
    END as yards_per_play,
    
    -- Passing stats
    gs.completionAttempts,
    CASE 
      WHEN gs.completionAttempts IS NOT NULL AND SPLIT(gs.completionAttempts, '-')[1] != '0'
      THEN CAST(SPLIT(gs.completionAttempts, '-')[0] AS DOUBLE) / CAST(SPLIT(gs.completionAttempts, '-')[1] AS DOUBLE)
      ELSE 0
    END as completion_percentage,
    
    gs.passingTDs as passing_tds,
    gs.passesIntercepted as passes_intercepted,
    
    -- Rushing stats
    gs.rushingTDs as rushing_tds,
    
    -- Defensive stats
    gs.sacks,
    gs.tackles,
    gs.tacklesForLoss as tackles_for_loss,
    gs.passesDeflected as passes_deflected,
    gs.interceptions,
    gs.interceptionYards as interception_yards,
    gs.interceptionTDs as interception_tds,
    
    -- Special teams
    gs.kickReturns as kick_returns,
    gs.kickReturnYards as kick_return_yards,
    gs.kickReturnTDs as kick_return_tds,
    gs.puntReturns as punt_returns,
    gs.puntReturnYards as punt_return_yards,
    gs.puntReturnTDs as punt_return_tds,
    
    -- Situational efficiency
    gs.thirdDownEff as third_down_efficiency,
    gs.fourthDownEff as fourth_down_efficiency,
    
    -- Turnovers and penalties
    gs.turnovers,
    gs.fumblesLost as fumbles_lost,
    gs.fumblesRecovered as fumbles_recovered,
    gs.totalFumbles as total_fumbles,
    gs.totalPenaltiesYards as total_penalties_yards,
    
    -- Time management
    gs.possessionTime as possession_time,
    
    -- Calculated team efficiency scores
    CASE 
      WHEN gs.totalYards > 0 AND gs.turnovers >= 0 
      THEN (gs.totalYards - (gs.turnovers * 50)) / gs.totalYards
      ELSE 0
    END as offensive_efficiency_score,
    
    -- Game context from silver games
    g.margin as final_margin,
    g.game_competitiveness,
    g.is_conference_game,
    g.game_phase
    
  FROM LIVE.game_stats_bronze gs
  INNER JOIN LIVE.fact_games_silver g ON gs.game_id = g.game_id
  WHERE gs.game_id IS NOT NULL 
    AND gs.team_id IS NOT NULL
    AND gs.team IS NOT NULL
);