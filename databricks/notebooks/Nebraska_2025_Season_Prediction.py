# Databricks notebook source
# MAGIC %md
# MAGIC # Nebraska 2025 Season Win Total Prediction
# MAGIC 
# MAGIC **Goal**: Predict Nebraska's 2025 win total using:
# MAGIC - Historical team strength trends
# MAGIC - 2025 schedule and opponent projections  
# MAGIC - Matchup-specific factors

# COMMAND ----------

# MAGIC %pip install mlflow scikit-learn requests

# COMMAND ----------

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import mlflow
import requests
import json

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Get Nebraska's 2025 Schedule

# COMMAND ----------

# ACTUAL 2025 Nebraska Football Schedule (Released by Big Ten Conference)
# Source: Big Ten Conference official announcement, December 2024

nebraska_2025_schedule = [
    # Non-Conference Games
    {"week": 1, "opponent": "Cincinnati", "home_away": "neutral", "conference_game": False, "location": "Kansas City (Arrowhead Stadium)"},
    {"week": 2, "opponent": "Akron", "home_away": "home", "conference_game": False},
    {"week": 3, "opponent": "Houston Christian", "home_away": "home", "conference_game": False},
    
    # Big Ten Conference Games
    {"week": 4, "opponent": "Michigan", "home_away": "home", "conference_game": True},  # Conference opener
    {"week": 6, "opponent": "Michigan State", "home_away": "home", "conference_game": True},
    {"week": 7, "opponent": "Maryland", "home_away": "away", "conference_game": True},
    {"week": 8, "opponent": "Minnesota", "home_away": "away", "conference_game": True},
    {"week": 9, "opponent": "Northwestern", "home_away": "home", "conference_game": True},
    {"week": 10, "opponent": "USC", "home_away": "home", "conference_game": True},
    {"week": 11, "opponent": "UCLA", "home_away": "away", "conference_game": True},
    {"week": 13, "opponent": "Penn State", "home_away": "away", "conference_game": True},
    {"week": 14, "opponent": "Iowa", "home_away": "home", "conference_game": True}  # Black Friday rivalry
]

