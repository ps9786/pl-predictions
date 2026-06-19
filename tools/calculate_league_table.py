#!/usr/bin/env python3
"""Calculate the World Cup prediction league table."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


SCORE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")


def normalise_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", value.strip()).casefold()


def fixture_key(home: str, away: str) -> tuple[str, str]:
    return normalise_name(home), normalise_name(away)


def parse_score(value: str) -> tuple[int, int] | None:
    match = SCORE_RE.match(value or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def result_type(score: tuple[int, int]) -> str:
    home, away = score
    if home > away:
        return "home"
    if away > home:
        return "away"
    return "draw"


def load_results(path: Path) -> tuple[dict[tuple[str, str], tuple[int, int]], dict[str, tuple[int, int]]]:
    by_fixture: dict[tuple[str, str], tuple[int, int]] = {}
    by_match_number: dict[str, tuple[int, int]] = {}

    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            score = parse_score(row.get("Result", ""))
            if score is None:
                continue

            by_fixture[fixture_key(row["Home Team"], row["Away Team"])] = score
            by_match_number[row["Match Number"].strip()] = score

    return by_fixture, by_match_number


def selection_fixture_key(value: str) -> tuple[str, str] | None:
    parts = re.split(r"\s+v\s+", value.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return None
    return fixture_key(parts[0], parts[1])


def load_selections(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no header row")

        players = [name for name in reader.fieldnames[3:] if name and name.strip()]
        return players, list(reader)


def score_predictions(
    players: list[str],
    selections: list[dict[str, str]],
    results_by_fixture: dict[tuple[str, str], tuple[int, int]],
    results_by_match_number: dict[str, tuple[int, int]],
) -> tuple[list[dict[str, int | str]], int]:
    table = {
        player: {"Player": player.strip(), "1 point": 0, "3 points": 0, "5 points": 0, "Total": 0}
        for player in players
    }
    scored_matches = 0

    for row in selections:
        key = selection_fixture_key(row.get("FIXTURE", ""))
        actual_score = results_by_fixture.get(key) if key else None
        if actual_score is None:
            actual_score = results_by_match_number.get(row.get("Match No", "").strip())
        if actual_score is None:
            continue

        scored_matches += 1
        actual_result = result_type(actual_score)
        predictions = {player: parse_score(row.get(player, "")) for player in players}
        exact_prediction_counts = Counter(score for score in predictions.values() if score is not None)

        for player, prediction in predictions.items():
            if prediction is None:
                continue

            if prediction == actual_score:
                if exact_prediction_counts[prediction] == 1:
                    table[player]["5 points"] += 1
                    table[player]["Total"] += 5
                else:
                    table[player]["3 points"] += 1
                    table[player]["Total"] += 3
            elif result_type(prediction) == actual_result:
                table[player]["1 point"] += 1
                table[player]["Total"] += 1

    league_table = sorted(
        table.values(),
        key=lambda row: (
            -int(row["Total"]),
            -(int(row["5 points"]) + int(row["3 points"])),
            -int(row["5 points"]),
            -int(row["3 points"]),
            -int(row["1 point"]),
            str(row["Player"]).casefold(),
        ),
    )
    return league_table, scored_matches


def print_table(rows: list[dict[str, int | str]]) -> None:
    columns = ["Pos", "Player", "Score", "Correct Scores", "5 Pointers", "3 Pointers", "1 Pointers"]
    printable_rows = []
    previous_total = None
    previous_position = 0

    for index, row in enumerate(rows, start=1):
        total = row["Total"]
        position = previous_position if total == previous_total else index
        previous_total = total
        previous_position = position
        printable_rows.append(
            {
                "Pos": position,
                "Player": row["Player"],
                "Score": row["Total"],
                "Correct Scores": int(row["5 points"]) + int(row["3 points"]),
                "5 Pointers": row["5 points"],
                "3 Pointers": row["3 points"],
                "1 Pointers": row["1 point"],
            }
        )

    widths = {
        column: max(len(column), *(len(str(row[column])) for row in printable_rows))
        for column in columns
    }

    print("  ".join(column.ljust(widths[column]) for column in columns))
    print("  ".join("-" * widths[column] for column in columns))
    for row in printable_rows:
        print(
            "  ".join(
                str(row[column]).rjust(widths[column]) if column != "Player" else str(row[column]).ljust(widths[column])
                for column in columns
            )
        )


def write_csv(path: Path, rows: list[dict[str, int | str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Player", "Score", "Correct Scores", "5 Pointers", "3 Pointers", "1 Pointers"],
        )
        writer.writeheader()
        writer.writerows(
            {
                "Player": row["Player"],
                "Score": row["Total"],
                "Correct Scores": int(row["5 points"]) + int(row["3 points"]),
                "5 Pointers": row["5 points"],
                "3 Pointers": row["3 points"],
                "1 Pointers": row["1 point"],
            }
            for row in rows
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Calculate the friends' World Cup prediction league table.")
    parser.add_argument("--results", default="public/wc2026.csv", type=Path, help="Path to wc2026.csv")
    parser.add_argument("--selections", default="public/selections.csv", type=Path, help="Path to selections.csv")
    parser.add_argument("--output", type=Path, help="Optional CSV output path")
    args = parser.parse_args()

    try:
        results_by_fixture, results_by_match_number = load_results(args.results)
        players, selections = load_selections(args.selections)
        rows, scored_matches = score_predictions(players, selections, results_by_fixture, results_by_match_number)
    except (OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print_table(rows)
    print(f"\nScored matches: {scored_matches}")

    if args.output:
        write_csv(args.output, rows)
        print(f"Wrote {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
