"""
Fetches latest stats from collegefootballdata.com API and saves to data/latest_stats.json
"""
import os
import requests
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('CFB_API_KEY')

# API endpoints
TEAM_STATS_URL = 'https://api.collegefootballdata.com/stats/season'
PLAYER_STATS_URL = 'https://api.collegefootballdata.com/stats/player/season'
GAMES_URL = 'https://api.collegefootballdata.com/games'
RANKINGS_URL = 'https://api.collegefootballdata.com/rankings'

HEADERS = {'Authorization': f'Bearer {API_KEY}'}
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'latest_stats.json')

def fetch_team_stats(year=2024, team='Texas'):
    params = {'year': year, 'team': team}
    resp = requests.get(TEAM_STATS_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_player_stats(year=2024, team='Texas'):
    params = {'year': year, 'team': team}
    resp = requests.get(PLAYER_STATS_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_games(year=2024, team='Texas'):
    params = {'year': year, 'team': team}
    resp = requests.get(GAMES_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_rankings(year=2024):
    params = {'year': year}
    resp = requests.get(RANKINGS_URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def build_record_by_week(games):
    record = []
    for g in games:
        home_team = g.get('home_team')
        away_team = g.get('away_team')
        if not home_team or not away_team:
            continue  # skip games missing team info
        week = g.get('week')
        home_points = g.get('home_points', 0)
        away_points = g.get('away_points', 0)
        win = (home_team == 'Texas' and home_points > away_points) or (away_team == 'Texas' and away_points > home_points)
        loss = not win
        opponent = away_team if home_team == 'Texas' else home_team
        score = f"{home_points}-{away_points}"
        location = 'Home' if home_team == 'Texas' else 'Away'
        record.append({'week': week, 'W': win, 'L': loss, 'opponent': opponent, 'score': score, 'location': location})
    return record

def fetch_stats():
    year = 2024
    team = 'Texas'
    # Team stats
    team_stats = fetch_team_stats(year, team)
    team_df = pd.json_normalize(team_stats)
    # Player stats
    player_stats = fetch_player_stats(year, team)
    player_df = pd.json_normalize(player_stats)
    # Games
    games = fetch_games(year, team)
    # Rankings
    rankings = fetch_rankings(year)
    # Build record by week
    record_by_week = build_record_by_week(games)
    # Save all to JSON
    out = {
        'stats': team_df.to_dict(orient='records'),
        'player_stats': player_df.to_dict(orient='records'),
        'games': games,
        'record_by_week': record_by_week,
        'rankings': rankings
    }
    with open(DATA_PATH, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved stats to {DATA_PATH}")

if __name__ == "__main__":
    fetch_stats()
