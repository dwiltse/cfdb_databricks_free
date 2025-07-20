# Databricks DLT Pipeline for Season Stats Data - Silver Layer
# File: fact_season_stats_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - FBS team season statistics with calculated efficiency metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver.fact_season_stats_silver",
    comment="Silver layer - FBS team season statistics with calculated efficiency and performance metrics",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_fail("valid_team", "team_name IS NOT NULL")
@dlt.expect_or_fail("fbs_teams_only", "team_id IS NOT NULL")  # Only teams that exist in FBS teams table
@dlt.expect_or_fail("positive_games", "games > 0")
@dlt.expect_or_fail("reasonable_totals", "total_yards >= 0 AND total_yards_allowed >= 0")
def fact_season_stats_silver():
    """
    Season-aggregated statistics for FBS teams with efficiency metrics.
    
    Filters to FBS teams only and adds calculated performance indicators.
    """
    
    season_stats = dlt.read(f"{catalog}.bronze.season_stats_bronze")
    teams = dlt.read(f"{catalog}.bronze.teams_bronze")
    
    return (
        season_stats.alias("ss")
        .join(
            teams.alias("t").select("id", "school"), 
            F.col("ss.team") == F.col("t.school"), 
            "inner"  # Only include teams that exist in FBS teams table
        )
        .filter(
            (F.col("ss.season").isNotNull()) &
            (F.col("ss.team").isNotNull()) &
            (F.col("ss.games") > 0)
        )
        .select(
            # Primary identifiers
            F.col("ss.season"),
            F.col("t.id").alias("team_id"),
            F.col("ss.team").alias("team_name"),
            F.col("ss.conference"),
            F.col("ss.games"),
            
            # Offensive statistics
            F.col("ss.totalYards").alias("total_yards"),
            F.col("ss.rushingYards").alias("rushing_yards"),
            F.col("ss.netPassingYards").alias("net_passing_yards"),
            F.col("ss.rushingAttempts").alias("rushing_attempts"),
            F.col("ss.passAttempts").alias("pass_attempts"),
            F.col("ss.passCompletions").alias("pass_completions"),
            F.col("ss.passingTDs").alias("passing_tds"),
            F.col("ss.rushingTDs").alias("rushing_tds"),
            F.col("ss.firstDowns").alias("first_downs"),
            
            # Defensive statistics (opponent stats)
            F.col("ss.totalYardsOpponent").alias("total_yards_allowed"),
            F.col("ss.rushingYardsOpponent").alias("rushing_yards_allowed"),
            F.col("ss.netPassingYardsOpponent").alias("net_passing_yards_allowed"),
            F.col("ss.firstDownsOpponent").alias("first_downs_allowed"),
            F.col("ss.passingTDsOpponent").alias("passing_tds_allowed"),
            F.col("ss.rushingTDsOpponent").alias("rushing_tds_allowed"),
            
            # Turnover statistics
            F.col("ss.turnovers"),
            F.col("ss.turnoversOpponent").alias("turnovers_forced"),
            F.col("ss.interceptions"),
            F.col("ss.interceptionsOpponent").alias("interceptions_thrown"),
            F.col("ss.fumblesLost").alias("fumbles_lost"),
            F.col("ss.fumblesLostOpponent").alias("opponent_fumbles_lost"),
            F.col("ss.fumblesRecovered").alias("fumbles_recovered"),
            F.col("ss.fumblesRecoveredOpponent").alias("opponent_fumbles_recovered"),
            
            # Special teams and field position
            F.col("ss.kickReturns").alias("kick_returns"),
            F.col("ss.kickReturnYards").alias("kick_return_yards"),
            F.col("ss.puntReturns").alias("punt_returns"),
            F.col("ss.puntReturnYards").alias("punt_return_yards"),
            
            # Efficiency statistics
            F.col("ss.thirdDownConversions").alias("third_down_conversions"),
            F.col("ss.thirdDowns").alias("third_down_attempts"),
            F.col("ss.thirdDownConversionsOpponent").alias("third_down_conversions_allowed"),
            F.col("ss.thirdDownsOpponent").alias("third_down_attempts_allowed"),
            F.col("ss.fourthDownConversions").alias("fourth_down_conversions"),
            F.col("ss.fourthDowns").alias("fourth_down_attempts"),
            
            # Defensive pressure
            F.col("ss.sacks"),
            F.col("ss.sacksOpponent").alias("sacks_allowed"),
            F.col("ss.tacklesForLoss").alias("tackles_for_loss"),
            F.col("ss.tacklesForLossOpponent").alias("tackles_for_loss_allowed"),
            
            # Penalties
            F.col("ss.penalties"),
            F.col("ss.penaltyYards").alias("penalty_yards"),
            F.col("ss.penaltiesOpponent").alias("opponent_penalties"),
            F.col("ss.penaltyYardsOpponent").alias("opponent_penalty_yards"),
            
            # Time of possession - already in seconds for season stats
            F.col("ss.possessionTime").alias("possession_time_seconds"),
            F.col("ss.possessionTimeOpponent").alias("opponent_possession_time_seconds"),
            
            # Calculated per-game averages
            F.round(F.col("ss.totalYards") / F.col("ss.games"), 1).alias("yards_per_game"),
            F.round(F.col("ss.totalYardsOpponent") / F.col("ss.games"), 1).alias("yards_allowed_per_game"),
            F.round(F.col("ss.rushingYards") / F.col("ss.games"), 1).alias("rushing_yards_per_game"),
            F.round(F.col("ss.netPassingYards") / F.col("ss.games"), 1).alias("passing_yards_per_game"),
            
            # Efficiency metrics
            F.when(F.col("ss.passAttempts") > 0, 
                   F.round(F.col("ss.passCompletions") / F.col("ss.passAttempts"), 3)
            ).otherwise(F.lit(0)).alias("completion_percentage"),
            
            F.when(F.col("ss.rushingAttempts") > 0,
                   F.round(F.col("ss.rushingYards") / F.col("ss.rushingAttempts"), 2)
            ).otherwise(F.lit(0)).alias("yards_per_rush"),
            
            F.when(F.col("ss.passAttempts") > 0,
                   F.round(F.col("ss.netPassingYards") / F.col("ss.passAttempts"), 2)
            ).otherwise(F.lit(0)).alias("yards_per_pass"),
            
            F.when(F.col("ss.thirdDowns") > 0,
                   F.round(F.col("ss.thirdDownConversions") / F.col("ss.thirdDowns"), 3)
            ).otherwise(F.lit(0)).alias("third_down_conversion_rate"),
            
            F.when(F.col("ss.thirdDownsOpponent") > 0,
                   F.round(F.col("ss.thirdDownConversionsOpponent") / F.col("ss.thirdDownsOpponent"), 3)
            ).otherwise(F.lit(0)).alias("third_down_conversion_rate_allowed"),
            
            # Turnover margin
            (F.col("ss.turnoversOpponent") - F.col("ss.turnovers")).alias("turnover_margin"),
            F.round((F.col("ss.turnoversOpponent") - F.col("ss.turnovers")) / F.col("ss.games"), 2).alias("turnover_margin_per_game"),
            
            # Total offensive and defensive efficiency
            F.when(F.col("ss.games") > 0,
                   F.round((F.col("ss.rushingAttempts") + F.col("ss.passAttempts")) / F.col("ss.games"), 1)
            ).otherwise(F.lit(0)).alias("plays_per_game"),
            
            F.when((F.col("ss.rushingAttempts") + F.col("ss.passAttempts")) > 0,
                   F.round(F.col("ss.totalYards") / (F.col("ss.rushingAttempts") + F.col("ss.passAttempts")), 2)
            ).otherwise(F.lit(0)).alias("yards_per_play"),
            
            # Performance categories
            F.when(F.col("ss.totalYards") / F.col("ss.games") >= 450, F.lit("Elite Offense"))
             .when(F.col("ss.totalYards") / F.col("ss.games") >= 375, F.lit("Good Offense"))
             .when(F.col("ss.totalYards") / F.col("ss.games") >= 300, F.lit("Average Offense"))
             .otherwise(F.lit("Below Average Offense")).alias("offensive_tier"),
            
            F.when(F.col("ss.totalYardsOpponent") / F.col("ss.games") <= 300, F.lit("Elite Defense"))
             .when(F.col("ss.totalYardsOpponent") / F.col("ss.games") <= 375, F.lit("Good Defense"))
             .when(F.col("ss.totalYardsOpponent") / F.col("ss.games") <= 450, F.lit("Average Defense"))
             .otherwise(F.lit("Below Average Defense")).alias("defensive_tier")
        )
    )