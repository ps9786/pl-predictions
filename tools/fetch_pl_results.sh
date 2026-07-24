#!/usr/bin/env bash
#
# Download actual Premier League 2026/27 results into ../results_2026_27.csv,
# in the same shape as the old World Cup results file so the scorer can read it:
#
#   Match Number,Round Number,Date,Home Team,Away Team,Result
#
# "Result" is "H - A" only for games that have been played; unplayed games get
# an empty Result and are ignored by the scorer. Source is the fixturedownload
# feed (epl-2026 == the 2026/27 season), which fills in scores as games finish.

set -euo pipefail

SRC="https://fixturedownload.com/feed/json/epl-2026"
OUT="$(cd "$(dirname "$0")/.." && pwd)/results_2026_27.csv"

echo "Fetching results from $SRC ..."
curl -fsS --max-time 30 "$SRC" | python3 -c "
import sys, csv, json
out = sys.argv[1]
data = json.load(sys.stdin)
rows, played = [], 0
for m in data:
    hs, as_ = m.get('HomeTeamScore'), m.get('AwayTeamScore')
    result = f'{hs} - {as_}' if hs is not None and as_ is not None else ''
    if result:
        played += 1
    rows.append([m.get('MatchNumber'), m.get('RoundNumber'),
                 (m.get('DateUtc') or '')[:10], m.get('HomeTeam'),
                 m.get('AwayTeam'), result])
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Match Number', 'Round Number', 'Date', 'Home Team', 'Away Team', 'Result'])
    w.writerows(rows)
print(f'Wrote {len(rows)} fixtures ({played} played) to {out}')
" "$OUT"
