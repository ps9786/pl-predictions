#!/usr/bin/env python3
"""
Build pl/stats.json — "fun stats" about how people predict, computed purely
from pl/selections.csv (the picks themselves), independent of actual results.

Grouping-dependent stats (unique / predictable / random / similar / twins)
are computed twice, under two different notions of "same scoreline":

  * by_score  — 1-0 and 0-1 are different picks (home/away matters).
  * by_margin — 1-0 and 0-1 count as the same pick (home/away ignored,
                e.g. "2-1" covers both 2-1 and 1-2). pl/stats.html has a
                toggle to switch between the two.

  * Most Unique       — count of picks where a player was the ONLY one who
                         predicted that scoreline for that match.
  * Most Predictable  — count of picks that matched the match's plurality
                         (single most-picked) scoreline. Matches with no
                         single most-popular scoreline (a tie at the top,
                         including "everyone picked something different")
                         don't count toward this for anyone.
  * Most Random       — Shannon entropy of the distinct scorelines a player
                         personally uses across all their picks, normalised
                         to 0-1 (1 = every pick different; 0 = always the same).
  * Most Similar Selections — the inverse: the share of a player's picks that
                         are their single favourite scoreline.
  * Prediction twins  — the pair of players whose scorelines match each
                         other most often.

  * Bonus (unaffected by the grouping mode): average goals predicted per
    game, and home/draw/away bias vs the field average.

Usage:
  python3 tools/calculate_pl_stats.py \
      --selections pl/selections.csv --output pl/stats.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

SCORE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")

Score = tuple[int, int]


def parse_score(value: str) -> Score | None:
    m = SCORE_RE.match(value or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def result_type(score: Score) -> str:
    h, a = score
    return "home" if h > a else "away" if a > h else "draw"


def label_by_score(score: Score) -> str:
    return f"{score[0]}-{score[1]}"


def label_by_margin(score: Score) -> str:
    return f"{max(score)}-{min(score)}"


def load_selections(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")
        players = [n for n in reader.fieldnames[3:] if n and n.strip()]
        return players, list(reader)


def entropy_bits(labels: list[str]) -> tuple[float, float]:
    n = len(labels)
    counts = Counter(labels)
    raw = -sum((c / n) * math.log2(c / n) for c in counts.values())
    max_possible = math.log2(n) if n > 1 else 0.0
    normalised = raw / max_possible if max_possible > 0 else 0.0
    return raw, normalised


def compute_group(
    players: list[str],
    picks_by_player: dict[str, list[Score]],
    match_picks: list[dict[str, Score]],
    label_fn: Callable[[Score], str],
) -> dict:
    unique_counts = Counter()
    predictable_counts = Counter()

    for preds in match_picks:
        labelled = {p: label_fn(s) for p, s in preds.items()}
        counts = Counter(labelled.values())
        for p, label in labelled.items():
            if counts[label] == 1:
                unique_counts[p] += 1

        max_count = max(counts.values())
        top_labels = [label for label, c in counts.items() if c == max_count]
        if max_count > 1 and len(top_labels) == 1:
            plurality = top_labels[0]
            for p, label in labelled.items():
                if label == plurality:
                    predictable_counts[p] += 1

    unique_list = [
        {"player": p, "count": unique_counts.get(p, 0), "picks": len(picks_by_player[p])}
        for p in players if picks_by_player[p]
    ]
    unique_list.sort(key=lambda r: (-r["count"], r["player"].casefold()))

    predictable_list = [
        {"player": p, "count": predictable_counts.get(p, 0), "picks": len(picks_by_player[p])}
        for p in players if picks_by_player[p]
    ]
    predictable_list.sort(key=lambda r: (-r["count"], r["player"].casefold()))

    random_list = []
    similar_list = []
    for p in players:
        scores = picks_by_player[p]
        if not scores:
            continue
        labels = [label_fn(s) for s in scores]

        raw, normalised = entropy_bits(labels)
        random_list.append({"player": p, "entropy": round(raw, 3),
                             "normalised": round(normalised, 3), "picks": len(scores)})

        counts = Counter(labels)
        favourite_label, favourite_count = counts.most_common(1)[0]
        similar_list.append({
            "player": p,
            "favourite_score": favourite_label,
            "count": favourite_count,
            "share": round(favourite_count / len(scores), 3),
            "picks": len(scores),
        })

    random_list.sort(key=lambda r: (-r["normalised"], r["player"].casefold()))
    similar_list.sort(key=lambda r: (-r["share"], r["player"].casefold()))

    # Prediction twins: for every pair of players, count matches where both
    # submitted a pick and their (labelled) scorelines agree.
    pair_matches = Counter()
    pair_agreements = Counter()
    for preds in match_picks:
        labelled = {p: label_fn(s) for p, s in preds.items()}
        names = list(labelled.keys())
        for a, b in combinations(names, 2):
            key = tuple(sorted((a, b)))
            pair_matches[key] += 1
            if labelled[a] == labelled[b]:
                pair_agreements[key] += 1

    twins_list = [
        {"player_a": a, "player_b": b, "matches": pair_agreements[(a, b)],
         "shared_considered": pair_matches[(a, b)],
         "agreement_pct": round(100 * pair_agreements[(a, b)] / pair_matches[(a, b)], 1)}
        for (a, b) in pair_matches
        if pair_matches[(a, b)] >= 3  # ignore pairs with barely any overlap
    ]
    twins_list.sort(key=lambda r: (-r["matches"], -r["agreement_pct"]))

    return {
        "unique": unique_list,
        "predictable": predictable_list,
        "random": random_list,
        "similar": similar_list,
        "twins": twins_list[:10],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build pl/stats.json from pl/selections.csv")
    ap.add_argument("--selections", type=Path, default=ROOT / "pl" / "selections.csv")
    ap.add_argument("--output", type=Path, default=ROOT / "pl" / "stats.json")
    args = ap.parse_args()

    try:
        players, selections = load_selections(args.selections)
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # picks_by_player[player] = list of (home, away) exact scores they predicted
    picks_by_player: dict[str, list[Score]] = defaultdict(list)
    # per match, {player: pick} — used by compute_group() and the bonus stats
    match_picks: list[dict[str, Score]] = []
    matches_considered = 0

    for row in selections:
        preds = {p: parse_score(row.get(p, "")) for p in players}
        preds = {p: s for p, s in preds.items() if s is not None}
        if not preds:
            continue
        matches_considered += 1
        match_picks.append(preds)
        for p, s in preds.items():
            picks_by_player[p].append(s)

    by_score = compute_group(players, picks_by_player, match_picks, label_by_score)
    by_margin = compute_group(players, picks_by_player, match_picks, label_by_margin)

    goals_list = []
    bias_list = []
    field_result_counts = Counter()
    field_total_picks = 0

    for p in players:
        scores = picks_by_player[p]
        if not scores:
            continue

        avg_goals = sum(h + a for h, a in scores) / len(scores)
        goals_list.append({"player": p, "avg_goals": round(avg_goals, 2), "picks": len(scores)})

        results = Counter(result_type(s) for s in scores)
        field_result_counts.update(results)
        field_total_picks += len(scores)
        n = len(scores)
        bias_list.append({
            "player": p,
            "home_pct": round(100 * results.get("home", 0) / n, 1),
            "draw_pct": round(100 * results.get("draw", 0) / n, 1),
            "away_pct": round(100 * results.get("away", 0) / n, 1),
            "picks": n,
        })

    goals_optimists = sorted(goals_list, key=lambda r: (-r["avg_goals"], r["player"].casefold()))
    goals_pessimists = sorted(goals_list, key=lambda r: (r["avg_goals"], r["player"].casefold()))
    bias_list.sort(key=lambda r: r["player"].casefold())

    field_average = {
        "home_pct": round(100 * field_result_counts.get("home", 0) / field_total_picks, 1),
        "draw_pct": round(100 * field_result_counts.get("draw", 0) / field_total_picks, 1),
        "away_pct": round(100 * field_result_counts.get("away", 0) / field_total_picks, 1),
    } if field_total_picks else {"home_pct": 0, "draw_pct": 0, "away_pct": 0}

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_matches": matches_considered,
        "total_players": len([p for p in players if picks_by_player[p]]),
        "by_score": by_score,
        "by_margin": by_margin,
        "goals_optimists": goals_optimists[:10],
        "goals_pessimists": goals_pessimists[:10],
        "bias": bias_list,
        "field_average": field_average,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"Wrote {args.output} ({matches_considered} matches, {stats['total_players']} players)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
