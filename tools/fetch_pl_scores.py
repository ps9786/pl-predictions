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

football-data.co.uk typically lags a day or more behind full time — the
fixturedownload.com feed (../results_2026_27.csv, written by
fetch_pl_results.sh) usually has a final score within minutes. So for any
match that fixturedownload shows as played but football-data.co.uk doesn't
have yet, we add a minimal fallback row (Fixture, Score, Date only — no
half-time/referee/shots detail, since fixturedownload doesn't provide it) and
mark it "Provisional" so the leaderboard can update immediately instead of
waiting. Because pl/scores.csv is rebuilt from scratch every run, once
football-data.co.uk catches up its authoritative row simply replaces the
fallback on the next run — no manual cleanup needed.

Usage:
  python3 tools/fetch_pl_scores.py
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOOKUP = HERE / "team_lookup.csv"
OUT = ROOT / "pl" / "scores.csv"
FALLBACK_SRC = ROOT / "results_2026_27.csv"

SRC = "https://football-data.co.uk/mmz4281/2627/E0.csv"

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

    fallback = load_fallback_rows(known)
    if fallback:
        print(f"[i] {len(fallback)} match(es) not yet on football-data.co.uk — "
              f"using provisional fixturedownload.com scores instead")
    rows.extend(fallback)

    rows.sort(key=lambda r: (r[0], r[1]))

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _, _, out_row in rows:
            writer.writerow(out_row)

    print(f"Wrote {len(rows)} results to {OUT} ({len(fallback)} provisional)")


if __name__ == "__main__":
    main()
