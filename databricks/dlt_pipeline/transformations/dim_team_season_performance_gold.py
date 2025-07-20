# Databricks DLT Pipeline for Team Season Performance - Gold Layer
# File: dim_team_season_performance_gold.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# GOLD LAYER - Complete team performance profiles by season for dashboards
# =============================================================================

@dlt.table(
    name=f"{catalog}.gold.dim_team_season_performance_gold",
    comment="Gold layer - Complete team performance profiles combining advanced and traditional metrics",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "gold"
    }
)
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_fail("valid_team", "team_name IS NOT NULL")
@dlt.expect_or_fail("has_games", "total_games > 0")
def dim_team_season_performance_gold():
    """
    Complete team performance profiles by season for analytics dashboards.
    
    Combines advanced EPA metrics, traditional statistics, game results, and
    contextual performance indicators into a single analytics-ready table.
    """
    
    teams = dlt.read(f"{catalog}.bronze.teams_bronze")
    advanced_stats = dlt.read(f"{catalog}.silver.fact_advanced_season_stats_silver")
    traditional_stats = dlt.read(f"{catalog}.silver.fact_season_stats_silver")
    
    # Calculate game results summary
    games = dlt.read(f"{catalog}.silver.fact_games_silver")
    
    # Home game results
    home_results = (
        games.filter(F.col("home_points").isNotNull() & F.col("away_points").isNotNull())
        .select(
            F.col("season"),
            F.col("home_team_id").alias("team_id"),
            F.col("home_points").alias("points_scored"),
            F.col("away_points").alias("points_allowed"),
            F.when(F.col("home_points") > F.col("away_points"), 1).otherwise(0).alias("wins"),
            F.when(F.col("home_points") < F.col("away_points"), 1).otherwise(0).alias("losses"),
            F.lit(1).alias("home_games"),
            F.lit(0).alias("away_games"),
            F.when(F.col("is_conference_game") == True, 1).otherwise(0).alias("conference_games"),
            F.col("game_competitiveness")
        )
    )
    
    # Away game results
    away_results = (
        games.filter(F.col("home_points").isNotNull() & F.col("away_points").isNotNull())
        .select(
            F.col("season"),
            F.col("away_team_id").alias("team_id"),
            F.col("away_points").alias("points_scored"),
            F.col("home_points").alias("points_allowed"),
            F.when(F.col("away_points") > F.col("home_points"), 1).otherwise(0).alias("wins"),
            F.when(F.col("away_points") < F.col("home_points"), 1).otherwise(0).alias("losses"),
            F.lit(0).alias("home_games"),
            F.lit(1).alias("away_games"),
            F.when(F.col("is_conference_game") == True, 1).otherwise(0).alias("conference_games"),
            F.col("game_competitiveness")
        )
    )
    
    # Combine all game results
    all_results = home_results.union(away_results)
    
    # Aggregate game results by team and season
    team_records = (
        all_results
        .groupBy("season", "team_id")
        .agg(
            F.sum("wins").alias("total_wins"),
            F.sum("losses").alias("total_losses"),
            F.sum("home_games").alias("home_games"),
            F.sum("away_games").alias("away_games"),
            F.sum("conference_games").alias("conference_games"),
            F.sum("points_scored").alias("total_points_scored"),
            F.sum("points_allowed").alias("total_points_allowed"),
            F.avg("points_scored").alias("avg_points_scored"),
            F.avg("points_allowed").alias("avg_points_allowed"),
            F.count("*").alias("total_games"),
            F.sum(F.when(F.col("game_competitiveness") == "Blowout", 1).otherwise(0)).alias("blowout_games"),
            F.sum(F.when(F.col("game_competitiveness") == "Close Game", 1).otherwise(0)).alias("close_games")
        )
    )
    
    return (
        teams.alias("t")
        .join(advanced_stats.alias("adv"), F.col("t.id") == F.col("adv.team_id"), "inner")
        .join(traditional_stats.alias("trad"), 
              (F.col("t.id") == F.col("trad.team_id")) & 
              (F.col("adv.season") == F.col("trad.season")), "inner")
        .join(team_records.alias("rec"),
              (F.col("t.id") == F.col("rec.team_id")) & 
              (F.col("adv.season") == F.col("rec.season")), "inner")
        .select(
            # Team and season identifiers
            F.col("adv.season"),
            F.col("t.id").alias("team_id"),
            F.col("t.school").alias("team_name"),
            F.col("t.mascot"),
            F.col("adv.conference"),
            F.col("t.classification"),
            F.col("t.division"),
            
            # Record and game summary
            F.col("rec.total_wins"),
            F.col("rec.total_losses"),
            F.col("rec.total_games"),
            F.round(F.col("rec.total_wins") / F.col("rec.total_games"), 3).alias("win_percentage"),
            F.col("rec.home_games"),
            F.col("rec.away_games"),
            F.col("rec.conference_games"),
            
            # Scoring summary
            F.round(F.col("rec.avg_points_scored"), 1).alias("avg_points_scored"),
            F.round(F.col("rec.avg_points_allowed"), 1).alias("avg_points_allowed"),
            F.round(F.col("rec.avg_points_scored") - F.col("rec.avg_points_allowed"), 1).alias("avg_point_differential"),
            
            # Game competitiveness
            F.col("rec.close_games"),
            F.col("rec.blowout_games"),
            F.round(F.col("rec.close_games") / F.col("rec.total_games"), 2).alias("close_game_rate"),
            
            # ADVANCED EPA METRICS
            F.col("adv.off_ppa_per_play").alias("offensive_epa_per_play"),
            F.col("adv.def_ppa_per_play_allowed").alias("defensive_epa_per_play"),
            F.col("adv.epa_differential").alias("overall_epa_rating"),
            F.col("adv.offensive_tier").alias("epa_offensive_tier"),
            F.col("adv.defensive_tier").alias("epa_defensive_tier"),
            
            # Explosiveness and efficiency
            F.col("adv.off_overall_explosiveness").alias("offensive_explosiveness"),
            F.col("adv.def_overall_explosiveness_allowed").alias("defensive_explosiveness_allowed"),
            F.col("adv.off_overall_success_rate").alias("offensive_success_rate"),
            F.col("adv.def_overall_success_rate_allowed").alias("defensive_success_rate_allowed"),
            
            # Line play metrics
            F.col("adv.off_line_yards_per_rush").alias("offensive_line_yards"),
            F.col("adv.def_line_yards_per_rush_allowed").alias("defensive_line_yards_allowed"),
            F.col("adv.off_stuff_rate").alias("offensive_stuff_rate"),
            F.col("adv.def_stuff_rate").alias("defensive_stuff_rate"),
            
            # TRADITIONAL METRICS
            F.col("trad.yards_per_game").alias("total_yards_per_game"),
            F.col("trad.yards_allowed_per_game").alias("total_yards_allowed_per_game"),
            F.col("trad.rushing_yards_per_game"),
            F.col("trad.passing_yards_per_game"),
            F.col("trad.turnover_margin_per_game"),
            F.col("trad.third_down_conversion_rate"),
            F.col("trad.third_down_conversion_rate_allowed"),
            
            # PERFORMANCE INDICATORS
            
            # Overall team rating (combines EPA and traditional metrics)
            F.round(
                (F.col("adv.epa_differential") * 0.6) + 
                ((F.col("rec.avg_points_scored") - F.col("rec.avg_points_allowed")) * 0.01) +
                ((F.col("rec.total_wins") / F.col("rec.total_games") - 0.5) * 0.4), 3
            ).alias("composite_team_rating"),
            
            # Strength indicators
            F.when(F.col("adv.epa_differential") >= 0.2, F.lit("Elite"))
             .when(F.col("adv.epa_differential") >= 0.1, F.lit("Very Good"))
             .when(F.col("adv.epa_differential") >= 0.0, F.lit("Above Average"))
             .when(F.col("adv.epa_differential") >= -0.1, F.lit("Below Average"))
             .otherwise(F.lit("Poor")).alias("overall_team_tier"),
            
            # Team style classification
            F.when((F.col("adv.off_overall_explosiveness") >= 1.5) & (F.col("adv.off_overall_success_rate") >= 0.45), F.lit("High-Powered Offense"))
             .when((F.col("adv.off_overall_success_rate") >= 0.45) & (F.col("adv.off_overall_explosiveness") < 1.5), F.lit("Efficient Offense"))
             .when((F.col("adv.off_overall_explosiveness") >= 1.5) & (F.col("adv.off_overall_success_rate") < 0.45), F.lit("Boom-or-Bust Offense"))
             .otherwise(F.lit("Struggling Offense")).alias("offensive_style"),
            
            F.when((F.col("adv.def_stuff_rate") >= 0.25) & (F.col("adv.def_overall_success_rate_allowed") <= 0.4), F.lit("Dominant Defense"))
             .when(F.col("adv.def_overall_success_rate_allowed") <= 0.4, F.lit("Bend-Dont-Break Defense"))
             .when(F.col("adv.def_stuff_rate") >= 0.25, F.lit("Run-Stopping Defense"))
             .otherwise(F.lit("Vulnerable Defense")).alias("defensive_style"),
            
            # Season context
            F.when(F.col("rec.total_wins") / F.col("rec.total_games") >= 0.75, F.lit("Excellent Season"))
             .when(F.col("rec.total_wins") / F.col("rec.total_games") >= 0.6, F.lit("Good Season"))
             .when(F.col("rec.total_wins") / F.col("rec.total_games") >= 0.4, F.lit("Average Season"))
             .otherwise(F.lit("Disappointing Season")).alias("season_assessment")
        )
    )