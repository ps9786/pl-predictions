#!/usr/bin/env python3
"""
Build the Premier League prediction scores table (league table) from
selections.csv, using the same rules as the World Cup game:

  * 5 points — exact score AND you are the ONLY player who predicted it
  * 3 points — exact score, but one or more other players predicted the same
  * 1 point  — correct result (home win / draw / away win) only
  * 0        — otherwise

selections.csv layout (see wc/selections.csv for an example):
  Match Date,Match No,FIXTURE,<Player 1>,<Player 2>,...
  <date>,<no>,<Home v Away>,<H-A>,<H-A>,...

Actual results come from results_2026_27.csv (produced by fetch_pl_results.sh):
  Match Number,Round Number,Date,Home Team,Away Team,Result   (Result = "H - A")

Matches are joined on Match No when present, otherwise on the normalised
fixture team names, so short names ("Forest"), feed names ("Nott'm Forest")
and full names ("Nottingham Forest") all line up.

Usage:
  python3 tools/calculate_scores_table.py \
      --selections selections.csv --results results_2026_27.csv \
      --output league_table.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

HERE   = Path(__file__).resolve().parent
ROOT   = HERE.parent
LOOKUP = HERE / "team_lookup.csv"

SCORE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


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
    # accept "A v B", "A v. B", "A vs B", "A vs. B"
    parts = re.split(r"\s+vs?\.?\s+", (value or "").strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None
    return norm_team(parts[0]), norm_team(parts[1])


# ── Load results ────────────────────────────────────────────────────────────
def load_results(path: Path):
    by_fixture: dict[tuple[str, str], tuple[int, int]] = {}
    by_number: dict[str, tuple[int, int]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            score = parse_score(row.get("Result", ""))
            if score is None:
                continue
            by_fixture[(norm_team(row.get("Home Team", "")),
                        norm_team(row.get("Away Team", "")))] = score
            num = (row.get("Match Number") or "").strip()
            if num:
                by_number[num] = score
    return by_fixture, by_number


def load_selections(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")
        players = [n for n in reader.fieldnames[3:] if n and n.strip()]
        return players, list(reader)


# ── Scoring ─────────────────────────────────────────────────────────────────
def score(players, selections, by_fixture, by_number=None):
    """by_number is only used when --use-match-numbers is passed: the selections'
    'Match No' column must then hold the OFFICIAL feed match numbers (1-380).
    By default it is ignored, because a per-round numbering scheme would silently
    join rows to unrelated fixtures."""
    table = {p: {"Player": p.strip(), "1": 0, "3": 0, "5": 0, "Total": 0} for p in players}
    scored = 0
    for row in selections:
        fixture_txt = row.get("FIXTURE", "")
        key = split_fixture(fixture_txt)
        if key is None and fixture_txt.strip():
            print(f"[!] Cannot parse FIXTURE {fixture_txt!r} — row skipped "
                  f"(expected 'Home v Away').", file=sys.stderr)
        actual = by_fixture.get(key) if key else None
        if actual is None and by_number is not None:
            actual = by_number.get((row.get("Match No") or "").strip())
        if actual is None:
            continue

        scored += 1
        outcome = result_type(actual)
        preds = {p: parse_score(row.get(p, "")) for p in players}
        exact_counts = Counter(s for s in preds.values() if s is not None)

        for p, pred in preds.items():
            if pred is None:
                continue
            if pred == actual:
                if exact_counts[pred] == 1:
                    table[p]["5"] += 1; table[p]["Total"] += 5
                else:
                    table[p]["3"] += 1; table[p]["Total"] += 3
            elif result_type(pred) == outcome:
                table[p]["1"] += 1; table[p]["Total"] += 1

    rows = sorted(table.values(), key=lambda r: (
        -r["Total"], -(r["5"] + r["3"]), -r["5"], -r["3"], -r["1"], r["Player"].casefold()))
    return rows, scored


def to_out_rows(rows):
    return [{
        "Player": r["Player"],
        "Score": r["Total"],
        "Correct Scores": r["5"] + r["3"],
        "5 Pointers": r["5"],
        "3 Pointers": r["3"],
        "1 Pointers": r["1"],
    } for r in rows]


def print_table(out_rows):
    cols = ["Pos", "Player", "Score", "Correct Scores", "5 Pointers", "3 Pointers", "1 Pointers"]
    printable, prev_total, prev_pos = [], None, 0
    for i, r in enumerate(out_rows, 1):
        pos = prev_pos if r["Score"] == prev_total else i
        prev_total, prev_pos = r["Score"], pos
        printable.append({"Pos": pos, **r})
    widths = {c: max([len(c)] + [len(str(r[c])) for r in printable]) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    print("  ".join("-" * widths[c] for c in cols))
    for r in printable:
        print("  ".join(
            (str(r[c]).ljust(widths[c]) if c == "Player" else str(r[c]).rjust(widths[c]))
            for c in cols))


def write_csv(path: Path, out_rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Player", "Score", "Correct Scores",
                                          "5 Pointers", "3 Pointers", "1 Pointers"])
        w.writeheader()
        w.writerows(out_rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the PL prediction scores table.")
    ap.add_argument("--selections", type=Path, default=ROOT / "selections.csv")
    ap.add_argument("--results", type=Path, default=ROOT / "results_2026_27.csv")
    ap.add_argument("--output", type=Path, default=ROOT / "league_table.csv")
    ap.add_argument("--use-match-numbers", action="store_true",
                    help="Also join on 'Match No' — ONLY safe when selections.csv "
                         "uses the official feed match numbers (1-380).")
    args = ap.parse_args()

    try:
        by_fixture, by_number = load_results(args.results)
        players, selections = load_selections(args.selections)
        rows, scored = score(players, selections, by_fixture,
                             by_number if args.use_match_numbers else None)
    except (OSError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    out_rows = to_out_rows(rows)
    print_table(out_rows)
    print(f"\nScored matches: {scored} / {len(selections)}")
    write_csv(args.output, out_rows)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
