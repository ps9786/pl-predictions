#!/usr/bin/env python3
"""
Show one player's predictions, game by game, with the points each one scored.

Uses the same pl/selections.csv + pl/scores.csv inputs and 5/3/1 rules as
tools/calculate_pl_scores.py.

Usage:
  python3 tools/player_scores.py "Paul Seward"
  python3 tools/player_scores.py paul          # case-insensitive substring match
  python3 tools/player_scores.py               # prompts interactively
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOOKUP = HERE / "team_lookup.csv"

SCORE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def build_aliases() -> dict[str, str]:
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


def norm_team(name: str) -> str:
    key = re.sub(r"\s+", " ", (name or "").strip()).lower()
    return ALIASES.get(key, key)


def parse_score(value: str) -> tuple[int, int] | None:
    m = SCORE_RE.match(value or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def result_type(score: tuple[int, int]) -> str:
    h, a = score
    return "home" if h > a else "away" if a > h else "draw"


def split_fixture(value: str) -> tuple[str, str] | None:
    parts = re.split(r"\s+-\s+", (value or "").strip(), maxsplit=1)
    if len(parts) != 2:
        return None
    return norm_team(parts[0]), norm_team(parts[1])


def load_scores(path: Path) -> dict[tuple[str, str], tuple[int, int]]:
    by_fixture: dict[tuple[str, str], tuple[int, int]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            key = split_fixture(row.get("Fixture", ""))
            score = parse_score(row.get("Score", ""))
            if key is None or score is None:
                continue
            by_fixture[key] = score
    return by_fixture


def load_selections(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")
        players = [n for n in reader.fieldnames[3:] if n and n.strip()]
        return players, list(reader)


def find_player(query: str, players: list[str]) -> str:
    query_norm = query.strip().casefold()
    exact = [p for p in players if p.strip().casefold() == query_norm]
    if exact:
        return exact[0]
    matches = [p for p in players if query_norm in p.strip().casefold()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"No player matching {query!r}. Known players:\n  " + "\n  ".join(players))
    sys.exit(f"{query!r} is ambiguous — matches: {', '.join(matches)}")


def player_games(player: str, selections, by_fixture):
    """For each fixture row, work out this player's prediction, the actual
    score (if played), and the points it earned (mirrors calculate_pl_scores.score)."""
    games = []
    for row in selections:
        fixture_txt = row.get("FIXTURE", "")
        pred = parse_score(row.get(player, ""))
        key = split_fixture(fixture_txt)
        actual = by_fixture.get(key) if key else None

        points = 0
        note = "not played yet" if actual is None else ""
        if pred is None:
            note = note or "no prediction"
        elif actual is not None:
            if pred == actual:
                # Need every player's prediction to know if it was unique.
                exact_counts = Counter(
                    parse_score(row.get(p, ""))
                    for p in row
                    if p not in ("Round", "Match No", "FIXTURE")
                )
                if exact_counts[pred] == 1:
                    points, note = 5, "exact score, unique"
                else:
                    points, note = 3, "exact score, shared"
            elif result_type(pred) == result_type(actual):
                points, note = 1, "correct result"
            else:
                points, note = 0, "wrong"

        games.append({
            "round": row.get("Round", ""),
            "fixture": fixture_txt,
            "prediction": row.get(player, "") or "-",
            "actual": f"{actual[0]}-{actual[1]}" if actual else "-",
            "points": points,
            "note": note,
        })
    return games


def print_games(player: str, games: list[dict]):
    cols = ["round", "fixture", "prediction", "actual", "points", "note"]
    headers = {"round": "Rnd", "fixture": "Fixture", "prediction": "Predicted",
               "actual": "Actual", "points": "Pts", "note": "Note"}
    widths = {c: max(len(headers[c]), *(len(str(g[c])) for g in games)) for c in cols}

    total = sum(g["points"] for g in games)
    print(f"\n{player} — {total} point{'s' if total != 1 else ''} total\n")
    print("  ".join(headers[c].ljust(widths[c]) for c in cols))
    print("  ".join("-" * widths[c] for c in cols))
    for g in games:
        print("  ".join(
            (str(g[c]).rjust(widths[c]) if c == "points" else str(g[c]).ljust(widths[c]))
            for c in cols))


def main() -> int:
    ap = argparse.ArgumentParser(description="Show a player's predictions and points, game by game.")
    ap.add_argument("player", nargs="?", help="Player name (or a substring of it). Prompted if omitted.")
    ap.add_argument("--selections", type=Path, default=ROOT / "pl" / "selections.csv")
    ap.add_argument("--scores", type=Path, default=ROOT / "pl" / "scores.csv")
    args = ap.parse_args()

    try:
        players, selections = load_selections(args.selections)
        by_fixture = load_scores(args.scores)
    except (OSError, ValueError) as e:
        sys.exit(f"Error: {e}")

    query = args.player or input("Player name: ")
    player = find_player(query, players)

    games = player_games(player, selections, by_fixture)
    print_games(player, games)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
