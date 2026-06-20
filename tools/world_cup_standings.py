#!/usr/bin/env python3
"""
World Cup 2026 Standings
Fetches the current group stage standings for the FIFA World Cup 2026
(league=1, season=2026) from api-sports.io and saves them to JSON.
"""

import json
import os
import sys
from datetime import datetime

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY,
}

WC_LEAGUE_ID = 1
WC_SEASON = 2026

OUTPUT_FILE = "wc2026_standings.json"


# ── API helper ─────────────────────────────────────────────────────────────────

def get_standings() -> list[dict]:
    """Fetch standings for all World Cup 2026 groups."""
    params = {
        "league": WC_LEAGUE_ID,
        "season": WC_SEASON,
    }
    resp = requests.get(
        f"{BASE_URL}/standings", headers=HEADERS, params=params, timeout=15
    )
    resp.raise_for_status()
    data = resp.json()

    errors = data.get("errors", {})
    if errors:
        print(f"API errors: {errors}", file=sys.stderr)
        return []

    # response is a list; the first item contains league + standings
    results = data.get("response", [])
    if not results:
        return []

    # standings is a list of groups, each group is a list of team rows
    return results[0].get("league", {}).get("standings", [])


# ── Data shaping ───────────────────────────────────────────────────────────────

def shape_team_row(row: dict) -> dict:
    """Flatten one team's row in a standings table."""
    team = row.get("team", {})
    all_stats = row.get("all", {})
    goals = all_stats.get("goals", {})
    home_stats = row.get("home", {})
    away_stats = row.get("away", {})

    return {
        "rank": row.get("rank"),
        "team_id": team.get("id"),
        "team_name": team.get("name"),
        "team_logo": team.get("logo"),
        "played": all_stats.get("played"),
        "win": all_stats.get("win"),
        "draw": all_stats.get("draw"),
        "lose": all_stats.get("lose"),
        "goals_for": goals.get("for"),
        "goals_against": goals.get("against"),
        "goal_difference": row.get("goalsDiff"),
        "points": row.get("points"),
        "form": row.get("form"),
        "status": row.get("status"),
        "description": row.get("description"),
        "home": {
            "played": home_stats.get("played"),
            "win": home_stats.get("win"),
            "draw": home_stats.get("draw"),
            "lose": home_stats.get("lose"),
            "goals_for": home_stats.get("goals", {}).get("for"),
            "goals_against": home_stats.get("goals", {}).get("against"),
        },
        "away": {
            "played": away_stats.get("played"),
            "win": away_stats.get("win"),
            "draw": away_stats.get("draw"),
            "lose": away_stats.get("lose"),
            "goals_for": away_stats.get("goals", {}).get("for"),
            "goals_against": away_stats.get("goals", {}).get("against"),
        },
        "last_updated": row.get("update"),
    }


def shape_standings(raw_groups: list[list[dict]]) -> list[dict]:
    """Convert the raw API groups into a clean list of group objects."""
    groups = []
    for group_rows in raw_groups:
        if not group_rows:
            continue

        # The group name lives on each row under the "group" key
        group_name = group_rows[0].get("group", f"Group {len(groups) + 1}")

        groups.append(
            {
                "group": group_name,
                "teams": [shape_team_row(row) for row in group_rows],
            }
        )

    return groups


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY:
        print(
            "ERROR: API key not set.\n"
            "Export your key first:  export API_FOOTBALL_KEY='your_key_here'",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Fetching World Cup 2026 standings...")

    raw_groups = get_standings()

    if not raw_groups:
        print("No standings data returned. The group stage may not have started yet.")
        sys.exit(0)

    groups = shape_standings(raw_groups)

    output = {
        "retrieved_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "league": "FIFA World Cup 2026",
        "league_id": WC_LEAGUE_ID,
        "season": WC_SEASON,
        "total_groups": len(groups),
        "standings": groups,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"Saved standings for {len(groups)} group(s) to {OUTPUT_FILE}")

    # Print a quick summary to the console
    print()
    for group in groups:
        print(f"  {group['group']}")
        for team in group["teams"]:
            pts = team["points"] if team["points"] is not None else "-"
            gd = team["goal_difference"] if team["goal_difference"] is not None else "-"
            print(
                f"    {team['rank']:>2}. {team['team_name']:<25} "
                f"Pts: {pts:<3}  GD: {gd}"
            )
        print()


if __name__ == "__main__":
    main()
