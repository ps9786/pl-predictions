import datetime
import json
import requests
import os

# --- CONFIGURATION ---
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
HOST = "v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON = 2026
OUTPUT_FILE = "worldcup_quirky.json"

HEADERS = {"x-rapidapi-host": HOST, "x-rapidapi-key": API_KEY}


def get_recent_fixtures():
    """Fetches fixtures from the last 24 hours to analyze."""
    url = f"https://{HOST}/fixtures"

    # Define a 24-hour window for yesterday's games
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
        data = response.json()
        return data.get("response", [])
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
    """Helper to extract specific stat values from the API's format."""
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
    fixtures = get_recent_fixtures()

    if not fixtures:
        print("No fixtures found for the processed time frame.")
        # Create a basic file so your website doesn't break if no games happened yesterday
        empty_payload = {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "status": "No matches played yesterday.",
            "chaos_matches": [],
            "unsung_heroes": [],
        }
        with open(OUTPUT_FILE, "w") as f:
            json.dump(empty_payload, f, indent=4)
        return

    chaos_matches = []
    all_player_performances = []

    for fix in fixtures:
        fixture_id = fix["fixture"]["id"]
        teams = fix["teams"]
        match_name = f"{teams['home']['name']} vs {teams['away']['name']}"

        # 1. Process Team Chaos Stats (Fouls, Cards, Low Shots)
        team_stats = get_fixture_statistics(fixture_id)

        total_fouls = 0
        total_shots = 0
        yellow_cards = 0
        red_cards = 0

        for t_data in team_stats:
            s_list = t_data.get("statistics", [])
            total_fouls += parse_stat(s_list, "Fouls")
            total_shots += parse_stat(s_list, "Total Shots")
            yellow_cards += parse_stat(s_list, "Yellow Cards")
            red_cards += parse_stat(s_list, "Red Cards")

        # Calculate a custom "Chaos Index" (High fouls + cards, low actual shots)
        # Avoid division by zero if there are no shots
        shot_factor = total_shots if total_shots > 0 else 1
        chaos_index = round(
            ((total_fouls + (yellow_cards * 2) + (red_cards * 5)) / shot_factor), 2
        )

        chaos_matches.append(
            {
                "match": match_name,
                "chaos_index": chaos_index,
                "fouls": total_fouls,
                "cards": {"yellow": yellow_cards, "red": red_cards},
            }
        )

        # 2. Process Player Stats (Interceptions, Blocks, Tacks for Unsung Heroes)
        player_data = get_player_statistics(fixture_id)

        for team_players in player_data:
            team_name = team_players["team"]["name"]
            for p_entry in team_players.get("players", []):
                p_info = p_entry.get("player", {})
                p_stats = p_entry.get("statistics", [{}])[
                    0
                ]  # Get match statistics array

                # Extract defensive grunt work
                tackles = p_stats.get("tackles", {}).get("interceptions") or 0
                blocks = p_stats.get("tackles", {}).get("blocks") or 0
                duels_won = p_stats.get("duels", {}).get("won") or 0

                if tackles > 0 or blocks > 0 or duels_won > 0:
                    all_player_performances.append(
                        {
                            "name": p_info.get("name"),
                            "team": team_name,
                            "photo": p_info.get("photo"),
                            "interceptions": tackles,
                            "blocks": blocks,
                            "duels_won": duels_won,
                            "dirty_work_score": (tackles * 2)
                            + (blocks * 2)
                            + duels_won,
                        }
                    )

    # Sort data to find the absolute peaks of the day
    chaos_matches.sort(key=lambda x: x["chaos_index"], reverse=True)
    all_player_performances.sort(
        key=lambda x: x["dirty_work_score"], reverse=True
    )

    # Build final Quirky Payload
    quirky_payload = {
        "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        "most_chaotic_match": chaos_matches[0] if chaos_matches else None,
        "unsung_heroes": all_player_performances[:5],  # Top 5 workhorses
    }

    # Write out to the JSON file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(quirky_payload, f, indent=4)

    print(f"Successfully generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
