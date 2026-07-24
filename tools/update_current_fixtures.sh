#!/usr/bin/env bash
#
# Download the Premier League 2026/27 fixtures and write ../fixtures_2026_27.json
# containing only fixtures from the CURRENT football week onward.
#
# A football week is treated as starting on Saturday, so anything before the
# most recent Saturday (on or before today) is dropped. e.g. run on a
# Wednesday and you keep last Saturday's games onward, but nothing earlier.
#
# The free api-football plan can't access season 2026, so we use the no-key
# feed from fixturedownload.com (epl-2026 == the 2026/27 season). It sends no
# CORS headers, which is why we snapshot it into a same-origin JSON file the
# select_games.html page can read.

set -euo pipefail

SRC="https://fixturedownload.com/feed/json/epl-2026"
OUT="$(cd "$(dirname "$0")/.." && pwd)/fixtures_2026_27.json"

# ── Cutoff = most recent Saturday on or before today (YYYY-MM-DD) ──────────
# date +%u : 1=Mon .. 6=Sat .. 7=Sun. Days back to Saturday = (u - 6 + 7) % 7.
dow=$(date +%u)
offset=$(( (dow - 6 + 7) % 7 ))
if date -v-1d +%Y-%m-%d >/dev/null 2>&1; then
  CUTOFF=$(date -v-"${offset}"d +%Y-%m-%d)      # BSD/macOS date
else
  CUTOFF=$(date -d "-${offset} days" +%Y-%m-%d)  # GNU/Linux date
fi

echo "Today: $(date +%Y-%m-%d) — keeping fixtures on/after Saturday $CUTOFF"
echo "Fetching $SRC ..."

curl -fsS --max-time 30 "$SRC" | CUTOFF="$CUTOFF" python3 -c "
import sys, os, json
cutoff = os.environ['CUTOFF']
data = json.load(sys.stdin)
games = []
for m in data:
    d = (m.get('DateUtc') or '')[:10]     # 'YYYY-MM-DD' (ISO sorts lexically)
    if d and d < cutoff:
        continue                          # drop anything before this week
    games.append({
        'round': m.get('RoundNumber'),
        'date':  m.get('DateUtc'),
        'home':  m.get('HomeTeam'),
        'away':  m.get('AwayTeam'),
    })
games.sort(key=lambda g: (g['round'] or 0, g['date'] or ''))
out = {
    'season': '2026/27',
    'source': 'fixturedownload.com/epl-2026',
    'from':   cutoff,
    'games':  games,
}
json.dump(out, open('$OUT', 'w'), indent=2, ensure_ascii=False)
print(f'Wrote {len(games)} fixtures (from {cutoff}) to $OUT')
"
