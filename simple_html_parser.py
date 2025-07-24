#!/usr/bin/env python3
"""
Simple HTML parser for ESPN schedule data without external dependencies
"""

import json
import os
import re
from datetime import datetime

def extract_games_from_html(html_content, week):
    """Extract game data from raw HTML content"""
    games = []
    
    # Common college football team names to help validate matches
    known_teams = {
        'Alabama', 'Auburn', 'Georgia', 'Florida', 'Tennessee', 'LSU', 'Arkansas', 'Mississippi', 'Missouri', 'South Carolina', 'Kentucky', 'Vanderbilt', 'Texas A&M',
        'Ohio State', 'Michigan', 'Penn State', 'Wisconsin', 'Iowa', 'Minnesota', 'Illinois', 'Indiana', 'Maryland', 'Michigan State', 'Nebraska', 'Northwestern', 'Purdue', 'Rutgers',
        'Clemson', 'Florida State', 'Miami', 'North Carolina', 'NC State', 'Virginia Tech', 'Virginia', 'Louisville', 'Pittsburgh', 'Syracuse', 'Wake Forest', 'Duke', 'Georgia Tech', 'Boston College',
        'Oklahoma', 'Texas', 'Kansas', 'Kansas State', 'Iowa State', 'Oklahoma State', 'Texas Tech', 'Baylor', 'TCU', 'West Virginia',
        'USC', 'UCLA', 'Oregon', 'Washington', 'Stanford', 'California', 'Arizona', 'Arizona State', 'Colorado', 'Utah'
    }
    
    # Patterns to exclude (navigation, UI elements, etc.)
    exclude_patterns = [
        r'skip to', r'main content', r'navigation', r'menu', r'search', r'login', r'sign in',
        r'facebook', r'twitter', r'instagram', r'social', r'follow', r'subscribe',
        r'advertisement', r'ad', r'sponsor', r'cookie', r'privacy', r'terms',
        r'loading', r'error', r'retry', r'refresh', r'update', r'version'
    ]
    
    # Look for team names in common patterns
    # ESPN often uses patterns like "Team1 @ Team2" or "Team1 vs Team2"
    team_patterns = [
        r'([A-Z][a-zA-Z\s&.\'()-]+?)\s+@\s+([A-Z][a-zA-Z\s&.\'()-]+?)(?=\s|<|$)',
        r'([A-Z][a-zA-Z\s&.\'()-]+?)\s+vs\.?\s+([A-Z][a-zA-Z\s&.\'()-]+?)(?=\s|<|$)',
        r'>([A-Z][a-zA-Z\s&.\'()-]{3,30})</.*?>([A-Z][a-zA-Z\s&.\'()-]{3,30})<'
    ]
    
    # Look for time patterns
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*[AP]M(?:\s*ET)?)',
        r'(TBD|TBA)'
    ]
    
    # Look for network patterns
    network_patterns = [
        r'(ESPN\+?|ESPN2|ESPNU|FOX|FS1|FS2|CBS|CBSSN|NBC|ABC|BTN)',
        r'(SEC Network|ACC Network|Pac-12 Network|Big Ten Network)'
    ]
    
    # Find potential game sections
    lines = html_content.split('\n')
    current_game = {}
    game_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Look for team matchups
        for pattern in team_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if len(match) == 2:
                    team1, team2 = match
                    
                    # Clean team names
                    team1 = re.sub(r'<[^>]+>', '', team1).strip()
                    team2 = re.sub(r'<[^>]+>', '', team2).strip()
                    
                    # Skip if teams are too short or too long (likely not real team names)
                    if len(team1) < 3 or len(team2) < 3 or len(team1) > 30 or len(team2) > 30:
                        continue
                        
                    # Skip if contains HTML artifacts
                    if any(char in team1 + team2 for char in ['<', '>', '{', '}', '[', ']']):
                        continue
                    
                    # Skip navigation and UI elements
                    team1_lower = team1.lower()
                    team2_lower = team2.lower()
                    
                    skip_game = False
                    for exclude_pattern in exclude_patterns:
                        if re.search(exclude_pattern, team1_lower) or re.search(exclude_pattern, team2_lower):
                            skip_game = True
                            break
                    
                    if skip_game:
                        continue
                    
                    # Skip if teams contain mostly numbers or special characters
                    if re.search(r'^\d+$|^[^a-zA-Z]*$', team1) or re.search(r'^\d+$|^[^a-zA-Z]*$', team2):
                        continue
                    
                    # Require at least one team to be a known college team or have college-like name
                    is_valid_matchup = False
                    for known_team in known_teams:
                        if known_team.lower() in team1_lower or known_team.lower() in team2_lower:
                            is_valid_matchup = True
                            break
                    
                    # Also accept teams with "State", "University", "College", "Tech" in name
                    college_indicators = ['state', 'university', 'college', 'tech', 'southern', 'northern', 'eastern', 'western', 'central']
                    if not is_valid_matchup:
                        for indicator in college_indicators:
                            if indicator in team1_lower or indicator in team2_lower:
                                is_valid_matchup = True
                                break
                    
                    if not is_valid_matchup:
                        continue
                        
                    # Determine home/away
                    if '@' in line:
                        away_team = team1
                        home_team = team2
                        neutral_site = False
                    else:
                        home_team = team1
                        away_team = team2
                        neutral_site = True
                    
                    game_count += 1
                    current_game = {
                        "game_id": f"espn_2025_w{week:02d}_game_{game_count:03d}",
                        "week": week,
                        "season": 2025,
                        "teams": {
                            "home": home_team,
                            "away": away_team,
                            "neutral_site": neutral_site
                        },
                        "game_time": None,
                        "broadcast": {"network": None},
                        "venue": {"name": None, "location": None},
                        "betting": {"line": None},
                        "metadata": {
                            "scraped_timestamp": datetime.now().isoformat() + "Z",
                            "source": "simple_html_parser",
                            "line_number": i
                        }
                    }
                    
                    # Look for time in surrounding lines
                    for j in range(max(0, i-3), min(len(lines), i+4)):
                        for time_pattern in time_patterns:
                            time_match = re.search(time_pattern, lines[j])
                            if time_match:
                                current_game["game_time"] = time_match.group(1)
                                break
                        if current_game["game_time"]:
                            break
                    
                    # Look for network in surrounding lines  
                    for j in range(max(0, i-3), min(len(lines), i+4)):
                        for net_pattern in network_patterns:
                            net_match = re.search(net_pattern, lines[j])
                            if net_match:
                                current_game["broadcast"]["network"] = net_match.group(1)
                                break
                        if current_game["broadcast"]["network"]:
                            break
                    
                    games.append(current_game)
    
    return games

