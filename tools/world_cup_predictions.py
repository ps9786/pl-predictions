#!/usr/bin/env python3
"""
World Cup 2026 Match Predictions
Fetches today's and tomorrow's World Cup 2026 fixtures from api-sports.io
and retrieves AI predictions for each match, saving results to JSON.
"""

import json
import os
import sys
from datetime import date, timedelta

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-apisports-key": API_KEY,
}

# World Cup 2026 identifiers (league=1, season=2026 per api-sports.io)
WC_LEAGUE_ID = 1
WC_SEASON = 2026

OUTPUT_FILE = "wc2026_predictions.json"


# ── API helpers ────────────────────────────────────────────────────────────────

def get_fixtures_for_date(match_date: date) -> list[dict]:
    """Return all World Cup 2026 fixtures for a given date."""
    params = {
        "league": WC_LEAGUE_ID,
        "season": WC_SEASON,
        "date": match_date.isoformat(),  # YYYY-MM-DD
    }
    resp = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    errors = data.get("errors", {})
    if errors:
        print(f"  API errors for fixtures on {match_date}: {errors}", file=sys.stderr)
        return []

    return data.get("response", [])


def get_prediction(fixture_id: int) -> dict:
    """Return the prediction payload for a single fixture."""
    params = {"fixture": fixture_id}
    resp = requests.get(f"{BASE_URL}/predictions", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    errors = data.get("errors", {})
    if errors:
        print(f"  API errors for prediction fixture {fixture_id}: {errors}", file=sys.stderr)
        return {}

    results = data.get("response", [])
    return results[0] if results else {}


# ── Data shaping ───────────────────────────────────────────────────────────────

def shape_fixture(fixture_raw: dict) -> dict:
    """Extract the most useful fixture fields into a flat dict."""
    f = fixture_raw.get("fixture", {})
    teams = fixture_raw.get("teams", {})
    venue = fixture_raw.get("fixture", {}).get("venue", {})
    goals = fixture_raw.get("goals", {})
    score = fixture_raw.get("score", {})
    league = fixture_raw.get("league", {})

    return {
        "fixture_id": f.get("id"),
        "date_utc": f.get("date"),
        "status": f.get("status", {}).get("long"),
        "venue": f.get("venue", {}).get("name"),
        "city": f.get("venue", {}).get("city"),
        "league": league.get("name"),
        "round": league.get("round"),
        "home_team": teams.get("home", {}).get("name"),
        "away_team": teams.get("away", {}).get("name"),
        "goals_home": goals.get("home"),
        "goals_away": goals.get("away"),
    }


def shape_prediction(pred_raw: dict) -> dict:
    """Extract prediction and comparison stats into a readable dict."""
    if not pred_raw:
        return {"available": False}

    predictions = pred_raw.get("predictions", {})
    winner = predictions.get("winner", {})
    under_over = predictions.get("under_over")
    goals = predictions.get("goals", {})
    advice = predictions.get("advice")
    win_or_draw = predictions.get("win_or_draw")
    percent = predictions.get("percent", {})

    comparison = pred_raw.get("comparison", {})

    teams = pred_raw.get("teams", {})
    home_last5 = teams.get("home", {}).get("last_5", {})
    away_last5 = teams.get("away", {}).get("last_5", {})

    return {
        "available": True,
        "winner": {
            "id": winner.get("id"),
            "name": winner.get("name"),
            "comment": winner.get("comment"),
        },
        "win_or_draw": win_or_draw,
        "under_over": under_over,
        "goals": {
            "home": goals.get("home"),
            "away": goals.get("away"),
        },
        "advice": advice,
        "win_probabilities": {
            "home": percent.get("home"),
            "draw": percent.get("draw"),
            "away": percent.get("away"),
        },
        "comparison": {
            "form": comparison.get("form", {}),
            "att": comparison.get("att", {}),
            "def": comparison.get("def", {}),
            "poisson_distribution": comparison.get("poisson_distribution", {}),
            "h2h": comparison.get("h2h", {}),
            "goals": comparison.get("goals", {}),
            "total": comparison.get("total", {}),
        },
        "home_last5": {
            "form": home_last5.get("form"),
            "att": home_last5.get("att"),
            "def": home_last5.get("def"),
            "goals": home_last5.get("goals", {}),
        },
        "away_last5": {
            "form": away_last5.get("form"),
            "att": away_last5.get("att"),
            "def": away_last5.get("def"),
            "goals": away_last5.get("goals", {}),
        },
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY:
        print(
            "ERROR: API key not set.\n"
            "Export your key first:  export API_FOOTBALL_KEY='your_key_here'",
            file=sys.stderr,
        )
        sys.exit(1)

    today = date.today()
    tomorrow = today + timedelta(days=1)
    target_dates = [today, tomorrow]

    print(f"Fetching World Cup 2026 fixtures for {today} and {tomorrow}...")

    all_results: list[dict] = []

    for match_date in target_dates:
        print(f"\n── {match_date} ──")
        fixtures = get_fixtures_for_date(match_date)

        if not fixtures:
            print("  No matches found.")
            continue

        print(f"  Found {len(fixtures)} match(es).")

        for fixture_raw in fixtures:
            shaped = shape_fixture(fixture_raw)
            fixture_id = shaped["fixture_id"]
            home = shaped["home_team"]
            away = shaped["away_team"]

            print(f"  Fetching prediction for fixture {fixture_id}: {home} vs {away}")
            pred_raw = get_prediction(fixture_id)
            prediction = shape_prediction(pred_raw)

            all_results.append(
                {
                    "match_date": match_date.isoformat(),
                    "fixture": shaped,
                    "prediction": prediction,
                }
            )

    if not all_results:
        print("\nNo World Cup 2026 matches found for today or tomorrow.")
    else:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
            json.dump(all_results, fh, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(all_results)} match prediction(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
