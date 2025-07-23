#!/usr/bin/env python3
"""
Simple ESPN HTML Parser using standard library only
Extracts basic schedule data from downloaded ESPN HTML files
"""

import json
import os
import re
from datetime import datetime
from html.parser import HTMLParser

# ESPN to CFDB team name mapping
ESPN_TO_CFDB_MAPPING = {
    "Miami (FL)": "Miami",
    "USC": "Southern California", 
    "UCF": "Central Florida",
    "BYU": "Brigham Young",
    "UConn": "Connecticut",
    "UMass": "Massachusetts",
    "FIU": "Florida International",
    "FAU": "Florida Atlantic",
    "UTSA": "UT San Antonio",
    "UTEP": "UTEP", 
    "WKU": "Western Kentucky",
    "ECU": "East Carolina",
    "SMU": "Southern Methodist",
    "TCU": "Texas Christian",
    "App State": "Appalachian State",
    "Ga. Southern": "Georgia Southern",
    "Old Dominion": "Old Dominion",
}

def standardize_team_name(espn_name):
    """Convert ESPN team names to CFDB standard names"""
    if not espn_name:
        return None
    return ESPN_TO_CFDB_MAPPING.get(espn_name.strip(), espn_name.strip())

def extract_schedule_from_html(html_content, week):
    """
    Extract schedule data from ESPN HTML content
    This is a basic parser since ESPN uses heavy JavaScript
    """
    print(f"   🔍 Searching for schedule data in Week {week}...")
    
    # Look for JSON data embedded in the HTML
    # ESPN often embeds data in script tags
    json_patterns = [
        r'window\.__espnfitt__\s*=\s*({.*?});',
        r'window\.espn\.gamestrip\s*=\s*({.*?});',
        r'window\.espn\.data\s*=\s*({.*?});',
        r'"events"\s*:\s*(\[.*?\])',
        r'"games"\s*:\s*(\[.*?\])',
    ]
    
    games_found = []
    
    for pattern in json_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL)
        if matches:
            print(f"   📋 Found {len(matches)} JSON data blocks")
            for match in matches:
                try:
                    data = json.loads(match)
                    games = extract_games_from_json(data, week)
                    games_found.extend(games)
                except json.JSONDecodeError:
                    continue
    
    # Fallback: search for team names in text
    if not games_found:
        print(f"   📝 No JSON found, searching for team names in text...")
        games_found = extract_games_from_text(html_content, week)
    
    return games_found

def extract_games_from_json(data, week):
    """Extract games from JSON data structure"""
    games = []
    
    # Common ESPN JSON structures
    possible_paths = [
        ['events'],
        ['games'], 
        ['schedule', 'events'],
        ['schedule', 'games'],
        ['content', 'schedule', 'events']
    ]
    
    for path in possible_paths:
        current = data
        try:
            for key in path:
                current = current[key]
            
            if isinstance(current, list):
                for event in current:
                    game = parse_espn_event(event, week)
                    if game:
                        games.append(game)
                break
        except (KeyError, TypeError):
            continue
    
    return games

def parse_espn_event(event, week):
    """Parse a single ESPN event/game object"""
    try:
        # Common ESPN event structure
        home_team = None
        away_team = None
        
        if 'competitors' in event:
            for comp in event['competitors']:
                team_name = comp.get('team', {}).get('displayName', '')
                if comp.get('homeAway') == 'home':
                    home_team = standardize_team_name(team_name)
                elif comp.get('homeAway') == 'away':
                    away_team = standardize_team_name(team_name)
        
        game_time = event.get('date', event.get('time', ''))
        venue = event.get('venue', {}).get('fullName', '')
        
        if home_team or away_team:
            return {
                "game_id": f"espn_2025_w{week:02d}_{away_team or 'team1'}_{home_team or 'team2'}".lower().replace(' ', '_'),
                "week": week,
                "season": 2025,
                "teams": {
                    "home": home_team,
                    "away": away_team,
                    "neutral_site": not home_team or not away_team
                },
                "game_time": game_time,
                "venue": {"name": venue},
                "metadata": {
                    "scraped_timestamp": datetime.utcnow().isoformat() + "Z",
                    "source": "espn_json_parser"
                }
            }
    except Exception as e:
        print(f"   ⚠️  Error parsing event: {e}")
    
    return None

