# Databricks DLT Pipeline for Game Predictions - Gold Layer
# File: fact_game_predictions_gold.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# GOLD LAYER - Game prediction features combining team performance metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.gold.fact_game_predictions_gold",
    comment="Gold layer - Game prediction features with team EPA differentials and performance indicators",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "gold"
    }
)
@dlt.expect_or_fail("valid_game_id", "game_id IS NOT NULL")
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_drop("both_teams_have_stats", "home_team_epa_rating IS NOT NULL AND away_team_epa_rating IS NOT NULL")
def fact_game_predictions_gold():
    """
    Game prediction features combining advanced team performance metrics.
    
    For each game, provides predictive features based on both teams' season performance,
    EPA ratings, recent form, and historical context for machine learning models.
    """
    
    games = dlt.read(f"{catalog}.silver.fact_games_silver")
    advanced_season_stats = dlt.read(f"{catalog}.silver.fact_advanced_season_stats_silver")
    season_stats = dlt.read(f"{catalog}.silver.fact_season_stats_silver")
    
    # Get home team advanced stats
    home_advanced = advanced_season_stats.alias("ha").select(
        F.col("ha.season"),
        F.col("ha.team_id").alias("home_team_id"),
        F.col("ha.off_ppa_per_play").alias("home_off_epa"),
        F.col("ha.def_ppa_per_play_allowed").alias("home_def_epa"),
        F.col("ha.off_overall_explosiveness").alias("home_explosiveness"),
        F.col("ha.off_overall_success_rate").alias("home_success_rate"),
        F.col("ha.defensive_efficiency_ppa").alias("home_def_efficiency"),
        F.col("ha.epa_differential").alias("home_epa_differential"),
        F.col("ha.offensive_tier").alias("home_off_tier"),
        F.col("ha.defensive_tier").alias("home_def_tier")
    )
    
    # Get away team advanced stats  
    away_advanced = advanced_season_stats.alias("aa").select(
        F.col("aa.season"),
        F.col("aa.team_id").alias("away_team_id"),
        F.col("aa.off_ppa_per_play").alias("away_off_epa"),
        F.col("aa.def_ppa_per_play_allowed").alias("away_def_epa"),
        F.col("aa.off_overall_explosiveness").alias("away_explosiveness"),
        F.col("aa.off_overall_success_rate").alias("away_success_rate"),
        F.col("aa.defensive_efficiency_ppa").alias("away_def_efficiency"),
        F.col("aa.epa_differential").alias("away_epa_differential"),
        F.col("aa.offensive_tier").alias("away_off_tier"),
        F.col("aa.defensive_tier").alias("away_def_tier")
    )
    
    # Get home team traditional stats
    home_traditional = season_stats.alias("ht").select(
        F.col("ht.season"),
        F.col("ht.team_id").alias("home_team_id"),
        F.col("ht.yards_per_game").alias("home_yards_per_game"),
        F.col("ht.yards_allowed_per_game").alias("home_yards_allowed_per_game"),
        F.col("ht.turnover_margin_per_game").alias("home_turnover_margin"),
        F.col("ht.third_down_conversion_rate").alias("home_third_down_rate"),
        F.col("ht.offensive_tier").alias("home_traditional_off_tier")
    )
    
    # Get away team traditional stats
    away_traditional = season_stats.alias("at").select(
        F.col("at.season"),
        F.col("at.team_id").alias("away_team_id"),
        F.col("at.yards_per_game").alias("away_yards_per_game"),
        F.col("at.yards_allowed_per_game").alias("away_yards_allowed_per_game"),
        F.col("at.turnover_margin_per_game").alias("away_turnover_margin"),
        F.col("at.third_down_conversion_rate").alias("away_third_down_rate"),
        F.col("at.offensive_tier").alias("away_traditional_off_tier")
    )
    
    return (
        games.alias("g")
        .join(home_advanced.alias("ha"), 
              (F.col("g.season") == F.col("ha.season")) & 
              (F.col("g.home_team_id") == F.col("ha.home_team_id")), "left")
        .join(away_advanced.alias("aa"),
              (F.col("g.season") == F.col("aa.season")) & 
              (F.col("g.away_team_id") == F.col("aa.away_team_id")), "left")
        .join(home_traditional.alias("ht"),
              (F.col("g.season") == F.col("ht.season")) & 
              (F.col("g.home_team_id") == F.col("ht.home_team_id")), "left")
        .join(away_traditional.alias("at"),
              (F.col("g.season") == F.col("at.season")) & 
              (F.col("g.away_team_id") == F.col("at.away_team_id")), "left")
        .filter(
            (F.col("g.season") >= 2014) &  # Only include games with advanced stats
            (F.col("g.home_points").isNotNull()) & 
            (F.col("g.away_points").isNotNull()) &
            (F.col("ha.home_off_epa").isNotNull()) &  # Home team has advanced stats
            (F.col("aa.away_off_epa").isNotNull())    # Away team has advanced stats
        )
        .select(
            # Game context
            F.col("g.game_id"),
            F.col("g.season"),
            F.col("g.week"),
            F.col("g.start_date"),
            F.col("g.home_team_id"),
            F.col("g.away_team_id"),
            F.col("g.home_team"),
            F.col("g.away_team"),
            F.col("g.is_neutral_site"),
            F.col("g.is_conference_game"),
            F.col("g.game_phase"),
            
            # Actual results (for training)
            F.col("g.home_points"),
            F.col("g.away_points"),
            F.col("g.margin"),
            F.col("g.winner_team_id"),
            
            # HOME TEAM FEATURES
            F.round(F.col("ha.home_off_epa"), 4).alias("home_team_epa_rating"),
            F.round(F.col("ha.home_def_epa"), 4).alias("home_team_def_epa_rating"),
            F.round(F.col("ha.home_explosiveness"), 4).alias("home_team_explosiveness"),
            F.round(F.col("ha.home_success_rate"), 4).alias("home_team_success_rate"),
            F.round(F.col("ha.home_epa_differential"), 4).alias("home_team_overall_rating"),
            F.col("ht.home_yards_per_game").alias("home_team_yards_per_game"),
            F.col("ht.home_yards_allowed_per_game").alias("home_team_yards_allowed"),
            F.col("ht.home_turnover_margin").alias("home_team_turnover_margin"),
            F.col("ht.home_third_down_rate").alias("home_team_third_down_rate"),
            
            # AWAY TEAM FEATURES  
            F.round(F.col("aa.away_off_epa"), 4).alias("away_team_epa_rating"),
            F.round(F.col("aa.away_def_epa"), 4).alias("away_team_def_epa_rating"),
            F.round(F.col("aa.away_explosiveness"), 4).alias("away_team_explosiveness"),
            F.round(F.col("aa.away_success_rate"), 4).alias("away_team_success_rate"),
            F.round(F.col("aa.away_epa_differential"), 4).alias("away_team_overall_rating"),
            F.col("at.away_yards_per_game").alias("away_team_yards_per_game"),
            F.col("at.away_yards_allowed_per_game").alias("away_team_yards_allowed"),
            F.col("at.away_turnover_margin").alias("away_team_turnover_margin"),
            F.col("at.away_third_down_rate").alias("away_team_third_down_rate"),
            
            # MATCHUP DIFFERENTIALS (Key prediction features)
            F.round(F.col("ha.home_off_epa") - F.col("aa.away_def_epa"), 4).alias("home_offense_vs_away_defense"),
            F.round(F.col("aa.away_off_epa") - F.col("ha.home_def_epa"), 4).alias("away_offense_vs_home_defense"),
            F.round(F.col("ha.home_epa_differential") - F.col("aa.away_epa_differential"), 4).alias("overall_team_rating_differential"),
            F.round(F.col("ha.home_explosiveness") - F.col("aa.away_explosiveness"), 4).alias("explosiveness_differential"),
            F.round(F.col("ha.home_success_rate") - F.col("aa.away_success_rate"), 4).alias("success_rate_differential"),
            
            # SITUATIONAL FACTORS
            F.when(F.col("g.is_neutral_site") == True, F.lit(0)).otherwise(F.lit(3)).alias("home_field_advantage_points"),
            F.when(F.col("g.is_conference_game") == True, F.lit(1)).otherwise(F.lit(0)).alias("conference_game_flag"),
            
            # PREDICTION CONFIDENCE INDICATORS
            F.abs(F.col("ha.home_epa_differential") - F.col("aa.away_epa_differential")).alias("rating_gap"),
            F.when(F.abs(F.col("ha.home_epa_differential") - F.col("aa.away_epa_differential")) >= 0.3, F.lit("High Confidence"))
             .when(F.abs(F.col("ha.home_epa_differential") - F.col("aa.away_epa_differential")) >= 0.15, F.lit("Medium Confidence"))
             .otherwise(F.lit("Low Confidence")).alias("prediction_confidence"),
            
            # TIER MATCHUP ANALYSIS
            F.concat_ws(" vs ", F.col("ha.home_off_tier"), F.col("aa.away_def_tier")).alias("offense_defense_matchup"),
            F.when((F.col("ha.home_off_tier") == "Elite Offense") & (F.col("aa.away_def_tier") == "Below Average Defense"), F.lit("Favorable"))
             .when((F.col("ha.home_off_tier") == "Below Average Offense") & (F.col("aa.away_def_tier") == "Elite Defense"), F.lit("Unfavorable"))
             .otherwise(F.lit("Neutral")).alias("home_matchup_advantage"),
            
            # GAME TYPE CLASSIFICATION
            F.when(F.col("g.game_phase") == "Playoff", F.lit("High Stakes"))
             .when(F.col("g.is_conference_game") == True, F.lit("Conference"))
             .when(F.col("g.week") <= 4, F.lit("Early Season"))
             .when(F.col("g.week") >= 12, F.lit("Late Season"))
             .otherwise(F.lit("Mid Season")).alias("game_importance")
        )
    )