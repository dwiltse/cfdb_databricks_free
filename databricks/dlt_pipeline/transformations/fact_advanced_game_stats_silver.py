# Databricks DLT Pipeline for Advanced Game Stats Data - Silver Layer
# File: fact_advanced_game_stats_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - FBS team advanced game statistics with EPA and efficiency metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver.fact_advanced_game_stats_silver",
    comment="Silver layer - FBS team advanced game statistics with EPA, explosiveness, and success rates per game",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_game_id", "game_id IS NOT NULL")
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_fail("valid_team", "team IS NOT NULL")
@dlt.expect_or_fail("fbs_games_only", "game_id IS NOT NULL")  # Links to FBS games through fact_games_silver
def fact_advanced_game_stats_silver():
    """
    Advanced game-level statistics for FBS teams with pre-calculated EPA, explosiveness, and efficiency metrics.
    
    Contains 61 columns of sophisticated per-game analytics including Expected Points Added,
    success rates, explosiveness, line yards, and defensive efficiency measures.
    """
    
    advanced_game_stats = dlt.read(f"{catalog}.bronze.advanced_game_stats_bronze")
    games = dlt.read(f"{catalog}.silver.fact_games_silver")
    
    return (
        advanced_game_stats.alias("ags")
        .join(games.alias("g"), F.col("ags.gameId") == F.col("g.game_id"), "inner")
        .filter(
            F.col("ags.gameId").isNotNull() &
            F.col("ags.team").isNotNull() &
            F.col("ags.season").isNotNull()
        )
        .select(
            # Primary identifiers
            F.col("ags.gameId").alias("game_id"),
            F.col("ags.season"),
            F.col("ags.week"),
            F.col("ags.team").alias("team_name"),
            F.col("ags.opponent").alias("opponent_name"),
            
            # OFFENSIVE PASSING METRICS
            F.col("ags.offense_passingPlays_explosiveness").alias("off_pass_explosiveness"),
            F.col("ags.offense_passingPlays_successRate").alias("off_pass_success_rate"),
            F.col("ags.offense_passingPlays_totalPPA").alias("off_pass_total_ppa"),
            F.col("ags.offense_passingPlays_ppa").alias("off_pass_ppa_per_play"),
            
            # OFFENSIVE RUSHING METRICS
            F.col("ags.offense_rushingPlays_explosiveness").alias("off_rush_explosiveness"),
            F.col("ags.offense_rushingPlays_successRate").alias("off_rush_success_rate"),
            F.col("ags.offense_rushingPlays_totalPPA").alias("off_rush_total_ppa"),
            F.col("ags.offense_rushingPlays_ppa").alias("off_rush_ppa_per_play"),
            
            # OFFENSIVE OVERALL METRICS
            F.col("ags.offense_explosiveness").alias("off_overall_explosiveness"),
            F.col("ags.offense_successRate").alias("off_overall_success_rate"),
            F.col("ags.offense_totalPPA").alias("off_total_ppa"),
            F.col("ags.offense_ppa").alias("off_ppa_per_play"),
            
            # OFFENSIVE LINE METRICS
            F.col("ags.offense_lineYardsTotal").alias("off_line_yards_total"),
            F.col("ags.offense_lineYards").alias("off_line_yards_per_rush"),
            F.col("ags.offense_stuffRate").alias("off_stuff_rate"),
            F.col("ags.offense_powerSuccess").alias("off_power_success_rate"),
            
            # DEFENSIVE PASSING METRICS
            F.col("ags.defense_passingPlays_explosiveness").alias("def_pass_explosiveness_allowed"),
            F.col("ags.defense_passingPlays_successRate").alias("def_pass_success_rate_allowed"),
            F.col("ags.defense_passingPlays_totalPPA").alias("def_pass_total_ppa_allowed"),
            F.col("ags.defense_passingPlays_ppa").alias("def_pass_ppa_per_play_allowed"),
            
            # DEFENSIVE RUSHING METRICS
            F.col("ags.defense_rushingPlays_explosiveness").alias("def_rush_explosiveness_allowed"),
            F.col("ags.defense_rushingPlays_successRate").alias("def_rush_success_rate_allowed"),
            F.col("ags.defense_rushingPlays_totalPPA").alias("def_rush_total_ppa_allowed"),
            F.col("ags.defense_rushingPlays_ppa").alias("def_rush_ppa_per_play_allowed"),
            
            # DEFENSIVE OVERALL METRICS
            F.col("ags.defense_explosiveness").alias("def_overall_explosiveness_allowed"),
            F.col("ags.defense_successRate").alias("def_overall_success_rate_allowed"),
            F.col("ags.defense_totalPPA").alias("def_total_ppa_allowed"),
            F.col("ags.defense_ppa").alias("def_ppa_per_play_allowed"),
            
            # DEFENSIVE LINE METRICS
            F.col("ags.defense_lineYardsTotal").alias("def_line_yards_total_allowed"),
            F.col("ags.defense_lineYards").alias("def_line_yards_per_rush_allowed"),
            F.col("ags.defense_stuffRate").alias("def_stuff_rate"),
            F.col("ags.defense_powerSuccess").alias("def_power_success_rate_allowed"),
            
            # VOLUME METRICS
            F.col("ags.defense_drives").alias("defensive_drives_faced"),
            F.col("ags.defense_plays").alias("defensive_plays_faced"),
            
            # GAME-LEVEL CALCULATED METRICS
            
            # Game efficiency scores
            F.round(F.col("ags.offense_ppa"), 4).alias("game_offensive_efficiency"),
            F.round(F.col("ags.defense_ppa"), 4).alias("game_defensive_efficiency"),
            
            # Game-level differentials
            F.round(
                F.col("ags.offense_explosiveness") - F.col("ags.defense_explosiveness"), 4
            ).alias("game_explosiveness_differential"),
            
            F.round(
                F.col("ags.offense_successRate") - F.col("ags.defense_successRate"), 4
            ).alias("game_success_rate_differential"),
            
            F.round(
                F.col("ags.offense_ppa") - F.col("ags.defense_ppa"), 4
            ).alias("game_epa_differential"),
            
            # Performance indicators for this game
            F.when(F.col("ags.offense_ppa") >= 0.3, F.lit("Dominant"))
             .when(F.col("ags.offense_ppa") >= 0.1, F.lit("Good"))
             .when(F.col("ags.offense_ppa") >= -0.1, F.lit("Average"))
             .otherwise(F.lit("Poor")).alias("game_offensive_performance"),
            
            F.when(F.col("ags.defense_ppa") <= -0.1, F.lit("Dominant"))
             .when(F.col("ags.defense_ppa") <= 0.1, F.lit("Good"))
             .when(F.col("ags.defense_ppa") <= 0.3, F.lit("Average"))
             .otherwise(F.lit("Poor")).alias("game_defensive_performance"),
            
            # Context from games silver
            F.col("g.margin").alias("final_margin"),
            F.col("g.game_competitiveness"),
            F.col("g.is_conference_game"),
            F.col("g.game_phase"),
            F.col("g.winner_team_id"),
            
            # Advanced situational metrics
            F.when(F.col("ags.offense_explosiveness") >= 1.5, F.lit(1)).otherwise(F.lit(0)).alias("explosive_offense_game"),
            F.when(F.col("ags.defense_stuffRate") >= 0.25, F.lit(1)).otherwise(F.lit(0)).alias("dominant_run_defense_game"),
            F.when(F.col("ags.offense_successRate") >= 0.45, F.lit(1)).otherwise(F.lit(0)).alias("efficient_offense_game"),
            
            # EPA performance tiers for quick filtering
            F.when(F.col("ags.offense_ppa") >= 0.2, F.lit("Top Tier"))
             .when(F.col("ags.offense_ppa") >= 0.0, F.lit("Above Average"))
             .when(F.col("ags.offense_ppa") >= -0.2, F.lit("Below Average"))
             .otherwise(F.lit("Bottom Tier")).alias("offensive_epa_tier"),
            
            F.when(F.col("ags.defense_ppa") <= -0.2, F.lit("Top Tier"))
             .when(F.col("ags.defense_ppa") <= 0.0, F.lit("Above Average"))
             .when(F.col("ags.defense_ppa") <= 0.2, F.lit("Below Average"))
             .otherwise(F.lit("Bottom Tier")).alias("defensive_epa_tier")
        )
    )