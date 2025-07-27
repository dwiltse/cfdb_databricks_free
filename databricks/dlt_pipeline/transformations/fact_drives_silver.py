# Databricks DLT Pipeline for Drives Data - Silver Layer
# File: fact_drives_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - Drive details for FBS games with calculated metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver_clean.drives",
    comment="Silver layer - Drive details for FBS games with calculated metrics",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_game_id", "game_id IS NOT NULL")
@dlt.expect_or_fail("valid_drive_id", "drive_id IS NOT NULL")
@dlt.expect_or_fail("valid_drive_number", "drive_number >= 1")
@dlt.expect_or_fail("valid_teams", "offense IS NOT NULL AND defense IS NOT NULL")
def drives():
    """
    Drive-level details linked to FBS games with performance metrics.
    
    Only includes drives from games involving FBS teams.
    """
    
    drives = dlt.read(f"{catalog}.bronze_raw.drives")
    games = dlt.read(f"{catalog}.silver_clean.games")
    
    return (
        drives.alias("d")
        .join(games.alias("g"), F.col("d.gameId") == F.col("g.game_id"), "inner")
        .filter((F.col("d.gameId").isNotNull()) & (F.col("d.id").isNotNull()))
        .select(
            # Primary identifiers
            F.col("d.gameId").alias("game_id"),
            F.col("d.id").alias("drive_id"),
            F.col("d.driveNumber").alias("drive_number"),
            
            # Team identifiers
            F.col("d.offense"),
            F.col("d.offenseConference").alias("offense_conference"),
            F.col("d.defense"),
            F.col("d.defenseConference").alias("defense_conference"),
            
            # Drive characteristics
            F.col("d.scoring"),
            F.col("d.plays"),
            F.col("d.yards"),
            F.col("d.driveResult").alias("drive_result"),
            F.col("d.isHomeOffense").alias("is_home_offense"),
            
            # Field position
            F.col("d.startPeriod").alias("start_period"),
            F.col("d.startYardline").alias("start_yardline"),
            F.col("d.startYardsToGoal").alias("start_yards_to_goal"),
            F.col("d.endPeriod").alias("end_period"),
            F.col("d.endYardline").alias("end_yardline"),
            F.col("d.endYardsToGoal").alias("end_yards_to_goal"),
            
            # Score progression
            F.col("d.startOffenseScore").alias("start_offense_score"),
            F.col("d.startDefenseScore").alias("start_defense_score"),
            F.col("d.endOffenseScore").alias("end_offense_score"),
            F.col("d.endDefenseScore").alias("end_defense_score"),
            
            # Calculated metrics
            F.when(F.col("d.plays") > 0, F.col("d.yards") / F.col("d.plays"))
             .otherwise(F.lit(0)).alias("yards_per_play"),
            
            F.when(
                F.col("d.startYardsToGoal").isNotNull() & F.col("d.endYardsToGoal").isNotNull(),
                F.col("d.startYardsToGoal") - F.col("d.endYardsToGoal")
            ).otherwise(F.col("d.yards")).alias("net_field_position_gain"),
            
            F.when(F.col("d.driveResult").isin(["TD", "TOUCHDOWN"]), F.lit("Touchdown"))
             .when(F.col("d.driveResult").isin(["FG", "FIELD GOAL"]), F.lit("Field Goal"))
             .when(F.col("d.driveResult") == "PUNT", F.lit("Punt"))
             .when(F.col("d.driveResult") == "DOWNS", F.lit("Turnover on Downs"))
             .when(F.col("d.driveResult").isin(["INT", "INTERCEPTION"]), F.lit("Interception"))
             .when(F.col("d.driveResult").isin(["FUMBLE", "LOST FUMBLE"]), F.lit("Fumble"))
             .otherwise(F.lit("Other")).alias("drive_outcome_category"),
            
            # Game context from silver games
            F.col("g.season"),
            F.col("g.week"),
            F.col("g.game_phase")
        )
    )