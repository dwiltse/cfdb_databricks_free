#!/usr/bin/env python3
"""
Nebraska 2025 Win Prediction Model - Live Demo
Demonstrates the prediction model using synthetic historical data
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

def main():
    print("🏈 NEBRASKA 2025 WIN PREDICTION MODEL")
    print("=" * 50)

    # Set random seed for reproducibility
    np.random.seed(42)

    # Create synthetic historical Nebraska game data (2014-2024)
    # Based on actual Nebraska performance patterns

    seasons = list(range(2014, 2025))
    nebraska_games = []

    # Define Nebraska's opponents over the years (realistic Big Ten + non-conference)
    big_ten_opponents = ['Iowa', 'Wisconsin', 'Minnesota', 'Northwestern', 'Illinois', 
                         'Michigan', 'Michigan State', 'Ohio State', 'Penn State', 
                         'Maryland', 'Rutgers', 'Indiana', 'Purdue']
    non_conf_opponents = ['Colorado', 'Auburn', 'Oregon', 'Oklahoma', 'Georgia Southern',
                         'Akron', 'Buffalo', 'Troy', 'Cincinnati', 'Northern Illinois']

    for season in seasons:
        # Nebraska's approximate EPA performance by year (realistic trends)
        if season <= 2016:  # Mike Riley era - declining
            nebraska_off_epa = np.random.normal(-0.05, 0.1)
            nebraska_def_epa = np.random.normal(0.1, 0.08)
        elif season <= 2019:  # Scott Frost early years - struggling
            nebraska_off_epa = np.random.normal(-0.1, 0.12)  
            nebraska_def_epa = np.random.normal(0.15, 0.1)
        elif season <= 2021:  # Continued struggles
            nebraska_off_epa = np.random.normal(-0.08, 0.1)
            nebraska_def_epa = np.random.normal(0.12, 0.09)
        else:  # Recent improvement
            nebraska_off_epa = np.random.normal(-0.02, 0.08)
            nebraska_def_epa = np.random.normal(0.05, 0.07)
        
        # Generate 12 games per season
        week = 1
        for game_num in range(12):
            # Choose opponent
            if game_num < 3:  # Non-conference
                opponent = np.random.choice(non_conf_opponents)
                is_conference = False
            else:  # Conference games
                opponent = np.random.choice(big_ten_opponents)
                is_conference = True
            
            # Home field advantage (60% home games)
            is_home = np.random.random() < 0.6
            home_field_advantage = 3 if is_home else 0
            
            # Opponent strength (varies by opponent)
            if opponent in ['Ohio State', 'Michigan', 'Wisconsin', 'Penn State']:
                # Strong opponents
                opp_off_epa = np.random.normal(0.15, 0.05)
                opp_def_epa = np.random.normal(-0.10, 0.05)
                opp_efficiency = np.random.normal(0.8, 0.1)
            elif opponent in ['Iowa', 'Minnesota', 'Northwestern']:
                # Medium opponents  
                opp_off_epa = np.random.normal(0.05, 0.08)
                opp_def_epa = np.random.normal(0.02, 0.08)
                opp_efficiency = np.random.normal(0.5, 0.15)
            else:
                # Weaker opponents
                opp_off_epa = np.random.normal(-0.05, 0.1)
                opp_def_epa = np.random.normal(0.08, 0.1)
                opp_efficiency = np.random.normal(0.2, 0.2)
            
            # Calculate advanced metrics
            epa_differential = (nebraska_off_epa - opp_def_epa) - (opp_off_epa - nebraska_def_epa)
            explosiveness_diff = np.random.normal(epa_differential * 0.8, 0.05)
            success_rate_diff = np.random.normal(epa_differential * 1.2, 0.1)
            
            # Win probability based on EPA differential + home field + randomness
            base_win_prob = 0.5 + (epa_differential * 8) + (home_field_advantage * 0.04)
            base_win_prob = max(0.05, min(0.95, base_win_prob))  # Clamp between 5% and 95%
            
            # Determine actual win (with some randomness)
            nebraska_win = np.random.random() < base_win_prob
            
            game_data = {
                'season': season,
                'week': week,
                'opponent': opponent,
                'nebraska_off_epa': nebraska_off_epa,
                'nebraska_def_epa': nebraska_def_epa,
                'nebraska_efficiency': nebraska_off_epa - nebraska_def_epa,
                'opponent_off_epa': opp_off_epa,
                'opponent_def_epa': opp_def_epa,
                'opponent_efficiency': opp_efficiency,
                'epa_differential': epa_differential,
                'explosiveness_differential': explosiveness_diff,
                'success_rate_differential': success_rate_diff,
                'home_field_advantage': home_field_advantage,
                'is_conference_game': 1 if is_conference else 0,
                'week_of_season': week,
                'nebraska_off_vs_opp_def': nebraska_off_epa - opp_def_epa,
                'opp_off_vs_nebraska_def': opp_off_epa - nebraska_def_epa,
                'opponent_strength': opp_efficiency,
                'nebraska_win': 1 if nebraska_win else 0
            }
            
            nebraska_games.append(game_data)
            week += 1

    # Convert to DataFrame
    df = pd.DataFrame(nebraska_games)

    print(f"📊 Generated {len(df)} Nebraska games from {df['season'].min()}-{df['season'].max()}")
    print(f"🏆 Overall win rate: {df['nebraska_win'].mean():.1%}")
    print(f"🏠 Home win rate: {df[df['home_field_advantage'] > 0]['nebraska_win'].mean():.1%}")
    print(f"🛣️  Road win rate: {df[df['home_field_advantage'] == 0]['nebraska_win'].mean():.1%}")
    print()

    # Show wins by season
    wins_by_season = df.groupby('season')['nebraska_win'].sum().reset_index()
    wins_by_season.columns = ['Season', 'Wins']
    print("📈 Historical Nebraska Win Totals:")
    print(wins_by_season.to_string(index=False))
    print()

    # Train the prediction model
    print("🤖 TRAINING PREDICTION MODEL")
    print("=" * 30)

    # Define feature columns
    feature_columns = [
        'nebraska_off_epa', 'nebraska_def_epa', 'nebraska_efficiency',
        'opponent_off_epa', 'opponent_def_epa', 'opponent_efficiency', 
        'epa_differential', 'explosiveness_differential', 'success_rate_differential',
        'home_field_advantage', 'is_conference_game', 'week_of_season',
        'nebraska_off_vs_opp_def', 'opp_off_vs_nebraska_def',
        'opponent_strength'
    ]

    # Prepare features and target
    X = df[feature_columns].fillna(0)
    y = df['nebraska_win']

    # Temporal split: train on 2014-2022, test on 2023-2024
    train_mask = df['season'] <= 2022
    test_mask = df['season'] >= 2023

    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]

    print(f"Training set: {len(X_train)} games ({y_train.sum()} wins, {y_train.mean():.1%} rate)")
    print(f"Test set: {len(X_test)} games ({y_test.sum()} wins, {y_test.mean():.1%} rate)")

    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate model
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    train_prob = model.predict_proba(X_train)[:, 1]
    test_prob = model.predict_proba(X_test)[:, 1]

    train_acc = accuracy_score(y_train, train_pred)
    test_acc = accuracy_score(y_test, test_pred)

    print(f"Training Accuracy: {train_acc:.3f}")
    print(f"Test Accuracy: {test_acc:.3f}")

    # Feature importance
    importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n🔍 TOP 5 MOST IMPORTANT FEATURES:")
    for i, (_, row) in enumerate(importance_df.head().iterrows(), 1):
        print(f"{i}. {row['feature']}: {row['importance']:.3f}")

    # 2025 Nebraska Schedule
    print(f"\n🗓️  2025 NEBRASKA SCHEDULE & PREDICTIONS")
    print("=" * 45)

    nebraska_2025_schedule = [
        {"week": 1, "opponent": "Cincinnati", "home_away": "neutral", "conference_game": False},
        {"week": 2, "opponent": "Akron", "home_away": "home", "conference_game": False},
        {"week": 3, "opponent": "Houston Christian", "home_away": "home", "conference_game": False},
        {"week": 4, "opponent": "Michigan", "home_away": "home", "conference_game": True},
        {"week": 6, "opponent": "Michigan State", "home_away": "home", "conference_game": True},
        {"week": 7, "opponent": "Maryland", "home_away": "away", "conference_game": True},
        {"week": 8, "opponent": "Minnesota", "home_away": "away", "conference_game": True},
        {"week": 9, "opponent": "Northwestern", "home_away": "home", "conference_game": True},
        {"week": 10, "opponent": "USC", "home_away": "home", "conference_game": True},
        {"week": 11, "opponent": "UCLA", "home_away": "away", "conference_game": True},
        {"week": 13, "opponent": "Penn State", "home_away": "away", "conference_game": True},
        {"week": 14, "opponent": "Iowa", "home_away": "home", "conference_game": True}
    ]

    # Project 2025 Nebraska strength (slight improvement over recent years)
    nebraska_2025_projection = {
        'off_epa': 0.02,  # Modest improvement
        'def_epa': 0.03,  # Slight improvement
        'efficiency': -0.01
    }

    # Project opponent strengths for 2025
    opponent_projections = {
        'Cincinnati': {'off_epa': 0.05, 'def_epa': 0.02, 'efficiency': 0.3},
        'Akron': {'off_epa': -0.15, 'def_epa': 0.12, 'efficiency': -0.2},
        'Houston Christian': {'off_epa': -0.20, 'def_epa': 0.15, 'efficiency': -0.3},
        'Michigan': {'off_epa': 0.12, 'def_epa': -0.05, 'efficiency': 0.7},
        'Michigan State': {'off_epa': 0.02, 'def_epa': 0.05, 'efficiency': 0.3},
        'Maryland': {'off_epa': 0.08, 'def_epa': 0.03, 'efficiency': 0.4},
        'Minnesota': {'off_epa': 0.06, 'def_epa': 0.01, 'efficiency': 0.5},
        'Northwestern': {'off_epa': -0.05, 'def_epa': 0.08, 'efficiency': 0.2},
        'USC': {'off_epa': 0.10, 'def_epa': -0.02, 'efficiency': 0.6},
        'UCLA': {'off_epa': 0.07, 'def_epa': 0.04, 'efficiency': 0.4},
        'Penn State': {'off_epa': 0.15, 'def_epa': -0.08, 'efficiency': 0.8},
        'Iowa': {'off_epa': 0.03, 'def_epa': -0.02, 'efficiency': 0.5}
    }

    # Generate 2025 predictions
    game_predictions_2025 = []

    for game in nebraska_2025_schedule:
        opponent = game['opponent']
        opp_proj = opponent_projections[opponent]
        
        # Home field advantage
        if game['home_away'] == 'home':
            home_field = 3
            location = 'vs'
        elif game['home_away'] == 'neutral':
            home_field = 1
            location = 'vs (N)'
        else:
            home_field = 0
            location = '@'
        
        # Calculate features
        epa_diff = (nebraska_2025_projection['off_epa'] - opp_proj['def_epa']) - \
                   (opp_proj['off_epa'] - nebraska_2025_projection['def_epa'])
        
        features = {
            'nebraska_off_epa': nebraska_2025_projection['off_epa'],
            'nebraska_def_epa': nebraska_2025_projection['def_epa'],
            'nebraska_efficiency': nebraska_2025_projection['efficiency'],
            'opponent_off_epa': opp_proj['off_epa'],
            'opponent_def_epa': opp_proj['def_epa'],
            'opponent_efficiency': opp_proj['efficiency'],
            'epa_differential': epa_diff,
            'explosiveness_differential': epa_diff * 0.8,
            'success_rate_differential': epa_diff * 1.2,
            'home_field_advantage': home_field,
            'is_conference_game': 1 if game['conference_game'] else 0,
            'week_of_season': game['week'],
            'nebraska_off_vs_opp_def': nebraska_2025_projection['off_epa'] - opp_proj['def_epa'],
            'opp_off_vs_nebraska_def': opp_proj['off_epa'] - nebraska_2025_projection['def_epa'],
            'opponent_strength': opp_proj['efficiency']
        }
        
        # Predict win probability
        feature_vector = pd.DataFrame([features])
        win_prob = model.predict_proba(feature_vector)[0][1]
        
        game_predictions_2025.append({
            'week': game['week'],
            'opponent': opponent,
            'location': location,
            'conference_game': game['conference_game'],
            'win_probability': win_prob,
            'predicted_result': 'W' if win_prob > 0.5 else 'L'
        })

    # Display 2025 predictions
    predictions_df = pd.DataFrame(game_predictions_2025)
    total_expected_wins = predictions_df['win_probability'].sum()
    predicted_wins = len(predictions_df[predictions_df['win_probability'] > 0.5])

    print(f"🎯 EXPECTED WINS: {total_expected_wins:.1f}")
    print(f"📊 PREDICTED RECORD: {predicted_wins}-{len(predictions_df) - predicted_wins}")
    print(f"📈 WIN PERCENTAGE: {total_expected_wins / len(predictions_df):.1%}")
    print()

    print("GAME-BY-GAME PREDICTIONS:")
    for _, game in predictions_df.iterrows():
        conf = '(CONF)' if game['conference_game'] else ''
        print(f"Week {game['week']:2d}: {game['location']:8s} {game['opponent']:15s} {conf:6s} - "
              f"{game['win_probability']:.1%} ({game['predicted_result']})")

    # Confidence analysis
    print(f"\n🎲 CONFIDENCE ANALYSIS:")
    high_confidence = len(predictions_df[predictions_df['win_probability'] > 0.7])
    low_confidence = len(predictions_df[predictions_df['win_probability'] < 0.3])
    toss_up = len(predictions_df) - high_confidence - low_confidence

    print(f"High Confidence Wins (>70%): {high_confidence}")
    print(f"High Confidence Losses (<30%): {low_confidence}")  
    print(f"Toss-up Games (30-70%): {toss_up}")

    # Monte Carlo simulation
    print(f"\n🎰 MONTE CARLO SIMULATION (10,000 seasons):")
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

    print("Win Total Distribution:")
    for wins in range(13):
        probability = (win_totals == wins).mean()
        if probability > 0.01:  # Only show probabilities > 1%
            bars = "█" * int(probability * 50)  # Visual bar chart
            print(f"{wins:2d} wins: {probability:5.1%} {bars}")

    print(f"\nMost Likely: {np.bincount(win_totals).argmax()} wins")
    print(f"Average: {win_totals.mean():.1f} wins")
    print(f"25th-75th Percentile: {np.percentile(win_totals, 25):.0f}-{np.percentile(win_totals, 75):.0f} wins")

if __name__ == "__main__":
    main()