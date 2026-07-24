#!/usr/bin/env bash
#
# Daily refresh for the Premier League prediction game (run from cron at 06:00).
#
#   1. Pull the latest actual results  -> results_2026_27.csv   (no API key)
#   2. Rebuild the scores table        -> league_table.csv      (if selections.csv exists)
#   3. Optionally refresh H2H + form    -> *_summary.csv         (only if SPORTSDB is set)
#   4. Commit + push any changed data so AWS Amplify redeploys
#
# Results and the scores table need NO API key. Head-to-head / form need the
# TheSportsDB premium key; set SPORTSDB in the crontab line to include them
# (build_predictions_data.py validates the key and refuses to write empty CSVs).
#
# Logs go to tools/daily_update.log (gitignored).

set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"

# ── Single-instance lock (mkdir is atomic; macOS has no flock) ──────────────
LOCKDIR="/tmp/pl-daily-update.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "[i] $(date '+%Y-%m-%d %H:%M:%S') another run is in progress ($LOCKDIR exists) — exiting"
  exit 0
fi
trap 'rmdir "$LOCKDIR"' EXIT

echo "===== $(date '+%Y-%m-%d %H:%M:%S') daily_update starting ====="

# 1. Actual results (fixturedownload feed, no key needed)
bash tools/fetch_pl_results.sh || echo "[!] results fetch failed"

# 2. Scores table (only if we have predictions to score)
if [ -f selections.csv ]; then
  python3 tools/calculate_scores_table.py || echo "[!] scores table failed"
else
  echo "[i] selections.csv not found — skipping scores table"
fi

# 3. Optional: refresh head-to-head + form (needs premium key; the python
#    script fails fast on an invalid/free key and never writes empty CSVs)
if [ -n "${SPORTSDB:-}" ]; then
  ./tools/update_predictions_data.sh || echo "[!] H2H/form refresh failed"
else
  echo "[i] SPORTSDB not set — skipping H2H/form refresh"
fi

# 4. Commit + push only the game data files, only if something changed.
#    games.txt is included so the deployed fixtures always match the CSVs
#    that were generated from them.
DATA_FILES=(games.txt results_2026_27.csv league_table.csv matchup_summary.csv team_form_summary.csv)
EXISTING=()
for f in "${DATA_FILES[@]}"; do [ -f "$f" ] && EXISTING+=("$f"); done

if [ ${#EXISTING[@]} -gt 0 ] && [ -n "$(git status --porcelain -- "${EXISTING[@]}")" ]; then
  git add "${EXISTING[@]}"
  if git commit -q -m "Daily update: $(date '+%Y-%m-%d %H:%M')"; then
    # Integrate any remote-side commits first so the push can't be rejected
    git pull --rebase origin main || echo "[!] pull --rebase failed"
    if git push origin main; then
      echo "[i] pushed — Amplify will redeploy"
    else
      echo "[!] git push failed — local main has unpushed commits, fix manually"
      exit 1
    fi
  else
    echo "[!] git commit failed — nothing pushed"
    exit 1
  fi
else
  echo "[i] no data changes to commit"
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S') daily_update finished ====="
