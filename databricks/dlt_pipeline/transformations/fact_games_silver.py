# Databricks DLT Pipeline for Games Data - Silver Layer
# File: fact_games_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - FBS game results with calculated performance metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver.fact_games_silver",
    comment="Silver layer - FBS game results with calculated performance metrics",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_game_id", "game_id IS NOT NULL")
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_fail("fbs_teams_only", "home_classification = 'fbs' OR away_classification = 'fbs'")
@dlt.expect_or_fail("completed_games", "home_points IS NOT NULL AND away_points IS NOT NULL")
@dlt.expect_or_fail("valid_scores", "home_points >= 0 AND away_points >= 0")
def fact_games_silver():
    """
    Core FBS game results with calculated metrics for analytics.
    
    Filters to FBS-involved games only and adds performance indicators.
    """
    
    return (
        dlt.read(f"{catalog}.bronze.games_bronze")
        .filter(
            (F.col("home_classification") == "fbs") | (F.col("away_classification") == "fbs")
        )
        .filter(
            (F.col("home_points").isNotNull()) & 
            (F.col("away_points").isNotNull()) &
            (F.col("id").isNotNull())
        )
        .select(
            # Primary identifiers
            F.col("id").alias("game_id"),
            "season",
            "week", 
            "start_date",
            
            # Team identifiers
            "home_team_id",
            "away_team_id",
            "home_team",
            "away_team",
            
            # Scores and calculated metrics
            "home_points",
            "away_points",
            F.abs(F.col("home_points") - F.col("away_points")).alias("margin"),
            (F.col("home_points") + F.col("away_points")).alias("total_score"),
            
            # Game characteristics
            F.when(F.col("week") > 15, "Postseason")
             .when(F.col("week") >= 14, "Late Season")
             .otherwise("Regular Season").alias("game_phase"),
            
            F.when(F.abs(F.col("home_points") - F.col("away_points")) <= 3, "Close")
             .when(F.abs(F.col("home_points") - F.col("away_points")) <= 14, "Moderate")
             .otherwise("Blowout").alias("game_competitiveness"),
            
            F.col("neutral_site").alias("is_neutral_site"),
            F.col("conference_game").alias("is_conference_game"),
            
            # Conference and classification
            "home_conference",
            "away_conference", 
            "home_classification",
            "away_classification",
            
            # Venue and attendance
            "venue_id",
            "attendance",
            
            # Advanced metrics
            "excitement",
            "home_postgame_win_prob",
            "away_postgame_win_prob",
            "home_start_elo",
            "home_end_elo",
            "away_start_elo",
            "away_end_elo",
            
            # Derived date fields
            F.to_date("start_date").alias("game_date"),
            F.dayofweek("start_date").alias("day_of_week"),
            F.month("start_date").alias("game_month"),
            
            # Winner identification
            F.when(F.col("home_points") > F.col("away_points"), F.col("home_team_id"))
             .when(F.col("away_points") > F.col("home_points"), F.col("away_team_id"))
             .otherwise(F.lit(None)).alias("winner_team_id"),
            
            F.when(F.col("home_points") > F.col("away_points"), F.lit("home"))
             .when(F.col("away_points") > F.col("home_points"), F.lit("away"))
             .otherwise(F.lit("tie")).alias("winner_location")
        )
    )