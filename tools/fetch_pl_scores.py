#!/usr/bin/env python3
"""
Regenerate pl/scores.csv from football-data.co.uk's results feed:

  https://football-data.co.uk/mmz4281/2627/E0.csv

That file lists one row per PLAYED match (full-time score, half-time score,
referee, shots/corners/cards — no future fixtures), in a format documented at
https://football-data.co.uk/notes.txt. Team names there ("Man United",
"Nott'm Forest", "Tottenham", "Aston Villa", "Crystal Palace", ...) are mapped
to the game's short names via tools/team_lookup.csv (the same alias table
build_predictions_data.py / calculate_pl_scores.py use), so the output stays
keyed the way plp.html / pl/index.html / pl/player.html expect:

  Fixture,Score,...
  Arsenal - Coventry,3-0,...

pl/scores.csv is fully REPLACED each run (football-data.co.uk is treated as
the source of truth for played-match results), sorted by kick-off date/time.
Columns after Score are extra match detail (half-time score, referee, shots,
corners, cards) kept in case the game wants them later; betting-odds columns
from the source are dropped.

football-data.co.uk typically lags a day or more behind full time. Two
fallbacks fill matches it doesn't have yet, in order:

  1. TheSportsDB (api/v1/json/<SPORTSDB key>/eventsseason.php), if the
     SPORTSDB env var is set. With a premium key this returns the full
     season in one call (the free key truncates to ~15 events, so this tier
     is skipped without a real key) and, for each finished match not yet on
     football-data.co.uk, a second call (lookupeventstats.php) fetches shots/
     corners/fouls/cards — comparable detail to football-data.co.uk, just
     from a different source.
  2. The fixturedownload.com feed (../results_2026_27.csv, written by
     fetch_pl_results.sh), which usually has a final score within minutes but
     no match-stat detail — used as a last resort with just Fixture/Score/Date.

Either way the fallback row is marked "Provisional" so the leaderboard can
update immediately instead of waiting on football-data.co.uk. Because
pl/scores.csv is rebuilt from scratch every run, once football-data.co.uk
catches up its authoritative row simply replaces the fallback on the next
run — no manual cleanup needed.

Usage:
  python3 tools/fetch_pl_scores.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOOKUP = HERE / "team_lookup.csv"
OUT = ROOT / "pl" / "scores.csv"
FALLBACK_SRC = ROOT / "results_2026_27.csv"

SRC = "https://football-data.co.uk/mmz4281/2627/E0.csv"

SPORTSDB_KEY = os.environ.get("SPORTSDB")
SPORTSDB_LEAGUE_ID = "4328"    # English Premier League
SPORTSDB_SEASON = "2026-2027"
SPORTSDB_STAT_MAP = {          # TheSportsDB strStat -> our (home field, away field)
    "Total Shots": ("HS", "AS"),
    "Shots on Goal": ("HST", "AST"),
    "Fouls": ("HF", "AF"),
    "Corner Kicks": ("HC", "AC"),
    "Yellow Cards": ("HY", "AY"),
    "Red Cards": ("HR", "AR"),
}

EXTRA_FIELDS = [
    "HTHG", "HTAG", "HTR", "Referee",
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
]
FIELDNAMES = ["Fixture", "Score", "Date"] + EXTRA_FIELDS + ["Provisional"]


def build_aliases() -> dict[str, str]:
    """All team-name spellings come from team_lookup.csv (the single source):
    the short name, the TheSportsDB name, and any extra `aliases` (;-separated)."""
    aliases: dict[str, str] = {}
    if LOOKUP.exists():
        with LOOKUP.open(newline="") as f:
            for row in csv.DictReader(f):
                short = row["short"].strip()
                aliases[short.lower()] = short
                aliases[row["thesportsdb_name"].strip().lower()] = short
                for alias in (row.get("aliases") or "").split(";"):
                    alias = alias.strip()
                    if alias:
                        aliases[alias.lower()] = short
    return aliases


ALIASES = build_aliases()


def short_name(team: str) -> str:
    short = ALIASES.get(team.strip().lower())
    if not short:
        sys.exit(f"[!] '{team}' not in tools/team_lookup.csv — add a short/alias for it")
    return short


def sportsdb_get(path: str):
    url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}/{path}"
    with urllib.request.urlopen(url, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_thesportsdb_rows(known: set[tuple[str, str]]) -> list[tuple[date, str, dict]]:
    """Fixture/Score/Date(+stats) rows from TheSportsDB, for finished matches
    football-data.co.uk doesn't have yet. Needs a premium SPORTSDB key — the
    free key truncates eventsseason.php to ~15 events, so this tier is
    skipped entirely without one."""
    if not SPORTSDB_KEY:
        return []

    try:
        data = sportsdb_get(f"eventsseason.php?id={SPORTSDB_LEAGUE_ID}&s={SPORTSDB_SEASON}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"[!] TheSportsDB eventsseason.php failed: {e}", file=sys.stderr)
        return []

    entries = []
    for e in (data or {}).get("events") or []:
        if e.get("strStatus") != "FT":
            continue
        hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
        if hs is None or as_ is None:
            continue
        home = short_name(e["strHomeTeam"])
        away = short_name(e["strAwayTeam"])
        if (home, away) in known:
            continue

        out_row = {"Fixture": f"{home} - {away}", "Score": f"{hs}-{as_}", "Date": e.get("dateEvent") or ""}
        for field in EXTRA_FIELDS:
            out_row[field] = ""
        out_row["Referee"] = (e.get("strOfficial") or "").strip()

        try:
            stats = sportsdb_get(f"lookupeventstats.php?id={e['idEvent']}").get("eventstats") or []
            for s in stats:
                fields = SPORTSDB_STAT_MAP.get(s.get("strStat"))
                if fields:
                    out_row[fields[0]] = s.get("intHome") or ""
                    out_row[fields[1]] = s.get("intAway") or ""
            time.sleep(0.3)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, AttributeError):
            pass   # bare score is still useful without the extra stats

        out_row["Provisional"] = "yes"
        known.add((home, away))
        match_date = datetime.strptime(e["dateEvent"], "%Y-%m-%d").date()
        entries.append((match_date, "", out_row))
    return entries


def load_fallback_rows(known: set[tuple[str, str]]) -> list[tuple[date, str, dict]]:
    """Minimal Fixture/Score/Date rows from fixturedownload.com's
    results_2026_27.csv, for played matches football-data.co.uk doesn't have
    yet (`known` = the (home, away) pairs football-data.co.uk already covers)."""
    if not FALLBACK_SRC.exists():
        return []

    entries = []
    with FALLBACK_SRC.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            result = (row.get("Result") or "").strip()
            if not result or " - " not in result:
                continue
            home = short_name(row["Home Team"])
            away = short_name(row["Away Team"])
            if (home, away) in known:
                continue
            hs, as_ = result.split(" - ", 1)
            match_date = row.get("Date") or ""
            out_row = {"Fixture": f"{home} - {away}", "Score": f"{hs}-{as_}", "Date": match_date}
            for field in EXTRA_FIELDS:
                out_row[field] = ""
            out_row["Provisional"] = "yes"
            entries.append((datetime.strptime(match_date, "%Y-%m-%d").date(), "", out_row))
    return entries


def main() -> None:
    print(f"Fetching {SRC} ...")
    with urllib.request.urlopen(SRC, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")

    reader = csv.DictReader(text.splitlines())
    rows = []
    known: set[tuple[str, str]] = set()
    for row in reader:
        if not (row.get("HomeTeam") and row.get("FTHG") and row.get("FTAG")):
            continue
        home = short_name(row["HomeTeam"])
        away = short_name(row["AwayTeam"])
        known.add((home, away))
        match_date = datetime.strptime(row["Date"], "%d/%m/%Y").date()
        out_row = {
            "Fixture": f"{home} - {away}",
            "Score": f"{row['FTHG']}-{row['FTAG']}",
            "Date": match_date.strftime("%Y-%m-%d"),
        }
        for field in EXTRA_FIELDS:
            out_row[field] = row.get(field, "")
        out_row["Provisional"] = ""
        rows.append((match_date, row.get("Time", ""), out_row))

    sportsdb_rows = load_thesportsdb_rows(known)
    if sportsdb_rows:
        print(f"[i] {len(sportsdb_rows)} match(es) not yet on football-data.co.uk — "
              f"using provisional TheSportsDB scores instead")
    rows.extend(sportsdb_rows)

    fallback = load_fallback_rows(known)
    if fallback:
        print(f"[i] {len(fallback)} match(es) not yet on football-data.co.uk or TheSportsDB — "
              f"using provisional fixturedownload.com scores instead")
    rows.extend(fallback)

    rows.sort(key=lambda r: (r[0], r[1]))

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _, _, out_row in rows:
            writer.writerow(out_row)

    provisional = len(sportsdb_rows) + len(fallback)
    print(f"Wrote {len(rows)} results to {OUT} ({provisional} provisional)")


if __name__ == "__main__":
    main()
