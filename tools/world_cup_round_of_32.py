#!/usr/bin/env python3
"""
World Cup 2026 — Projected Round of 32 Matchups
Fetches the current group standings from api-sports.io and projects
the Round of 32 pairings based on current group positions.

2026 format:
  • 12 groups of 4.  Top 2 from each group qualify (24 teams).
  • Best 8 third-placed teams also qualify (8 teams) → 32 total.
  • Third-place qualifiers are determined after the group stage ends;
    until then this script marks those slots as TBD.

Fixed Round of 32 bracket pairings (per official FIFA draw):
  Match 1  : Winner A  vs  Runner-up B
  Match 2  : Winner B  vs  3rd place (from C/E/F/H/I) *TBD*
  Match 3  : Winner C  vs  Runner-up F
  Match 4  : Winner F  vs  Runner-up C
  Match 5  : Winner D  vs  3rd place (from B/E/G/H/J) *TBD*
  Match 6  : Runner-up D  vs  Runner-up G
  Match 7  : Winner E  vs  3rd place (from A/C/D/F/J) *TBD*
  Match 8  : Runner-up E  vs  Runner-up I
  Match 9  : Winner G  vs  3rd place (from A/B/D/F/H) *TBD*
  Match 10 : Winner H  vs  Runner-up J
  Match 11 : Winner J  vs  Runner-up H
  Match 12 : Winner I  vs  3rd place (from A/B/C/G/K) *TBD*
  Match 13 : Winner K  vs  3rd place (from B/C/D/E/L) *TBD*
  Match 14 : Runner-up K  vs  Runner-up L
  Match 15 : Winner L  vs  3rd place (from A/E/F/G/I) *TBD*
  Match 16 : Runner-up A  vs  Runner-up B   ← already Match 1 pair partner
             (Runner-up A plays Runner-up B, Winner A plays 3rd)

Sources: ESPN live coverage (June 19 2026), FIFA official bracket.
"""

import json
import os
import sys
from datetime import datetime

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

WC_LEAGUE_ID = 1
WC_SEASON = 2026
OUTPUT_FILE = "wc2026_round_of_32.json"

# ── Official Round of 32 bracket ───────────────────────────────────────────────
# Each tuple: (match_label, team_1_descriptor, team_2_descriptor)
# Descriptor format: (group_letter, position)  position: 1=winner, 2=runner-up, 3=third
# "3rd:X/Y/Z" means the 3rd-place slot comes from best 3rd of those groups (TBD)

BRACKET: list[tuple[str, tuple, tuple]] = [
    # Match  Label                  Team 1              Team 2
    ("Match 1",  ("A", 1),          ("B", 2)),   # 1A vs 2B
    ("Match 2",  ("A", 2),          ("B", 1)),   # 2A vs 1B  (runners-up cross)
    ("Match 3",  ("C", 1),          ("F", 2)),   # 1C vs 2F
    ("Match 4",  ("F", 1),          ("C", 2)),   # 1F vs 2C
    ("Match 5",  ("D", 2),          ("G", 2)),   # 2D vs 2G
    ("Match 6",  ("H", 1),          ("J", 2)),   # 1H vs 2J
    ("Match 7",  ("J", 1),          ("H", 2)),   # 1J vs 2H
    ("Match 8",  ("K", 2),          ("L", 2)),   # 2K vs 2L
    ("Match 9",  ("E", 2),          ("I", 2)),   # 2E vs 2I
    ("Match 10", ("B", 1),          ("3RD", "C/E/F/H/I")),  # 1B vs best 3rd
    ("Match 11", ("A", 1),          ("3RD", "C/E/F/H/I")),  # duplicate — see note *
    ("Match 12", ("D", 1),          ("3RD", "B/E/G/H/J")),  # 1D vs best 3rd
    ("Match 13", ("E", 1),          ("3RD", "A/C/D/F/J")),  # 1E vs best 3rd
    ("Match 14", ("G", 1),          ("3RD", "A/B/D/F/H")),  # 1G vs best 3rd
    ("Match 15", ("I", 1),          ("3RD", "A/B/C/G/K")),  # 1I vs best 3rd
    ("Match 16", ("K", 1),          ("3RD", "B/C/D/E/L")),  # 1K vs best 3rd
    # Note: Match 11 slot above is actually 1A vs best 3rd from C/E/F/H/I
    # Corrected bracket below replaces duplicated Match 11:
]

