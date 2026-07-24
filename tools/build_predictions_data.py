#!/usr/bin/env python3
"""
Build matchup_summary.csv (head-to-head) and team_form_summary.csv (last-5 form)
for the fixtures in games.txt, using TheSportsDB.

games.txt is the source of truth. Its short team names (e.g. "Man Utd", "Spurs",
"Palace") are mapped to TheSportsDB clubs via tools/team_lookup.csv, and the
output CSVs are keyed back by those SAME short names so plp.html matches them.

Endpoints used (require a valid TheSportsDB PREMIUM key for full data):
  - searchevents.php?e=Home_vs_Away&s=SEASON   -> head-to-head results
  - eventslast.php?id=TEAM_ID                  -> a team's last 5 matches (form)

The key is read from the SPORTSDB env var (falls back to the free test key
"123", on which eventslast only returns 1 result — premium returns 5).

Run:  SPORTSDB=<your_key> python3 tools/build_predictions_data.py
"""

import csv
import os
import sys
import time
import json
import urllib.parse
import urllib.request
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY   = os.getenv("SPORTSDB", "123")
BASE_URL  = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"
H2H_SEASONS_BACK = 3          # how many seasons of head-to-head to consider
REQUEST_PAUSE    = 1.0        # polite delay between calls (free key is rate-limited)

HERE      = os.path.dirname(os.path.abspath(__file__))
ROOT      = os.path.dirname(HERE)                       # pl-predictions/
GAMES_TXT = os.path.join(ROOT, "games.txt")
LOOKUP    = os.path.join(HERE, "team_lookup.csv")
H2H_OUT   = os.path.join(ROOT, "matchup_summary.csv")
FORM_OUT  = os.path.join(ROOT, "team_form_summary.csv")


# ── HTTP with 429 handling ──────────────────────────────────────────────────
def api_get(path):
    url = f"{BASE_URL}/{path}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=25) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  [!] Rate limited (429) — pausing 60s…")
                time.sleep(60)
                continue
            print(f"  [!] HTTP {e.code} for {path}")
            return None
        except Exception as e:
            print(f"  [!] Request failed ({e}) for {path}")
            return None
    return None


# ── Season helpers ──────────────────────────────────────────────────────────
def recent_seasons(n):
    """Last n season strings like '2025-2026', newest last."""
    now = datetime.now()
    start = now.year if now.month >= 8 else now.year - 1   # PL season starts Aug
    return [f"{y}-{y + 1}" for y in range(start - n + 1, start + 1)]


# ── Load lookup + fixtures ──────────────────────────────────────────────────
def load_lookup():
    by_short = {}
    with open(LOOKUP, newline="") as f:
        for row in csv.DictReader(f):
            by_short[row["short"].strip().lower()] = {
                "short": row["short"].strip(),
                "name":  row["thesportsdb_name"].strip(),
                "id":    row["thesportsdb_id"].strip(),
            }
    return by_short


def parse_games():
    fixtures = []
    with open(GAMES_TXT) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            game = line.split(",", 1)[0].strip()      # drop any trailing note
            if " - " not in game:
                continue
            home, away = (p.strip() for p in game.split(" - ", 1))
            if home and away:
                fixtures.append((home, away))
    return fixtures


# ── Head-to-head ────────────────────────────────────────────────────────────
def slug(name):
    return name.replace(" ", "_")


def fetch_events(name_a, name_b, season):
    data = api_get(f"searchevents.php?e={urllib.parse.quote(slug(name_a))}_vs_"
                   f"{urllib.parse.quote(slug(name_b))}&s={season}")
    time.sleep(REQUEST_PAUSE)
    return (data or {}).get("event") or []


def get_h2h(home, away, seasons):
    """Return up to 5 recent scores 'H-A' from the games.txt HOME team's view."""
    events = []
    for season in seasons:
        events += fetch_events(home["name"], away["name"], season)   # home vs away
        events += fetch_events(away["name"], home["name"], season)   # away vs home
    if not events:
        return [""] * 5

    events.sort(key=lambda e: e.get("dateEvent", ""), reverse=True)
    aligned = []
    for e in events[:5]:
        if e.get("strStatus") == "Match Postponed":
            aligned.append("P")
            continue
        hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
        if hs is None or as_ is None:
            continue
        api_home = (e.get("strHomeTeam") or "").strip().lower()
        if api_home == home["name"].strip().lower():
            aligned.append(f"{hs}-{as_}")
        else:
            aligned.append(f"{as_}-{hs}")     # flip to home team's perspective
    while len(aligned) < 5:
        aligned.append("")
    return aligned[:5]


# ── Form (last 5) ───────────────────────────────────────────────────────────
def get_form(team):
    """Return [oldest … newest] of 5 results: W/D/L (P postponed, C cancelled)."""
    data = api_get(f"eventslast.php?id={team['id']}")
    time.sleep(REQUEST_PAUSE)
    events = (data or {}).get("results") or []
    if not events:
        return [""] * 5

    out = []  # newest first
    for e in events[:5]:
        status = e.get("strStatus", "")
        if status == "Match Postponed":
            out.append("P"); continue
        if status == "Match Cancelled":
            out.append("C"); continue
        hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
        if hs is None or as_ is None:
            out.append("?"); continue
        h, a = int(hs), int(as_)
        if str(e.get("idHomeTeam")) == str(team["id"]):
            out.append("W" if h > a else "L" if h < a else "D")
        else:
            out.append("W" if a > h else "L" if a < h else "D")
    while len(out) < 5:
        out.append("")
    return list(reversed(out[:5]))   # oldest first -> newest on the right


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    if API_KEY in ("123", "1", "3"):
        print("[i] Using the FREE test key — form (eventslast) returns only 1 game. "
              "Set SPORTSDB=<premium key> for full last-5 form.\n")

    lookup   = load_lookup()
    fixtures = parse_games()
    if not fixtures:
        print(f"No fixtures found in {GAMES_TXT}"); sys.exit(1)

    seasons = recent_seasons(H2H_SEASONS_BACK)
    print(f"[i] {len(fixtures)} fixtures · H2H seasons: {', '.join(seasons)}\n")

    def resolve(short):
        t = lookup.get(short.lower())
        if not t:
            print(f"  [!] '{short}' not in team_lookup.csv — add it (H2H uses the "
                  f"raw name, form skipped).")
            return {"short": short, "name": short, "id": None}
        return t

    h2h_rows, form_rows, seen = [], [], {}
    for home_s, away_s in fixtures:
        home, away = resolve(home_s), resolve(away_s)
        print(f"[+] {home_s} vs {away_s}")

        h2h_rows.append([home_s, away_s] + get_h2h(home, away, seasons))

        for short, team in ((home_s, home), (away_s, away)):
            if short.lower() in seen or team["id"] is None:
                continue
            seen[short.lower()] = True
            print(f"    form: {short}")
            form_rows.append([short] + get_form(team))

    with open(H2H_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Home Team", "Away Team", "Score 1", "Score 2", "Score 3", "Score 4", "Score 5"])
        w.writerows(h2h_rows)

    with open(FORM_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Team", "Game 5", "Game 4", "Game 3", "Game 2", "Game 1"])
        w.writerows(form_rows)

    print(f"\nDone.\n  {H2H_OUT}  ({len(h2h_rows)} fixtures)"
          f"\n  {FORM_OUT}  ({len(form_rows)} teams)")


if __name__ == "__main__":
    main()
