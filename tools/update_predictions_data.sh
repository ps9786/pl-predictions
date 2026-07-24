#!/usr/bin/env bash
#
# Regenerate matchup_summary.csv (head-to-head) and team_form_summary.csv
# (last-5 form) for the fixtures currently in games.txt, from TheSportsDB.
#
# games.txt is the source of truth; team_lookup.csv maps its short names to
# TheSportsDB clubs. Set a premium key for full last-5 form:
#
#   SPORTSDB=<your_premium_key> ./tools/update_predictions_data.sh

set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build_predictions_data.py
