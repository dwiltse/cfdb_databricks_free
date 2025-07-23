#!/usr/bin/env python3
"""
ESPN HTML Parser for 2025 College Football Schedules
Parses downloaded HTML files and extracts game data to JSON format
"""

import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ESPN to CFDB team name mapping for known mismatches
ESPN_TO_CFDB_MAPPING = {
    # Common mismatches we expect
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
    "NIU": "Northern Illinois",
    "EMU": "Eastern Michigan",
    "CMU": "Central Michigan",
    "WMU": "Western Michigan",
    "BGSU": "Bowling Green",
    "Kent St.": "Kent State",
    "Ball St.": "Ball State",
    "Miami (OH)": "Miami (OH)",
    # Add more as we discover them
}

def standardize_team_name(espn_name):
    """Convert ESPN team names to CFDB standard names"""
    if not espn_name:
        return None
    return ESPN_TO_CFDB_MAPPING.get(espn_name.strip(), espn_name.strip())

def extract_teams_from_element(team_element):
    """Extract team names and home/away status from team element"""
    team_text = team_element.get_text().strip()
    
    # Look for @ symbol to determine home/away
    if '@' in team_text:
        parts = team_text.split('@')
        away_team = standardize_team_name(parts[0].strip())
        home_team = standardize_team_name(parts[1].strip())
        neutral_site = False
    else:
        # Could be neutral site or different format
        # Try to split on common separators
        separators = [' vs ', ' v ', '  ']
        teams = None
        
        for sep in separators:
            if sep in team_text:
                teams = team_text.split(sep)
                break
        
        if teams and len(teams) >= 2:
            team1 = standardize_team_name(teams[0].strip())
            team2 = standardize_team_name(teams[1].strip())
            # For neutral sites, we'll call first team "home" for consistency
            home_team = team1
            away_team = team2
            neutral_site = True
        else:
            # Single team or unrecognized format
            return None, None, True
    
    return home_team, away_team, neutral_site

def extract_time_and_network(time_element):
    """Extract game time and TV network from time element"""
    time_text = time_element.get_text().strip()
    
    # Extract time (patterns like "8:00 PM", "12:30 PM", "TBD")
    time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M|TBD|TBA)', time_text)
    game_time = time_match.group(1) if time_match else None
    
    # Extract network
    networks = ['ESPN', 'ESPN2', 'ESPNU', 'ESPN+', 'FOX', 'FS1', 'FS2', 'CBS', 'CBSSN', 
               'NBC', 'ABC', 'BTN', 'SEC Network', 'ACC Network', 'Pac-12 Network', 
               'Big Ten Network', 'ACCN', 'SECN', 'P12N']
    
    network = None
    for net in networks:
        if net in time_text:
            network = net
            break
    
    return game_time, network

def extract_venue_info(venue_element):
    """Extract venue name and location from venue element"""
    if not venue_element:
        return None, None
    
    venue_text = venue_element.get_text().strip()
    
    # Split venue name and location (usually by comma)
    if ',' in venue_text:
        parts = venue_text.split(',')
        venue_name = parts[0].strip()
        venue_location = ','.join(parts[1:]).strip()
    else:
        venue_name = venue_text
        venue_location = None
    
    return venue_name, venue_location

def extract_betting_info(betting_elements):
    """Extract betting line and over/under from betting elements"""
    betting_line = None
    spread = None
    over_under = None
    
    for element in betting_elements:
        text = element.get_text().strip()
        
        # Look for spread (patterns like "NEB -7", "Line: NEB -7")
        if 'Line:' in text or any(char in text for char in ['-', '+']):
            betting_line = text.replace('Line:', '').strip()
            # Extract numeric spread
            spread_match = re.search(r'[+-]?\d+\.?\d*', betting_line)
            if spread_match:
                spread = float(spread_match.group())
        
        # Look for over/under (patterns like "O/U: 51.5", "51.5")
        if 'O/U:' in text or re.search(r'\d+\.?\d*', text):
            ou_match = re.search(r'(\d+\.?\d*)', text)
            if ou_match:
                over_under = float(ou_match.group())
    
    return betting_line, spread, over_under

def parse_espn_week_html(html_file, week):
    """Parse a single week's HTML file and extract game data"""
    print(f"📄 Parsing Week {week}: {html_file}")
    
    try:
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return None
    
    soup = BeautifulSoup(content, 'html.parser')
    games = []
    
    # ESPN uses various class names - we'll try multiple approaches
    possible_selectors = [
        '.schedule-game',
        '.game-module', 
        '.Table__TR',
        'tr[data-idx]',
        '.gameModules',
        'table tr'
    ]
    
    game_elements = []
    for selector in possible_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"   🎯 Found {len(elements)} elements with selector: {selector}")
            game_elements = elements
            break
    
    if not game_elements:
        print(f"   ⚠️  No game elements found with any selector")
        # Try to find any text that looks like team names
        all_text = soup.get_text()
        if 'Nebraska' in all_text or 'Alabama' in all_text:
            print(f"   📝 File contains team names but couldn't parse structure")
        return None
    
    game_count = 0
    for i, element in enumerate(game_elements):
        try:
            # Skip header rows or empty elements
            if not element.get_text().strip():
                continue
            
            # Try to extract team information
            team_elements = element.find_all(['td', 'div', 'span'], string=re.compile(r'[A-Za-z\s]+'))
            if len(team_elements) < 2:
                continue
            
            # This is a simplified parser - we'll need to adjust based on actual ESPN structure
            element_text = element.get_text()
            
            # Look for team names (basic pattern matching)
            # We'll improve this once we see the actual HTML structure
            teams = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', element_text)
            
            if len(teams) >= 2:
                # Basic game structure
                game_data = {
                    "game_id": f"espn_2025_w{week:02d}_game_{game_count + 1:03d}",
                    "week": week,
                    "season": 2025,
                    "teams": {
                        "home": standardize_team_name(teams[0]) if len(teams) > 0 else None,
                        "away": standardize_team_name(teams[1]) if len(teams) > 1 else None,
                        "neutral_site": False  # Will improve detection later
                    },
                    "game_time": None,  # Will extract from actual HTML
                    "broadcast": {"network": None},
                    "venue": {"name": None, "location": None},
                    "betting": {"line": None, "spread": None, "over_under": None},
                    "metadata": {
                        "scraped_timestamp": datetime.utcnow().isoformat() + "Z",
                        "source": "espn_html_parser",
                        "raw_text": element_text[:200]  # For debugging
                    }
                }
                
                games.append(game_data)
                game_count += 1
                
        except Exception as e:
            print(f"   ⚠️  Error parsing game element {i}: {e}")
            continue
    
    week_data = {
        "week": week,
        "season": 2025,
        "games": games,
        "metadata": {
            "total_games": len(games),
            "scraped_timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "espn_html_parser",
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
    print("🏈 ESPN HTML Parser for 2025 Schedules")
    print("=" * 40)
    
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
    print(f"   Average games per week: {total_games/max(successful_weeks, 1):.1f}")
    
    if successful_weeks > 0:
        print(f"\n🎉 JSON files saved to: cfdb_schedules/2025/")
        print(f"🔄 Next: Load into your DLT pipeline or test with prediction model")
    else:
        print(f"\n⚠️  No weeks parsed successfully. Check HTML structure and update parser.")

if __name__ == "__main__":
    main()