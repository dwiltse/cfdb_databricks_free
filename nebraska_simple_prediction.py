#!/usr/bin/env python3
"""
Nebraska 2025 Win Prediction Model - Simplified Demo
Uses only standard library to demonstrate the prediction logic
"""

import random
import math

def main():
    print("🏈 NEBRASKA 2025 WIN PREDICTION MODEL")
    print("=" * 50)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # 2025 Nebraska Schedule (Official Big Ten Release)
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
    
    print("📅 2025 SCHEDULE:")
    for game in nebraska_2025_schedule:
        conf = "(CONF)" if game['conference_game'] else ""
        location = game['home_away'].upper()
        print(f"Week {game['week']:2d}: {location:7s} vs {game['opponent']:15s} {conf}")
    print()
    
    # Nebraska 2025 Projected Strength (based on recent trends)
    # EPA (Expected Points Added) per play - higher offense/lower defense is better
    nebraska_2025_projection = {
        'off_epa': 0.02,   # Modest offensive improvement 
        'def_epa': 0.03,   # Slight defensive improvement (positive = worse)
        'efficiency': -0.01, # Overall net efficiency
        'trend_factor': 1.05  # Slight upward trend under new coaching
    }
    
    # Opponent strength projections for 2025 (based on 3-year averages)
    opponent_projections = {
        'Cincinnati': {'off_epa': 0.05, 'def_epa': 0.02, 'efficiency': 0.3, 'tier': 'Medium'},
        'Akron': {'off_epa': -0.15, 'def_epa': 0.12, 'efficiency': -0.2, 'tier': 'Weak'},
        'Houston Christian': {'off_epa': -0.20, 'def_epa': 0.15, 'efficiency': -0.3, 'tier': 'Weak'},
        'Michigan': {'off_epa': 0.12, 'def_epa': -0.05, 'efficiency': 0.7, 'tier': 'Strong'},
        'Michigan State': {'off_epa': 0.02, 'def_epa': 0.05, 'efficiency': 0.3, 'tier': 'Medium'},
        'Maryland': {'off_epa': 0.08, 'def_epa': 0.03, 'efficiency': 0.4, 'tier': 'Medium'},
        'Minnesota': {'off_epa': 0.06, 'def_epa': 0.01, 'efficiency': 0.5, 'tier': 'Medium'},
        'Northwestern': {'off_epa': -0.05, 'def_epa': 0.08, 'efficiency': 0.2, 'tier': 'Medium'},
        'USC': {'off_epa': 0.10, 'def_epa': -0.02, 'efficiency': 0.6, 'tier': 'Strong'},
        'UCLA': {'off_epa': 0.07, 'def_epa': 0.04, 'efficiency': 0.4, 'tier': 'Medium'},
        'Penn State': {'off_epa': 0.15, 'def_epa': -0.08, 'efficiency': 0.8, 'tier': 'Strong'},
        'Iowa': {'off_epa': 0.03, 'def_epa': -0.02, 'efficiency': 0.5, 'tier': 'Medium'}
    }
    
    print("🎯 OPPONENT STRENGTH ANALYSIS:")
    strong_opponents = [opp for opp, data in opponent_projections.items() if data['tier'] == 'Strong']
    medium_opponents = [opp for opp, data in opponent_projections.items() if data['tier'] == 'Medium']
    weak_opponents = [opp for opp, data in opponent_projections.items() if data['tier'] == 'Weak']
    
    print(f"Strong Opponents ({len(strong_opponents)}): {', '.join(strong_opponents)}")
    print(f"Medium Opponents ({len(medium_opponents)}): {', '.join(medium_opponents)}")
    print(f"Weak Opponents ({len(weak_opponents)}): {', '.join(weak_opponents)}")
    print()
    
    # Generate game-by-game predictions
    print("🔮 GAME-BY-GAME WIN PREDICTIONS:")
    print("=" * 45)
    
    game_predictions = []
    
    for game in nebraska_2025_schedule:
        opponent = game['opponent']
        opp_data = opponent_projections[opponent]
        
        # Calculate EPA differential (key predictor)
        nebraska_off_vs_opp_def = nebraska_2025_projection['off_epa'] - opp_data['def_epa']
        opp_off_vs_nebraska_def = opp_data['off_epa'] - nebraska_2025_projection['def_epa']
        epa_differential = nebraska_off_vs_opp_def - opp_off_vs_nebraska_def
        
        # Home field advantage
        if game['home_away'] == 'home':
            home_advantage = 0.12  # ~12% boost for home games
            location_symbol = 'vs'
        elif game['home_away'] == 'neutral':
            home_advantage = 0.04  # Small neutral site advantage
            location_symbol = 'vs (N)'
        else:
            home_advantage = -0.08  # Road disadvantage
            location_symbol = '@'
        
        # Conference game difficulty modifier
        conf_modifier = -0.03 if game['conference_game'] else 0.05  # Conference games are harder
        
        # Calculate base win probability using logistic function
        # This mimics what a trained model would do
        base_factor = epa_differential * 8 + home_advantage + conf_modifier
        win_probability = 1 / (1 + math.exp(-base_factor))  # Logistic function
        
        # Clamp between reasonable bounds
        win_probability = max(0.05, min(0.95, win_probability))
        
        # Determine prediction
        predicted_result = 'W' if win_probability > 0.5 else 'L'
        confidence = 'HIGH' if win_probability > 0.7 or win_probability < 0.3 else 'MED'
        
        game_predictions.append({
            'week': game['week'],
            'opponent': opponent,
            'location_symbol': location_symbol,
            'conference_game': game['conference_game'],
            'win_probability': win_probability,
            'predicted_result': predicted_result,
            'confidence': confidence,
            'epa_differential': epa_differential
        })
        
        # Display prediction
        conf_label = '(CONF)' if game['conference_game'] else ''
        print(f"Week {game['week']:2d}: {location_symbol:8s} {opponent:15s} {conf_label:6s} - "
              f"{win_probability:.1%} ({predicted_result}) [{confidence}]")
    
    # Calculate season totals
    total_expected_wins = sum(game['win_probability'] for game in game_predictions)
    predicted_wins = len([g for g in game_predictions if g['predicted_result'] == 'W'])
    predicted_losses = len(game_predictions) - predicted_wins
    
    print(f"\n📊 2025 SEASON PROJECTION:")
    print("=" * 30)
    print(f"🎯 Expected Wins: {total_expected_wins:.1f}")
    print(f"📈 Predicted Record: {predicted_wins}-{predicted_losses}")
    print(f"📊 Win Percentage: {total_expected_wins / len(game_predictions):.1%}")
    
    # Confidence breakdown
    high_conf_wins = len([g for g in game_predictions if g['win_probability'] > 0.7])
    high_conf_losses = len([g for g in game_predictions if g['win_probability'] < 0.3])
    toss_ups = len(game_predictions) - high_conf_wins - high_conf_losses
    
    print(f"\n🎲 CONFIDENCE ANALYSIS:")
    print(f"High Confidence Wins (>70%): {high_conf_wins}")
    print(f"High Confidence Losses (<30%): {high_conf_losses}")
    print(f"Toss-up Games (30-70%): {toss_ups}")
    
    # Win distribution simulation
    print(f"\n🎰 WIN TOTAL SIMULATION (1,000 seasons):")
    win_totals = []
    
    for sim in range(1000):
        season_wins = 0
        for game in game_predictions:
            if random.random() < game['win_probability']:
                season_wins += 1
        win_totals.append(season_wins)
    
    # Count distribution
    win_distribution = {}
    for wins in win_totals:
        win_distribution[wins] = win_distribution.get(wins, 0) + 1
    
    print("Win Total Distribution:")
    for wins in sorted(win_distribution.keys()):
        count = win_distribution[wins]
        percentage = count / 1000
        if percentage >= 0.01:  # Only show >1% probability
            bar = "█" * int(percentage * 40)
            print(f"{wins:2d} wins: {percentage:5.1%} {bar}")
    
    # Statistics
    avg_wins = sum(win_totals) / len(win_totals)
    win_totals_sorted = sorted(win_totals)
    median_wins = win_totals_sorted[len(win_totals_sorted) // 2]
    p25 = win_totals_sorted[len(win_totals_sorted) // 4]
    p75 = win_totals_sorted[3 * len(win_totals_sorted) // 4]
    
    print(f"\nStatistics:")
    print(f"Average: {avg_wins:.1f} wins")
    print(f"Median: {median_wins} wins")
    print(f"25th-75th Percentile: {p25}-{p75} wins")
    
    # Key insights
    print(f"\n💡 KEY INSIGHTS:")
    print("=" * 20)
    
    # Easiest games
    easiest = sorted(game_predictions, key=lambda x: x['win_probability'], reverse=True)[:3]
    print("Easiest Games:")
    for game in easiest:
        print(f"  • Week {game['week']}: {game['location_symbol']} {game['opponent']} ({game['win_probability']:.1%})")
    
    # Hardest games  
    hardest = sorted(game_predictions, key=lambda x: x['win_probability'])[:3]
    print("Hardest Games:")
    for game in hardest:
        print(f"  • Week {game['week']}: {game['location_symbol']} {game['opponent']} ({game['win_probability']:.1%})")
    
    print(f"\n🏠 Home vs Road:")
    home_games = [g for g in game_predictions if 'vs' in g['location_symbol'] and 'N' not in g['location_symbol']]
    road_games = [g for g in game_predictions if '@' in g['location_symbol']]
    
    home_expected = sum(g['win_probability'] for g in home_games)
    road_expected = sum(g['win_probability'] for g in road_games)
    
    print(f"Home Expected Wins: {home_expected:.1f} ({len(home_games)} games)")
    print(f"Road Expected Wins: {road_expected:.1f} ({len(road_games)} games)")
    
    print(f"\n🔄 Conference vs Non-Conference:")
    conf_games = [g for g in game_predictions if g['conference_game']]
    non_conf_games = [g for g in game_predictions if not g['conference_game']]
    
    conf_expected = sum(g['win_probability'] for g in conf_games)
    non_conf_expected = sum(g['win_probability'] for g in non_conf_games)
    
    print(f"Conference Expected Wins: {conf_expected:.1f} ({len(conf_games)} games)")
    print(f"Non-Conference Expected Wins: {non_conf_expected:.1f} ({len(non_conf_games)} games)")
    
    print(f"\n🎯 BOTTOM LINE:")
    print(f"Nebraska is projected to win {total_expected_wins:.1f} games in 2025")
    print(f"Most likely range: {p25}-{p75} wins")
    if total_expected_wins >= 6.5:
        print("✅ Bowl eligible with high confidence")
    elif total_expected_wins >= 5.5:
        print("⚠️  Bowl eligibility uncertain - depends on close games")
    else:
        print("❌ Bowl eligibility unlikely without significant improvement")

if __name__ == "__main__":
    main()