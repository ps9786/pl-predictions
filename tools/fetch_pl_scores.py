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

Usage:
  python3 tools/fetch_pl_scores.py
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOOKUP = HERE / "team_lookup.csv"
OUT = ROOT / "pl" / "scores.csv"

SRC = "https://football-data.co.uk/mmz4281/2627/E0.csv"

EXTRA_FIELDS = [
    "HTHG", "HTAG", "HTR", "Referee",
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
]


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


def main() -> None:
    print(f"Fetching {SRC} ...")
    with urllib.request.urlopen(SRC, timeout=30) as resp:
        text = resp.read().decode("utf-8-sig")

    reader = csv.DictReader(text.splitlines())
    rows = []
    for row in reader:
        if not (row.get("HomeTeam") and row.get("FTHG") and row.get("FTAG")):
            continue
        home = short_name(row["HomeTeam"])
        away = short_name(row["AwayTeam"])
        date = datetime.strptime(row["Date"], "%d/%m/%Y").strftime("%Y-%m-%d")
        out_row = {
            "Fixture": f"{home} - {away}",
            "Score": f"{row['FTHG']}-{row['FTAG']}",
            "Date": date,
        }
        for field in EXTRA_FIELDS:
            out_row[field] = row.get(field, "")
        rows.append((row["Date"], row.get("Time", ""), out_row))

    rows.sort(key=lambda r: (datetime.strptime(r[0], "%d/%m/%Y"), r[1]))

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Fixture", "Score", "Date"] + EXTRA_FIELDS)
        writer.writeheader()
        for _, _, out_row in rows:
            writer.writerow(out_row)

    print(f"Wrote {len(rows)} results to {OUT}")


if __name__ == "__main__":
    main()