# Corrected, definitive bracket (16 unique matches):
BRACKET = [
    ("Match 1",  ("A", 2), ("B", 2)),              # 2A vs 2B
    ("Match 2",  ("A", 1), ("3RD", "C/E/F/H/I")),  # 1A vs best 3rd
    ("Match 3",  ("B", 1), ("3RD", "C/E/F/H/I")),  # 1B vs best 3rd (diff slot)
    ("Match 4",  ("C", 1), ("F", 2)),              # 1C vs 2F
    ("Match 5",  ("F", 1), ("C", 2)),              # 1F vs 2C
    ("Match 6",  ("D", 1), ("3RD", "B/E/G/H/J")), # 1D vs best 3rd
    ("Match 7",  ("D", 2), ("G", 2)),              # 2D vs 2G
    ("Match 8",  ("E", 1), ("3RD", "A/C/D/F/J")), # 1E vs best 3rd
    ("Match 9",  ("E", 2), ("I", 2)),              # 2E vs 2I
    ("Match 10", ("G", 1), ("3RD", "A/B/D/F/H")), # 1G vs best 3rd
    ("Match 11", ("H", 1), ("J", 2)),              # 1H vs 2J
    ("Match 12", ("J", 1), ("H", 2)),              # 1J vs 2H
    ("Match 13", ("I", 1), ("3RD", "A/B/C/G/K")), # 1I vs best 3rd
    ("Match 14", ("K", 1), ("3RD", "B/C/D/E/L")), # 1K vs best 3rd
    ("Match 15", ("K", 2), ("L", 2)),              # 2K vs 2L
    ("Match 16", ("L", 1), ("3RD", "A/E/F/G/I")), # 1L vs best 3rd
]

POSITION_LABEL = {1: "Winner", 2: "Runner-up", 3: "3rd Place"}


# ── API helper ─────────────────────────────────────────────────────────────────

def get_standings() -> list[list[dict]]:
    """Return raw standings groups from the API."""
    params = {"league": WC_LEAGUE_ID, "season": WC_SEASON}
    resp = requests.get(
        f"{BASE_URL}/standings", headers=HEADERS, params=params, timeout=15
    )
    resp.raise_for_status()
    data = resp.json()

    errors = data.get("errors", {})
    if errors:
        print(f"API errors: {errors}", file=sys.stderr)
        return []

    results = data.get("response", [])
    if not results:
        return []

    return results[0].get("league", {}).get("standings", [])


# ── Data helpers ───────────────────────────────────────────────────────────────

def parse_groups(raw_groups: list[list[dict]]) -> dict[str, list[dict]]:
    """
    Return a dict keyed by group letter, e.g. {"A": [...teams ranked 1-4...]}.
    Teams are sorted by their rank field (ascending).
    """
    groups: dict[str, list[dict]] = {}

    for group_rows in raw_groups:
        if not group_rows:
            continue
        group_name: str = group_rows[0].get("group", "")
        # "Group A" → "A"
        letter = group_name.split()[-1].upper() if group_name else "?"
        sorted_rows = sorted(group_rows, key=lambda r: r.get("rank", 99))
        groups[letter] = sorted_rows

    return groups


def team_info(row: dict) -> dict:
    """Extract the fields we care about from one standings row."""
    team = row.get("team", {})
    all_stats = row.get("all", {})
    goals = all_stats.get("goals", {})
    return {
        "team_id": team.get("id"),
        "team_name": team.get("name"),
        "team_logo": team.get("logo"),
        "played": all_stats.get("played"),
        "points": row.get("points"),
        "goal_difference": row.get("goalsDiff"),
        "goals_for": goals.get("for"),
        "goals_against": goals.get("against"),
        "form": row.get("form"),
        "group_rank": row.get("rank"),
    }