def extract_games_from_text(html_content, week):
    """Fallback: extract games from HTML text content"""
    # Remove HTML tags for text analysis
    text_content = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Known college football team names (partial list)
    team_names = [
        'Alabama', 'Auburn', 'Georgia', 'Florida', 'Tennessee', 'LSU', 'Arkansas', 'Mississippi State',
        'Ole Miss', 'South Carolina', 'Kentucky', 'Vanderbilt', 'Missouri', 'Texas A&M',
        'Ohio State', 'Michigan', 'Penn State', 'Wisconsin', 'Iowa', 'Minnesota', 'Illinois',
        'Northwestern', 'Indiana', 'Purdue', 'Michigan State', 'Maryland', 'Rutgers', 'Nebraska',
        'Texas', 'Oklahoma', 'Kansas', 'Kansas State', 'Iowa State', 'Baylor', 'TCU', 'Texas Tech',
        'West Virginia', 'Oklahoma State', 'Cincinnati', 'Houston', 'UCF', 'BYU',
        'Notre Dame', 'USC', 'UCLA', 'Oregon', 'Washington', 'Arizona', 'Arizona State',
        'Colorado', 'Utah', 'Stanford', 'California', 'Oregon State', 'Washington State',
    ]
    
    games = []
    game_count = 0
    
    # Look for patterns like team names near each other
    for i, team1 in enumerate(team_names):
        if team1 in text_content:
            # Look for another team name nearby
            for team2 in team_names[i+1:]:
                if team2 in text_content and team1 != team2:
                    # Simple heuristic: if both teams appear, assume it's a game
                    # This is very basic but better than nothing
                    game_count += 1
                    games.append({
                        "game_id": f"espn_2025_w{week:02d}_game_{game_count:03d}",
                        "week": week,
                        "season": 2025,
                        "teams": {
                            "home": standardize_team_name(team1),
                            "away": standardize_team_name(team2),
                            "neutral_site": False
                        },
                        "game_time": None,
                        "venue": {"name": None},
                        "metadata": {
                            "scraped_timestamp": datetime.utcnow().isoformat() + "Z",
                            "source": "espn_text_parser",
                            "confidence": "low"
                        }
                    })
                    
                    if game_count >= 20:  # Reasonable limit per week
                        break
            if game_count >= 20:
                break
    
    return games

def parse_espn_week_html(html_file, week):
    """Parse a single week's HTML file"""
    print(f"📄 Parsing Week {week}: {html_file}")
    
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return None
    
    games = extract_schedule_from_html(content, week)
    
    week_data = {
        "week": week,
        "season": 2025,
        "games": games,
        "metadata": {
            "total_games": len(games),
            "scraped_timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "espn_simple_parser",
            "html_file": html_file
        }
    }
    
    print(f"   ✅ Extracted {len(games)} games from Week {week}")
    return week_data

def save_week_json(week_data, output_dir="cfdb_schedules/2025"):
    """Save week data to JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    
    week = week_data["week"]
    filename = f"week_{week:02d}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(week_data, f, indent=2)
    
    print(f"💾 Saved {filepath}")
    return filepath

def main():
    """Main parsing function"""
    print("🏈 Simple ESPN HTML Parser for 2025 Schedules")
    print("=" * 45)
    
    html_dir = "raw_html/2025"
    
    if not os.path.exists(html_dir):
        print(f"❌ HTML directory not found: {html_dir}")
        print("   Run ./download_espn_schedules.sh first")
        return
    
    # Process each week
    total_games = 0
    successful_weeks = 0
    
    for week in range(1, 16):
        html_file = os.path.join(html_dir, f"week_{week}.html")
        
        if not os.path.exists(html_file):
            print(f"⚠️  Week {week} HTML file not found: {html_file}")
            continue
        
        week_data = parse_espn_week_html(html_file, week)
        
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
    
    if total_games > 0:
        print(f"\n🎉 JSON files saved to: cfdb_schedules/2025/")
        print(f"🔄 Next: Test with a few samples to verify data quality")
        
        # Show sample from Week 1
        sample_file = "cfdb_schedules/2025/week_01.json"
        if os.path.exists(sample_file):
            with open(sample_file, 'r') as f:
                sample_data = json.load(f)
            print(f"\n📋 Sample from Week 1 ({len(sample_data['games'])} games):")
            for game in sample_data['games'][:3]:
                home = game['teams']['home'] or 'Unknown'
                away = game['teams']['away'] or 'Unknown'
                print(f"   {away} @ {home}")
    else:
        print(f"\n⚠️  No games extracted. ESPN uses heavy JavaScript.")
        print(f"   💡 Consider using Playwright MCP for better extraction")

if __name__ == "__main__":
    main()