def parse_week_html(html_file, week):
    """Parse a single week's HTML file"""
    print(f"📄 Parsing Week {week}: {html_file}")
    
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return None
    
    games = extract_games_from_html(content, week)
    
    # Remove duplicates based on team names
    unique_games = []
    seen_matchups = set()
    
    for game in games:
        home = game["teams"]["home"]
        away = game["teams"]["away"]
        matchup = tuple(sorted([home, away]))
        
        if matchup not in seen_matchups:
            unique_games.append(game)
            seen_matchups.add(matchup)
    
    week_data = {
        "week": week,
        "season": 2025,
        "games": unique_games,
        "metadata": {
            "total_games": len(unique_games),
            "scraped_timestamp": datetime.now().isoformat() + "Z",
            "source": "simple_html_parser",
            "html_file": html_file
        }
    }
    
    print(f"   ✅ Extracted {len(unique_games)} unique games from Week {week}")
    return week_data

def save_week_json(week_data, output_dir="cfdb_schedules/2025"):
    """Save week data to JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    
    week = week_data["week"]
    filename = f"week_{week:02d}_parsed.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(week_data, f, indent=2)
    
    print(f"💾 Saved {filepath}")
    return filepath

def main():
    """Main parsing function"""
    print("🏈 Simple HTML Parser for ESPN 2025 Schedules")
    print("=" * 45)
    
    html_dir = "raw_html/2025_backup_low_quality"
    
    if not os.path.exists(html_dir):
        print(f"❌ HTML directory not found: {html_dir}")
        return
    
    total_games = 0
    successful_weeks = 0
    
    for week in range(1, 16):
        html_file = os.path.join(html_dir, f"week_{week}.html")
        
        if not os.path.exists(html_file):
            print(f"⚠️  Week {week} HTML file not found: {html_file}")
            continue
        
        week_data = parse_week_html(html_file, week)
        
        if week_data and week_data["games"]:
            save_week_json(week_data)
            total_games += len(week_data["games"])
            successful_weeks += 1
        else:
            print(f"❌ Failed to parse Week {week}")
    
    print(f"\n📊 Parsing Summary:")
    print(f"   Successful weeks: {successful_weeks}/15")
    print(f"   Total games extracted: {total_games}")
    if successful_weeks > 0:
        print(f"   Average games per week: {total_games/successful_weeks:.1f}")
    
    if successful_weeks > 0:
        print(f"\n🎉 JSON files saved to: cfdb_schedules/2025/")
    else:
        print(f"\n⚠️  No weeks parsed successfully.")

if __name__ == "__main__":
    main()