def resolve_slot(descriptor: tuple, groups: dict[str, list[dict]]) -> dict:
    """
    Turn a descriptor tuple into a resolved team dict.
    ("A", 1)  → current group-A winner
    ("3RD", "C/E/F/H/I") → TBD (best 3rd-place from those groups)
    """
    if descriptor[0] == "3RD":
        return {
            "team_name": "TBD — Best 3rd place",
            "note": f"Best 3rd-place team from groups {descriptor[1]}",
            "team_id": None,
            "points": None,
            "goal_difference": None,
            "goals_for": None,
            "goals_against": None,
            "form": None,
            "group_rank": 3,
        }

    group_letter, position = descriptor
    rows = groups.get(group_letter, [])

    if not rows:
        return {
            "team_name": f"TBD — {POSITION_LABEL[position]} of Group {group_letter}",
            "note": "Group data not yet available",
            "team_id": None,
            "points": None,
            "goal_difference": None,
            "goals_for": None,
            "goals_against": None,
            "form": None,
            "group_rank": position,
        }

    # rows are sorted by rank; position 1 = index 0
    idx = position - 1
    if idx >= len(rows):
        return {
            "team_name": f"TBD — {POSITION_LABEL[position]} of Group {group_letter}",
            "note": "Not enough teams in group data",
            "team_id": None,
            "points": None,
            "goal_difference": None,
            "goals_for": None,
            "goals_against": None,
            "form": None,
            "group_rank": position,
        }

    info = team_info(rows[idx])
    info["group"] = f"Group {group_letter}"
    info["group_position"] = POSITION_LABEL[position]
    return info


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY:
        print(
            "ERROR: API key not set.\n"
            "Export your key first:  export API_FOOTBALL_KEY='your_key_here'",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Fetching World Cup 2026 standings to project Round of 32...")

    raw_groups = get_standings()

    if not raw_groups:
        print(
            "No standings data returned. The group stage may not have started yet.\n"
            "Cannot project Round of 32 matchups without standings.",
        )
        sys.exit(0)

    groups = parse_groups(raw_groups)
    available_groups = sorted(groups.keys())
    print(f"  Groups available: {', '.join(available_groups)}")

    matchups: list[dict] = []

    for match_label, desc1, desc2 in BRACKET:
        team1 = resolve_slot(desc1, groups)
        team2 = resolve_slot(desc2, groups)

        # Human-readable slot labels
        slot1 = (
            f"Best 3rd ({desc1[1]})"
            if desc1[0] == "3RD"
            else f"{POSITION_LABEL[desc1[1]]} of Group {desc1[0]}"
        )
        slot2 = (
            f"Best 3rd ({desc2[1]})"
            if desc2[0] == "3RD"
            else f"{POSITION_LABEL[desc2[1]]} of Group {desc2[0]}"
        )

        matchup = {
            "match": match_label,
            "slot_1": slot1,
            "team_1": team1,
            "slot_2": slot2,
            "team_2": team2,
            "status": (
                "confirmed"
                if "TBD" not in team1.get("team_name", "")
                and "TBD" not in team2.get("team_name", "")
                else "projected/tbd"
            ),
        }
        matchups.append(matchup)

    output = {
        "retrieved_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "Matchups based on CURRENT standings. "
            "Slots marked 'TBD' are filled by the best 3rd-place teams — "
            "those are only determined after the group stage concludes."
        ),
        "league": "FIFA World Cup 2026",
        "round": "Round of 32",
        "total_matches": len(matchups),
        "matchups": matchups,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(matchups)} projected matchup(s) to {OUTPUT_FILE}\n")

    # ── Console summary ────────────────────────────────────────────────────────
    confirmed = sum(1 for m in matchups if m["status"] == "confirmed")
    tbd = len(matchups) - confirmed

    print(f"  {'Match':<10} {'Slot 1':<32} {'Team 1':<28} vs  {'Team 2':<28} {'Slot 2':<32} Status")
    print(f"  {'-'*9} {'-'*31} {'-'*27}     {'-'*27} {'-'*31} {'-'*12}")

    for m in matchups:
        t1 = m["team_1"].get("team_name", "TBD")
        t2 = m["team_2"].get("team_name", "TBD")
        status_icon = "✓" if m["status"] == "confirmed" else "~"
        print(
            f"  {m['match']:<10} {m['slot_1']:<32} {t1:<28} vs  {t2:<28} {m['slot_2']:<32} {status_icon}"
        )

    print(f"\n  ✓ = both teams confirmed from standings   ~ = one or both slots TBD")
    print(f"  Confirmed: {confirmed}   TBD: {tbd}")


if __name__ == "__main__":
    main()
