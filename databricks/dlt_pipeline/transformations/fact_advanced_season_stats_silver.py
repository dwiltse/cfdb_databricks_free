# Databricks DLT Pipeline for Advanced Season Stats Data - Silver Layer
# File: fact_advanced_season_stats_silver.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters - Configure catalog in your DLT pipeline settings
catalog = spark.conf.get("catalog", "cfdb_dev")  # Default to 'cfdb_dev' if not specified

# =============================================================================
# SILVER LAYER - FBS team advanced season statistics with EPA and efficiency metrics
# =============================================================================

@dlt.table(
    name=f"{catalog}.silver.fact_advanced_season_stats_silver",
    comment="Silver layer - FBS team advanced season statistics with EPA, explosiveness, and success rates",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "silver"
    }
)
@dlt.expect_or_fail("valid_season", "season >= 2000 AND season <= YEAR(CURRENT_DATE()) + 1")
@dlt.expect_or_fail("valid_team", "team IS NOT NULL")
@dlt.expect_or_fail("fbs_teams_only", "team_id IS NOT NULL")  # Only teams that exist in FBS teams table
@dlt.expect_or_fail("valid_epa", "offense_passingPlays_ppa IS NOT NULL OR offense_rushingPlays_ppa IS NOT NULL")
def fact_advanced_season_stats_silver():
    """
    Advanced season-level statistics for FBS teams with pre-calculated EPA, explosiveness, and efficiency metrics.
    
    Contains 82 columns of sophisticated analytics including Expected Points Added,
    success rates, explosiveness, line yards, and defensive efficiency measures.
    """
    
    advanced_stats = dlt.read(f"{catalog}.bronze.advanced_season_stats_bronze")
    teams = dlt.read(f"{catalog}.bronze.teams_bronze")
    
    return (
        advanced_stats.alias("ads")
        .join(
            teams.alias("t").select("id", "school"), 
            F.col("ads.team") == F.col("t.school"), 
            "inner"  # Only include teams that exist in FBS teams table
        )
        .filter(
            (F.col("ads.season").isNotNull()) &
            (F.col("ads.team").isNotNull())
        )
        .select(
            # Primary identifiers
            F.col("ads.season"),
            F.col("t.id").alias("team_id"),
            F.col("ads.team").alias("team_name"),
            F.col("ads.conference"),
            
            # OFFENSIVE PASSING METRICS
            F.col("ads.offense_passingPlays_explosiveness").alias("off_pass_explosiveness"),
            F.col("ads.offense_passingPlays_successRate").alias("off_pass_success_rate"),
            F.col("ads.offense_passingPlays_totalPPA").alias("off_pass_total_ppa"),
            F.col("ads.offense_passingPlays_ppa").alias("off_pass_ppa_per_play"),
            F.col("ads.offense_passingPlays_rate").alias("off_pass_play_rate"),
            
            # OFFENSIVE RUSHING METRICS  
            F.col("ads.offense_rushingPlays_explosiveness").alias("off_rush_explosiveness"),
            F.col("ads.offense_rushingPlays_successRate").alias("off_rush_success_rate"),
            F.col("ads.offense_rushingPlays_totalPPA").alias("off_rush_total_ppa"),
            F.col("ads.offense_rushingPlays_ppa").alias("off_rush_ppa_per_play"),
            F.col("ads.offense_rushingPlays_rate").alias("off_rush_play_rate"),
            
            # OFFENSIVE OVERALL METRICS
            F.col("ads.offense_explosiveness").alias("off_overall_explosiveness"),
            F.col("ads.offense_successRate").alias("off_overall_success_rate"),
            F.col("ads.offense_totalPPA").alias("off_total_ppa"),
            F.col("ads.offense_ppa").alias("off_ppa_per_play"),
            
            # OFFENSIVE LINE METRICS
            F.col("ads.offense_lineYardsTotal").alias("off_line_yards_total"),
            F.col("ads.offense_lineYards").alias("off_line_yards_per_rush"),
            F.col("ads.offense_stuffRate").alias("off_stuff_rate"),
            F.col("ads.offense_powerSuccess").alias("off_power_success_rate"),
            
            # DEFENSIVE PASSING METRICS
            F.col("ads.defense_passingPlays_explosiveness").alias("def_pass_explosiveness_allowed"),
            F.col("ads.defense_passingPlays_successRate").alias("def_pass_success_rate_allowed"),
            F.col("ads.defense_passingPlays_totalPPA").alias("def_pass_total_ppa_allowed"),
            F.col("ads.defense_passingPlays_ppa").alias("def_pass_ppa_per_play_allowed"),
            
            # DEFENSIVE RUSHING METRICS
            F.col("ads.defense_rushingPlays_explosiveness").alias("def_rush_explosiveness_allowed"),
            F.col("ads.defense_rushingPlays_successRate").alias("def_rush_success_rate_allowed"),
            F.col("ads.defense_rushingPlays_totalPPA").alias("def_rush_total_ppa_allowed"),
            F.col("ads.defense_rushingPlays_ppa").alias("def_rush_ppa_per_play_allowed"),
            
            # DEFENSIVE OVERALL METRICS
            F.col("ads.defense_explosiveness").alias("def_overall_explosiveness_allowed"),
            F.col("ads.defense_successRate").alias("def_overall_success_rate_allowed"),
            F.col("ads.defense_totalPPA").alias("def_total_ppa_allowed"),
            F.col("ads.defense_ppa").alias("def_ppa_per_play_allowed"),
            
            # DEFENSIVE LINE METRICS
            F.col("ads.defense_lineYardsTotal").alias("def_line_yards_total_allowed"),
            F.col("ads.defense_lineYards").alias("def_line_yards_per_rush_allowed"),
            F.col("ads.defense_stuffRate").alias("def_stuff_rate"),
            F.col("ads.defense_powerSuccess").alias("def_power_success_rate_allowed"),
            
            # VOLUME METRICS
            F.col("ads.defense_drives").alias("defensive_drives_faced"),
            F.col("ads.defense_plays").alias("defensive_plays_faced"),
            
            # CALCULATED EFFICIENCY METRICS
            
            # Overall offensive efficiency (PPA-based)
            F.round(F.col("ads.offense_ppa"), 4).alias("offensive_efficiency_ppa"),
            
            # Overall defensive efficiency (lower PPA allowed = better)
            F.round(F.col("ads.defense_ppa"), 4).alias("defensive_efficiency_ppa"),
            
            # Explosiveness differential (offense - defense allowed)
            F.round(
                F.col("ads.offense_explosiveness") - F.col("ads.defense_explosiveness"), 4
            ).alias("explosiveness_differential"),
            
            # Success rate differential (offense - defense allowed)  
            F.round(
                F.col("ads.offense_successRate") - F.col("ads.defense_successRate"), 4
            ).alias("success_rate_differential"),
            
            # Line yards differential (offense - defense allowed)
            F.round(
                F.col("ads.offense_lineYards") - F.col("ads.defense_lineYards"), 4
            ).alias("line_yards_differential"),
            
            # Overall EPA differential (offense - defense allowed)
            F.round(
                F.col("ads.offense_ppa") - F.col("ads.defense_ppa"), 4
            ).alias("epa_differential"),
            
            # PERFORMANCE TIERS BASED ON EPA
            F.when(F.col("ads.offense_ppa") >= 0.15, F.lit("Elite Offense"))
             .when(F.col("ads.offense_ppa") >= 0.05, F.lit("Good Offense"))
             .when(F.col("ads.offense_ppa") >= -0.05, F.lit("Average Offense"))
             .otherwise(F.lit("Below Average Offense")).alias("offensive_tier"),
            
            F.when(F.col("ads.defense_ppa") <= -0.05, F.lit("Elite Defense"))
             .when(F.col("ads.defense_ppa") <= 0.05, F.lit("Good Defense"))
             .when(F.col("ads.defense_ppa") <= 0.15, F.lit("Average Defense"))
             .otherwise(F.lit("Below Average Defense")).alias("defensive_tier"),
            
            # COMBINED EFFICIENCY SCORE  
            F.round(
                (F.col("ads.offense_ppa") - F.col("ads.defense_ppa")) * 100, 2
            ).alias("overall_efficiency_score")
        )
    )