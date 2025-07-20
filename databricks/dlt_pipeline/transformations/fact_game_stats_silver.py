# Databricks DLT Pipeline for Game Stats Data - Silver Layer
# File: fact_game_stats_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - Team statistics per game for FBS teams with efficiency metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver.fact_game_stats_silver",
    comment="Silver layer - Team statistics per game for FBS teams with calculated efficiency metrics",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_game_id", "game_id IS NOT NULL")
@dlt.expect_or_fail("valid_team_id", "team_id IS NOT NULL")
@dlt.expect_or_fail("valid_home_away", "home_away IN ('home', 'away')")
@dlt.expect_or_fail("valid_total_yards", "total_yards >= 0")
def fact_game_stats_silver():
    """
    Team performance statistics per game for FBS teams.
    
    Only includes stats from games involving FBS teams with calculated efficiency metrics.
    """
    
    game_stats = dlt.read(f"{catalog}.bronze.game_stats_bronze")
    games = dlt.read(f"{catalog}.silver.fact_games_silver")
    
    return (
        game_stats.alias("gs")
        .join(games.alias("g"), F.col("gs.game_id") == F.col("g.game_id"), "inner")
        .filter(
            (F.col("gs.game_id").isNotNull()) &
            (F.col("gs.team_id").isNotNull()) &
            (F.col("gs.team").isNotNull())
        )
        .select(
            # Primary identifiers
            F.col("gs.game_id"),
            F.col("gs.team_id"),
            F.col("gs.team"),
            F.col("gs.opponent_id"),
            F.col("gs.opponent"),
            F.col("gs.home_away"),
            
            # Game context
            F.col("gs.season"),
            F.col("gs.week"),
            F.col("gs.season_type"),
            F.col("gs.conference"),
            F.col("gs.opponent_conference"),
            
            # Core offensive stats
            F.col("gs.totalYards").alias("total_yards"),
            F.col("gs.rushingYards").alias("rushing_yards"),
            F.col("gs.netPassingYards").alias("net_passing_yards"),
            F.col("gs.rushingAttempts").alias("rushing_attempts"),
            F.col("gs.firstDowns").alias("first_downs"),
            
            # Efficiency metrics
            F.col("gs.yardsPerPass").alias("yards_per_pass"),
            F.col("gs.yardsPerRushAttempt").alias("yards_per_rush"),
            
            # Passing stats
            F.col("gs.completionAttempts"),
            F.col("gs.passingTDs").alias("passing_tds"),
            F.col("gs.passesIntercepted").alias("passes_intercepted"),
            
            # Rushing stats
            F.col("gs.rushingTDs").alias("rushing_tds"),
            
            # Defensive stats
            F.col("gs.sacks"),
            F.col("gs.tackles"),
            F.col("gs.tacklesForLoss").alias("tackles_for_loss"),
            F.col("gs.passesDeflected").alias("passes_deflected"),
            F.col("gs.interceptions"),
            F.col("gs.interceptionYards").alias("interception_yards"),
            F.col("gs.interceptionTDs").alias("interception_tds"),
            
            # Special teams
            F.col("gs.kickReturns").alias("kick_returns"),
            F.col("gs.kickReturnYards").alias("kick_return_yards"),
            F.col("gs.kickReturnTDs").alias("kick_return_tds"),
            F.col("gs.puntReturns").alias("punt_returns"),
            F.col("gs.puntReturnYards").alias("punt_return_yards"),
            F.col("gs.puntReturnTDs").alias("punt_return_tds"),
            
            # Situational efficiency
            F.col("gs.thirdDownEff").alias("third_down_efficiency"),
            F.col("gs.fourthDownEff").alias("fourth_down_efficiency"),
            
            # Turnovers and penalties
            F.col("gs.turnovers"),
            F.col("gs.fumblesLost").alias("fumbles_lost"),
            F.col("gs.fumblesRecovered").alias("fumbles_recovered"),
            F.col("gs.totalFumbles").alias("total_fumbles"),
            F.col("gs.totalPenaltiesYards").alias("total_penalties_yards"),
            
            # Time management
            F.col("gs.possessionTime").alias("possession_time_raw"),
            # Convert possession time from "MM:SS" to total seconds
            F.when(
                F.col("gs.possessionTime").isNotNull() & F.col("gs.possessionTime").contains(":"),
                (F.split(F.col("gs.possessionTime"), ":")[0].cast("int") * 60) + 
                F.split(F.col("gs.possessionTime"), ":")[1].cast("int")
            ).otherwise(F.lit(None)).alias("possession_time_seconds"),
            
            # Game context from silver games
            F.col("g.margin").alias("final_margin"),
            F.col("g.game_competitiveness"),
            F.col("g.is_conference_game"),
            F.col("g.game_phase")
        )
    )