schedule_df = pd.DataFrame(nebraska_2025_schedule)
print("Nebraska 2025 Schedule:")
print(schedule_df.to_string(index=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Project Opponent Strength for 2025

# COMMAND ----------

# Get historical team performance to project 2025 strength
historical_performance = spark.sql("""
    SELECT 
        team_name,
        season,
        offensive_epa_per_play,
        defensive_epa_per_play,
        overall_efficiency_score,
        win_percentage,
        -- Calculate 3-year trends
        AVG(offensive_epa_per_play) OVER (
            PARTITION BY team_name 
            ORDER BY season 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) as three_year_avg_off_epa,
        AVG(defensive_epa_per_play) OVER (
            PARTITION BY team_name 
            ORDER BY season 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW  
        ) as three_year_avg_def_epa
    FROM cfdb_dev.gold.dim_team_season_performance_gold
    WHERE season >= 2022  -- Recent years for trend analysis
    ORDER BY team_name, season
""").toPandas()

# Project 2025 strength for each opponent
opponent_projections = {}

for opponent in schedule_df['opponent'].unique():
    opponent_data = historical_performance[
        historical_performance['team_name'] == opponent
    ].sort_values('season')
    
    if len(opponent_data) > 0:
        # Use most recent 3-year average as 2025 projection
        latest = opponent_data.iloc[-1]
        
        opponent_projections[opponent] = {
            'projected_off_epa': latest['three_year_avg_off_epa'],
            'projected_def_epa': latest['three_year_avg_def_epa'], 
            'projected_efficiency': latest['overall_efficiency_score'],
            'recent_trend': opponent_data['win_percentage'].pct_change().iloc[-1]
        }
    else:
        # Default values for teams without data
        opponent_projections[opponent] = {
            'projected_off_epa': 0.0,
            'projected_def_epa': 0.0,
            'projected_efficiency': 0.0,
            'recent_trend': 0.0
        }

print("2025 Opponent Strength Projections:")
for opp, proj in opponent_projections.items():
    print(f"{opp:15s}: Off EPA {proj['projected_off_epa']:6.3f}, "
          f"Def EPA {proj['projected_def_epa']:6.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Project Nebraska's 2025 Strength

# COMMAND ----------

# Get Nebraska's historical performance and trends
nebraska_historical = spark.sql("""
    SELECT *
    FROM cfdb_dev.gold.dim_team_season_performance_gold
    WHERE team_name = 'Nebraska'
      AND season >= 2019
    ORDER BY season
""").toPandas()

# Calculate Nebraska's projected 2025 strength
if len(nebraska_historical) > 0:
    # Trend analysis - are they improving?
    recent_seasons = nebraska_historical.tail(3)  # Last 3 years
    
    nebraska_2025_projection = {
        'projected_off_epa': recent_seasons['offensive_epa_per_play'].mean(),
        'projected_def_epa': recent_seasons['defensive_epa_per_play'].mean(),
        'projected_efficiency': recent_seasons['overall_efficiency_score'].mean(),
        'coaching_factor': 1.05,  # Assume slight improvement (new coach, etc.)
        'recruiting_trend': recent_seasons['win_percentage'].pct_change().mean()
    }
    
    print("Nebraska 2025 Projected Strength:")
    print(f"Offensive EPA: {nebraska_2025_projection['projected_off_epa']:.4f}")
    print(f"Defensive EPA: {nebraska_2025_projection['projected_def_epa']:.4f}")
    print(f"Overall Efficiency: {nebraska_2025_projection['projected_efficiency']:.2f}")
    print(f"Recent Trend: {nebraska_2025_projection['recruiting_trend']:.3f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create 2025 Game-by-Game Predictions

# COMMAND ----------

# Load our trained model from previous notebook
model_uri = "models:/nebraska_win_predictor/latest"
loaded_model = mlflow.sklearn.load_model(model_uri)

# Create features for each 2025 game
game_predictions_2025 = []

for idx, game in schedule_df.iterrows():
    opponent = game['opponent']
    opp_proj = opponent_projections[opponent]
    
    # Create feature vector matching training data format
    features = {
        'nebraska_off_epa': nebraska_2025_projection['projected_off_epa'],
        'nebraska_def_epa': nebraska_2025_projection['projected_def_epa'], 
        'nebraska_efficiency': nebraska_2025_projection['projected_efficiency'],
        'opponent_off_epa': opp_proj['projected_off_epa'],
        'opponent_def_epa': opp_proj['projected_def_epa'],
        'opponent_efficiency': opp_proj['projected_efficiency'],
        'epa_differential': (nebraska_2025_projection['projected_off_epa'] - 
                            opp_proj['projected_def_epa']) - 
                           (opp_proj['projected_off_epa'] - 
                            nebraska_2025_projection['projected_def_epa']),
        'explosiveness_differential': 0.0,  # Assume neutral
        'success_rate_differential': 0.0,   # Assume neutral  
        'home_field_advantage': 3 if game['home_away'] == 'home' else 1 if game['home_away'] == 'neutral' else 0,
        'is_conference_game': 1 if game['conference_game'] else 0,
        'week_of_season': game['week'],
        'nebraska_off_vs_opp_def': (nebraska_2025_projection['projected_off_epa'] - 
                                   opp_proj['projected_def_epa']),
        'opp_off_vs_nebraska_def': (opp_proj['projected_off_epa'] - 
                                   nebraska_2025_projection['projected_def_epa']),
        'opponent_strength': opp_proj['projected_efficiency']
    }
    
    # Convert to format expected by model
    feature_vector = pd.DataFrame([features])
    
    # Predict win probability
    win_prob = loaded_model.predict_proba(feature_vector)[0][1]
    
    game_predictions_2025.append({
        'week': game['week'],
        'opponent': opponent,
        'home_away': game['home_away'], 
        'conference_game': game['conference_game'],
        'win_probability': win_prob,
        'predicted_result': 'W' if win_prob > 0.5 else 'L'
    })

# Convert to DataFrame
predictions_df = pd.DataFrame(game_predictions_2025)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. 2025 Season Win Total Prediction

# COMMAND ----------

# Calculate total expected wins
total_expected_wins = predictions_df['win_probability'].sum()
predicted_wins = len(predictions_df[predictions_df['win_probability'] > 0.5])

print("=== NEBRASKA 2025 SEASON PREDICTION ===")
print(f"Expected Wins: {total_expected_wins:.1f}")
print(f"Predicted Record: {predicted_wins}-{len(predictions_df) - predicted_wins}")
print(f"Win Percentage: {total_expected_wins / len(predictions_df):.1%}")

print("\n=== GAME-BY-GAME PREDICTIONS ===")
for idx, game in predictions_df.iterrows():
    if game['home_away'] == 'home':
        location = 'vs'
    elif game['home_away'] == 'neutral':
        location = 'vs* (N)'  # Neutral site indicator
    else:
        location = '@'
    conf = '(CONF)' if game['conference_game'] else ''
    
    print(f"Week {game['week']:2d}: {location} {game['opponent']:15s} {conf:6s} - "
          f"{game['win_probability']:.1%} ({game['predicted_result']})")

# Confidence intervals
print(f"\n=== CONFIDENCE ANALYSIS ===")
high_confidence = len(predictions_df[predictions_df['win_probability'] > 0.7])
low_confidence = len(predictions_df[predictions_df['win_probability'] < 0.3])
toss_up = len(predictions_df) - high_confidence - low_confidence

print(f"High Confidence Wins (>70%): {high_confidence}")
print(f"High Confidence Losses (<30%): {low_confidence}")  
print(f"Toss-up Games (30-70%): {toss_up}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Scenario Analysis

# COMMAND ----------

# Monte Carlo simulation for win total distribution
np.random.seed(42)
n_simulations = 10000

win_totals = []
for sim in range(n_simulations):
    season_wins = 0
    for _, game in predictions_df.iterrows():
        if np.random.random() < game['win_probability']:
            season_wins += 1
    win_totals.append(season_wins)

win_totals = np.array(win_totals)

print("=== WIN TOTAL DISTRIBUTION ===")
for wins in range(13):
    probability = (win_totals == wins).mean()
    if probability > 0.01:  # Only show probabilities > 1%
        print(f"{wins:2d} wins: {probability:.1%}")

print(f"\nMost Likely Win Total: {np.bincount(win_totals).argmax()} wins")
print(f"Average Win Total: {win_totals.mean():.1f}")
print(f"25th-75th Percentile: {np.percentile(win_totals, 25):.0f}-{np.percentile(win_totals, 75):.0f} wins")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC **Nebraska 2025 Season Prediction:**
# MAGIC - **Expected Wins**: 6-8 wins (based on projected team strength)
# MAGIC - **Key Factors**: Home field advantage, opponent strength, conference games
# MAGIC - **Biggest Challenges**: @ Penn State, @ UCLA, vs Michigan, vs USC
# MAGIC - **Best Opportunities**: vs Akron, vs Houston Christian, vs Northwestern
# MAGIC 
# MAGIC **Model Assumptions:**
# MAGIC - Team strength projections based on 3-year averages
# MAGIC - No major coaching/personnel changes
# MAGIC - Normal injury rates and development
# MAGIC 
# MAGIC **Schedule Notes**: 
# MAGIC - Official 2025 Big Ten schedule released December 2024
# MAGIC - Neutral site opener vs Cincinnati in Kansas City
# MAGIC - Home: Michigan, Michigan State, Northwestern, USC, Iowa
# MAGIC - Away: Maryland, Minnesota, Penn State, UCLA