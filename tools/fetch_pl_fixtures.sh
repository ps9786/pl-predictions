#!/usr/bin/env bash
#
# Fetch the full Premier League 2026/27 fixture list and write it to
# ../fixtures_2026_27.json for use by select_games.html.
#
# The free api-football plan cannot access season 2026, so we use the
# no-key public feed from fixturedownload.com (epl-2026 == the 2026/27 season).
# fixturedownload does not send CORS headers, so the browser can't fetch it
# directly — that's why we snapshot it into a same-origin JSON file here.
#
# Re-run this whenever the source updates (e.g. once real fixtures replace
# any provisional data).

set -euo pipefail

SRC="https://fixturedownload.com/feed/json/epl-2026"
OUT="$(cd "$(dirname "$0")/.." && pwd)/fixtures_2026_27.json"

echo "Fetching $SRC ..."
curl -fsS --max-time 30 "$SRC" | python3 -c "
import sys, json
data = json.load(sys.stdin)
games = []
for m in data:
    games.append({
        'round': m.get('RoundNumber'),
        'date':  m.get('DateUtc'),
        'home':  m.get('HomeTeam'),
        'away':  m.get('AwayTeam'),
    })
games.sort(key=lambda g: (g['round'] or 0, g['date'] or ''))
out = {'season': '2026/27', 'source': 'fixturedownload.com/epl-2026', 'games': games}
json.dump(out, open('$OUT', 'w'), indent=2, ensure_ascii=False)
print(f'Wrote {len(games)} fixtures to $OUT')
"
