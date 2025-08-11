import os
import json
from dotenv import load_dotenv
from cfbd import ApiClient, Configuration
from cfbd.api import GamesApi, TeamsApi, PlayersApi, RankingsApi, StatsApi, BettingApi

load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")

configuration = Configuration()
configuration.api_key['Authorization'] = f"Bearer {API_KEY}"  # <--- FIXED

def fetch_team_games(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = GamesApi(api_client)
        return api.get_games(year=year, team=team)

def fetch_team_stats(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = StatsApi(api_client)
        return api.get_team_season_stats(year=year, team=team)

def fetch_player_stats(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = PlayersApi(api_client)
        # You may want to adjust this to fetch only certain positions or starters
        return api.get_player_season_stats(year=year, team=team)

def fetch_rankings(year=2024):
    with ApiClient(configuration) as api_client:
        api = RankingsApi(api_client)
        return api.get_rankings(year=year)

def fetch_betting_lines(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = BettingApi(api_client)
        return api.get_lines(year=year, team=team)

def fetch_next_game(year=2024, team="Texas"):
    # Pull all games, then filter for the next game with a future date
    import datetime
    games = fetch_team_games(year=year, team=team)
    now = datetime.datetime.utcnow()
    for game in games:
        if hasattr(game, 'start_date'):
            try:
                game_date = datetime.datetime.fromisoformat(game.start_date.replace('Z', '+00:00'))
                if game_date > now:
                    return game
            except Exception:
                continue
    return None

def main():
    year = 2024
    team = "Texas"
    stats = {}
    print("Fetching team games...")
    stats["games"] = [game.to_dict() for game in fetch_team_games(year, team)]

    print("Fetching team stats...")
    stats["team_stats"] = [stat.to_dict() for stat in fetch_team_stats(year, team)]

    print("Fetching player stats...")
    stats["player_stats"] = [player.to_dict() for player in fetch_player_stats(year, team)]

    print("Fetching rankings...")
    stats["rankings"] = [ranking.to_dict() for ranking in fetch_rankings(year)]

    print("Fetching betting lines...")
    stats["betting_lines"] = [line.to_dict() for line in fetch_betting_lines(year, team)]

    print("Fetching next game info...")
    next_game = fetch_next_game(year, team)
    stats["next_game"] = next_game.to_dict() if next_game else {}

    print("Saving stats to data/latest_stats.json")
    os.makedirs("data", exist_ok=True)
    with open("data/latest_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("Done!")

if __name__ == "__main__":
    main()