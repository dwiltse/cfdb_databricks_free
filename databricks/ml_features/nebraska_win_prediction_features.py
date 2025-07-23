# Databricks ML Feature Engineering for Nebraska Win Prediction
# File: nebraska_win_prediction_features.py

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Pipeline Parameters
catalog = spark.conf.get("catalog", "cfdb_dev")

@dlt.table(
    name=f"{catalog}.ml.nebraska_win_prediction_features",
    comment="ML features for Nebraska win prediction model",
    table_properties={
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.autoOptimize.autoCompact": "true",
        "pipelines.autoOptimize.managed": "true",
        "quality": "ml_features"
    }
)
def nebraska_win_prediction_features():
    """
    Create ML-ready features for predicting Nebraska game outcomes.
    
    Features include team strength, matchup differentials, situational factors,
    and historical performance indicators.
    """
    
    games = dlt.read(f"{catalog}.silver.fact_games_silver")
    predictions = dlt.read(f"{catalog}.gold.fact_game_predictions_gold")
    team_performance = dlt.read(f"{catalog}.gold.dim_team_season_performance_gold")
    
    # Get Nebraska team performance by season
    nebraska_performance = team_performance.filter(F.col("team_name") == "Nebraska").alias("neb")
    
    # Get opponent team performance  
    opponent_performance = team_performance.alias("opp")
    
    return (
        games.alias("g")
        .join(predictions.alias("p"), F.col("g.game_id") == F.col("p.game_id"), "inner")
        .join(nebraska_performance, F.col("g.season") == F.col("neb.season"), "left")
        .join(opponent_performance, 
              (F.col("g.season") == F.col("opp.season")) & 
              (F.when(F.col("g.home_team") == "Nebraska", F.col("g.away_team"))
               .otherwise(F.col("g.home_team")) == F.col("opp.team_name")), "left")
        .filter(
            (F.col("g.home_team") == "Nebraska") | (F.col("g.away_team") == "Nebraska")
        )
        .select(
            # Identifiers
            F.col("g.game_id"),
            F.col("g.season"),
            F.col("g.week"),
            F.col("g.home_team"),
            F.col("g.away_team"),
            
            # TARGET VARIABLE
            F.when(
                (F.col("g.home_team") == "Nebraska") & (F.col("g.home_points") > F.col("g.away_points")), 1
            ).when(
                (F.col("g.away_team") == "Nebraska") & (F.col("g.away_points") > F.col("g.home_points")), 1
            ).otherwise(0).alias("nebraska_win"),
            
            # NEBRASKA FEATURES (season-long strength)
            F.col("neb.offensive_epa_per_play").alias("nebraska_off_epa"),
            F.col("neb.defensive_epa_per_play").alias("nebraska_def_epa"),
            F.col("neb.overall_efficiency_score").alias("nebraska_efficiency"),
            F.col("neb.win_percentage").alias("nebraska_season_win_pct"),
            F.col("neb.avg_points_scored").alias("nebraska_avg_points"),
            F.col("neb.avg_points_allowed").alias("nebraska_avg_points_allowed"),
            
            # OPPONENT FEATURES (season-long strength)
            F.col("opp.offensive_epa_per_play").alias("opponent_off_epa"),
            F.col("opp.defensive_epa_per_play").alias("opponent_def_epa"),
            F.col("opp.overall_efficiency_score").alias("opponent_efficiency"),
            F.col("opp.win_percentage").alias("opponent_season_win_pct"),
            F.col("opp.avg_points_scored").alias("opponent_avg_points"),
            F.col("opp.avg_points_allowed").alias("opponent_avg_points_allowed"),
            
            # MATCHUP FEATURES (game-specific)
            F.when(F.col("g.home_team") == "Nebraska", 
                   F.col("p.home_team_epa_rating")).otherwise(
                   F.col("p.away_team_epa_rating")).alias("nebraska_game_epa"),
            
            F.when(F.col("g.home_team") == "Nebraska",
                   F.col("p.away_team_epa_rating")).otherwise(
                   F.col("p.home_team_epa_rating")).alias("opponent_game_epa"),
            
            F.col("p.overall_team_rating_differential").alias("epa_differential"),
            F.col("p.explosiveness_differential"),
            F.col("p.success_rate_differential"),
            
            # SITUATIONAL FEATURES
            F.when(F.col("g.home_team") == "Nebraska", 3).otherwise(0).alias("home_field_advantage"),
            F.col("g.is_conference_game").cast("int").alias("is_conference_game"),
            F.col("g.week").alias("week_of_season"),
            
            # DERIVED FEATURES
            (F.col("neb.offensive_epa_per_play") - F.col("opp.defensive_epa_per_play")).alias("nebraska_off_vs_opp_def"),
            (F.col("opp.offensive_epa_per_play") - F.col("neb.defensive_epa_per_play")).alias("opp_off_vs_nebraska_def"),
            
            # SEASON CONTEXT
            F.when(F.col("g.week") <= 4, "early_season")
             .when(F.col("g.week") >= 10, "late_season")
             .otherwise("mid_season").alias("season_phase"),
             
            # STRENGTH OF SCHEDULE PROXY
            F.col("opp.overall_efficiency_score").alias("opponent_strength")
        )
    )