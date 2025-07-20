-- Databricks DLT Pipeline - Silver Layer
-- File: agg_team_season_stats_silver.sql

-- Aggregated team performance by season for prediction modeling
CREATE OR REFRESH MATERIALIZED VIEW LIVE.agg_team_season_stats_silver (
  CONSTRAINT valid_team_id EXPECT (team_id IS NOT NULL),
  CONSTRAINT valid_season EXPECT (season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1),
  CONSTRAINT games_played_check EXPECT (games_played > 0),
  CONSTRAINT valid_record EXPECT (wins + losses = games_played)
)
COMMENT "Silver layer - Season-aggregated team statistics for FBS teams with efficiency metrics"
TBLPROPERTIES (
  "delta.autoOptimize.optimizeWrite" = "true",
  "delta.autoOptimize.autoCompact" = "true",
  "pipelines.autoOptimize.managed" = "true"
)
AS (
  WITH team_games AS (
    -- Get all games for each team with standardized team perspective
    SELECT 
      g.season,
      CASE WHEN g.home_team_id = t.id THEN g.home_team_id ELSE g.away_team_id END as team_id,
      CASE WHEN g.home_team_id = t.id THEN g.home_team ELSE g.away_team END as team_name,
      CASE WHEN g.home_team_id = t.id THEN g.home_conference ELSE g.away_conference END as conference,
      
      -- Team's perspective: points scored and allowed
      CASE WHEN g.home_team_id = t.id THEN g.home_points ELSE g.away_points END as points_scored,
      CASE WHEN g.home_team_id = t.id THEN g.away_points ELSE g.home_points END as points_allowed,
      
      -- Win/loss from team's perspective
      CASE 
        WHEN (g.home_team_id = t.id AND g.home_points > g.away_points) OR 
             (g.away_team_id = t.id AND g.away_points > g.home_points) 
        THEN 1 ELSE 0 
      END as win,
      
      -- Home/away indicator
      CASE WHEN g.home_team_id = t.id THEN 1 ELSE 0 END as home_game,
      
      -- Game characteristics
      g.is_conference_game,
      g.game_competitiveness,
      g.margin
      
    FROM LIVE.fact_games_silver g
    CROSS JOIN (SELECT DISTINCT home_team_id as id FROM LIVE.fact_games_silver 
               UNION 
               SELECT DISTINCT away_team_id as id FROM LIVE.fact_games_silver) t
    WHERE (g.home_team_id = t.id OR g.away_team_id = t.id)
  ),
  
  season_stats AS (
    -- Aggregate team statistics by season
    SELECT 
      tg.season,
      tg.team_id,
      tg.team_name,
      tg.conference,
      
      -- Basic record
      COUNT(*) as games_played,
      SUM(tg.win) as wins,
      COUNT(*) - SUM(tg.win) as losses,
      ROUND(SUM(tg.win) / COUNT(*), 3) as win_percentage,
      
      -- Scoring statistics
      ROUND(AVG(tg.points_scored), 1) as avg_points_scored,
      ROUND(AVG(tg.points_allowed), 1) as avg_points_allowed,
      ROUND(AVG(tg.points_scored - tg.points_allowed), 1) as avg_point_differential,
      
      SUM(tg.points_scored) as total_points_scored,
      SUM(tg.points_allowed) as total_points_allowed,
      
      -- Game type breakdowns
      SUM(CASE WHEN tg.is_conference_game THEN tg.win ELSE 0 END) as conference_wins,
      SUM(CASE WHEN tg.is_conference_game THEN 1 ELSE 0 END) as conference_games,
      SUM(CASE WHEN tg.home_game = 1 THEN tg.win ELSE 0 END) as home_wins,
      SUM(CASE WHEN tg.home_game = 1 THEN 1 ELSE 0 END) as home_games,
      SUM(CASE WHEN tg.home_game = 0 THEN tg.win ELSE 0 END) as away_wins,
      SUM(CASE WHEN tg.home_game = 0 THEN 1 ELSE 0 END) as away_games,
      
      -- Competitiveness metrics
      SUM(CASE WHEN tg.game_competitiveness = 'Close' THEN 1 ELSE 0 END) as close_games,
      SUM(CASE WHEN tg.game_competitiveness = 'Close' AND tg.win = 1 THEN 1 ELSE 0 END) as close_game_wins,
      SUM(CASE WHEN tg.game_competitiveness = 'Blowout' AND tg.win = 1 THEN 1 ELSE 0 END) as blowout_wins,
      
      -- Margin analysis
      MAX(tg.margin) as largest_margin_victory,
      STDDEV(tg.points_scored) as scoring_consistency,
      STDDEV(tg.points_allowed) as defensive_consistency
      
    FROM team_games tg
    GROUP BY tg.season, tg.team_id, tg.team_name, tg.conference
  )
  
  SELECT 
    ss.*,
    
    -- Calculated efficiency metrics
    CASE 
      WHEN ss.conference_games > 0 
      THEN ROUND(ss.conference_wins / ss.conference_games, 3) 
      ELSE 0 
    END as conference_win_percentage,
    
    CASE 
      WHEN ss.home_games > 0 
      THEN ROUND(ss.home_wins / ss.home_games, 3) 
      ELSE 0 
    END as home_win_percentage,
    
    CASE 
      WHEN ss.away_games > 0 
      THEN ROUND(ss.away_wins / ss.away_games, 3) 
      ELSE 0 
    END as away_win_percentage,
    
    CASE 
      WHEN ss.close_games > 0 
      THEN ROUND(ss.close_game_wins / ss.close_games, 3) 
      ELSE 0 
    END as close_game_win_percentage,
    
    -- Performance tier classification
    CASE 
      WHEN ss.win_percentage >= 0.75 THEN 'Elite'
      WHEN ss.win_percentage >= 0.60 THEN 'Good'
      WHEN ss.win_percentage >= 0.45 THEN 'Average'
      ELSE 'Below Average'
    END as performance_tier
    
  FROM season_stats ss
);