import datetime
import json
import os
import requests

# --- CONFIGURATION ---
# Using the requested environment variable lookup
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
HOST = "v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON = 2026
OUTPUT_FILE = "worldcup_quirky.json"

HEADERS = {"x-rapidapi-host": HOST, "x-rapidapi-key": API_KEY}


def get_recent_fixtures():
    """Fetches fixtures from yesterday\'s rolling 24-hour window."""
    url = f"https://{HOST}/fixtures"

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "from": yesterday.strftime("%Y-%m-%d"),
        "to": yesterday.strftime("%Y-%m-%d"),
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get("response", [])
    except Exception as e:
        print(f"Error fetching fixtures: {e}")
        return []


def get_fixture_statistics(fixture_id):
    """Fetches team statistics for a specific fixture."""
    url = f"https://{HOST}/fixtures/statistics"
    try:
        response = requests.get(url, headers=HEADERS, params={"fixture": fixture_id})
        response.raise_for_status()
        return response.json().get("response", [])
    except Exception:
        return []


def get_player_statistics(fixture_id):
    """Fetches granular player performance statistics for a fixture."""
    url = f"https://{HOST}/fixtures/players"
    try:
        response = requests.get(url, headers=HEADERS, params={"fixture": fixture_id})
        response.raise_for_status()
        return response.json().get("response", [])
    except Exception:
        return []


def parse_stat(stats_list, type_string):
    """Helper to extract specific team stat values from the API\'s format."""
    for stat in stats_list:
        if stat.get("type") == type_string:
            val = stat.get("value")
            if val is None:
                return 0
            if isinstance(val, str) and "%" in val:
                return int(val.replace("%", ""))
            return int(val)
    return 0


def main():
    if not API_KEY:
        print(
            "Error: API_FOOTBALL_KEY environment variable is empty or not set."
        )
        return

    fixtures = get_recent_fixtures()

    if not fixtures:
        print("No fixtures found for yesterday\'s date window.")
        empty_payload = {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "status": "No matches played yesterday.",
            "referee_report": [],
            "quirky_player_stats": {},
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(empty_payload, f, indent=4)
        return

    referee_records = {}
    all_player_performances = []

    for fix in fixtures:
        fixture_id = fix["fixture"]["id"]
        teams = fix["teams"]
        match_name = f"{teams['home']['name']} vs {teams['away']['name']}"

        # 1. Process Referee and Team Data
        ref_name = fix["fixture"].get("referee")
        team_stats = get_fixture_statistics(fixture_id)

        total_fouls = 0
        yellow_cards = 0
        red_cards = 0

        for t_data in team_stats:
            s_list = t_data.get("statistics", [])
            total_fouls += parse_stat(s_list, "Fouls")
            yellow_cards += parse_stat(s_list, "Yellow Cards")
            red_cards += parse_stat(s_list, "Red Cards")

        if ref_name:
            # Clean up referee string (API sometimes provides "Name, Country")
            clean_ref_name = ref_name.split(",")[0].strip()

            if clean_ref_name not in referee_records:
                referee_records[clean_ref_name] = {
                    "name": clean_ref_name,
                    "matches_officiated": 0,
                    "total_fouls_called": 0,
                    "total_yellows": 0,
                    "total_reds": 0,
                }

            referee_records[clean_ref_name]["matches_officiated"] += 1
            referee_records[clean_ref_name]["total_fouls_called"] += total_fouls
            referee_records[clean_ref_name]["total_yellows"] += yellow_cards
            referee_records[clean_ref_name]["total_reds"] += red_cards

        # 2. Process Detailed, Quirky Player Statistics
        player_data = get_player_statistics(fixture_id)

        for team_players in player_data:
            team_name = team_players["team"]["name"]
            for p_entry in team_players.get("players", []):
                p_info = p_entry.get("player", {})
                p_stats = p_entry.get("statistics", [{}])[0]

                # Extract deep performance data blocks safely
                games = p_stats.get("games", {})
                shots = p_stats.get("shots", {})
                goals = p_stats.get("goals", {})
                fouls = p_stats.get("fouls", {})
                defense = p_stats.get("tackles", {})

                # Only evaluate if the player actually played minutes
                if (games.get("minutes") or 0) > 0:
                    all_player_performances.append(
                        {
                            "name": p_info.get("name"),
                            "team": team_name,
                            "photo": p_info.get("photo"),
                            "minutes": games.get("minutes") or 0,
                            "offsides": p_stats.get("offsides") or 0,
                            "fouls_drawn": fouls.get("drawn") or 0,
                            "fouls_committed": fouls.get("committed") or 0,
                            "shots_total": shots.get("total") or 0,
                            "shots_on_target": shots.get("on") or 0,
                            "interceptions": defense.get("interceptions") or 0,
                            "blocks": defense.get("blocks") or 0,
                        }
                    )

    # --- TOP QUIRKY CATEGORY RANKINGS ---

    # 1. Referees sorted by severity (Fouls per game logic)
    referee_list = list(referee_records.values())
    referee_list.sort(key=lambda x: x["total_fouls_called"], reverse=True)

    # 2. Sniper Alert: Most accurate shooters (Minimum 2 shots on target)
    snipers = [p for p in all_player_performances if p["shots_on_target"] >= 2]
    snipers.sort(key=lambda x: x["shots_on_target"], reverse=True)

    # 3. Target Man: Most fouled players on the pitch
    pin_cushions = [p for p in all_player_performances if p["fouls_drawn"] >= 1]
    pin_cushions.sort(key=lambda x: x["fouls_drawn"], reverse=True)

    # 4. Offside Trap Victims: Players caught wandering too early
    offside_kings = [p for p in all_player_performances if p["offsides"] >= 1]
    offside_kings.sort(key=lambda x: x["offsides"], reverse=True)

    # Final Payload Structure
    quirky_payload = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "referee_report": referee_list,
        "quirky_player_stats": {
            "snipers": snipers[:3],
            "most_fouled": pin_cushions[:3],
            "offside_kings": offside_kings[:3],
        },
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(quirky_payload, f, indent=4)

    print(f"Successfully compiled and updated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
