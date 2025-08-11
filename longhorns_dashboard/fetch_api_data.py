import os
import json
from typing import List, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from cfbd import ApiClient, Configuration
from cfbd.api import GamesApi, TeamsApi, PlayersApi, RankingsApi, StatsApi, BettingApi
from cfbd.exceptions import UnauthorizedException, ApiException

loaded = load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env')) or load_dotenv()
API_KEY = os.getenv("CFBD_API_KEY")
if not API_KEY:
    raise RuntimeError("CFBD_API_KEY is missing. Add it to longhorns_dashboard/.env or project .env.")

configuration = Configuration()
# Optional verbose HTTP logging if CFBD_DEBUG=true
if os.getenv("CFBD_DEBUG", "false").lower() in {"1", "true", "yes"}:
    configuration.debug = True

# cfbd 5.x expects bearer token via access_token to enable 'apiKey' auth
configuration.access_token = API_KEY

def fetch_team_games(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = GamesApi(api_client)
        try:
            return api.get_games(year=year, team=team)
        except UnauthorizedException as e:
            print("ERROR: Unauthorized while fetching games. Please verify CFBD_API_KEY is valid and active.")
            return []
        except ApiException as e:
            print(f"ERROR: Failed to fetch games: {e}")
            return []

def fetch_team_stats(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = StatsApi(api_client)
        try:
            return api.get_team_stats(year=year, team=team)
        except UnauthorizedException:
            print("ERROR: Unauthorized while fetching team stats.")
            return []
        except ApiException as e:
            print(f"ERROR: Failed to fetch team stats: {e}")
            return []

def fetch_player_stats(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        stats_api = StatsApi(api_client)
        try:
            # You may want to adjust this to fetch only certain positions or starters
            return stats_api.get_player_season_stats(year=year, team=team)
        except UnauthorizedException:
            print("ERROR: Unauthorized while fetching player stats.")
            return []
        except ApiException as e:
            print(f"ERROR: Failed to fetch player stats: {e}")
            return []

def fetch_rankings(year=2024):
    with ApiClient(configuration) as api_client:
        api = RankingsApi(api_client)
        try:
            return api.get_rankings(year=year)
        except UnauthorizedException:
            print("ERROR: Unauthorized while fetching rankings.")
            return []
        except ApiException as e:
            print(f"ERROR: Failed to fetch rankings: {e}")
            return []

def fetch_betting_lines(year=2024, team="Texas"):
    with ApiClient(configuration) as api_client:
        api = BettingApi(api_client)
        try:
            return api.get_lines(year=year, team=team)
        except UnauthorizedException:
            print("ERROR: Unauthorized while fetching betting lines.")
            return []
        except ApiException as e:
            print(f"ERROR: Failed to fetch betting lines: {e}")
            return []

def fetch_next_game(year=2024, team="Texas"):
    # Pull all games, then filter for the next game with a future date
    games = fetch_team_games(year=year, team=team)
    now = datetime.now(timezone.utc)
    for game in games:
        if hasattr(game, 'start_date') and game.start_date:
            try:
                game_date = datetime.fromisoformat(game.start_date.replace('Z', '+00:00'))
                if game_date.tzinfo is None:
                    game_date = game_date.replace(tzinfo=timezone.utc)
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

    def _json_default(o):
        # cfbd models have to_dict; handle datetimes; fallback to str
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        if isinstance(o, datetime):
            try:
                return o.isoformat()
            except Exception:
                return str(o)
        return str(o)

    with open("data/latest_stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=_json_default)

    print("Done!")

if __name__ == "__main__":
    main()