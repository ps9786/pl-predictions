# CLAUDE.md

Guidance for AI assistants working in this repo. See `README.md` for the
human-facing run instructions; this file captures architecture, conventions,
and the non-obvious gotchas.

## What this is

A friends' **Premier League scoreline-prediction game**. It is a **static site**
(plain HTML/CSS/JS, no build step, no framework) plus **Python/bash tools** run
manually or by cron. There is **no backend in this repo** — dynamic bits are
external services (an AWS Lambda for submissions, TheSportsDB + fixturedownload
for data). The 2025/26 **World Cup edition is finished/archived** (`wc/`,
`plpb.html`, `*_b.*`, `world_cup_*`, `calculate_league_table.py`, etc.). Prefer
not to touch archived files unless asked.

## Data flow

```
fixturedownload.com ──fetch_pl_fixtures.sh──▶ fixtures_2026_27.json ──▶ select_games.html
                                                                             │ (copy/paste)
                                                                             ▼
                                                                          games.txt   ◀── SOURCE OF TRUTH
                                                                             │
                     team_lookup.csv ──▶ build_predictions_data.py ◀────────┘
                                              │  (TheSportsDB, SPORTSDB key)
                                              ▼
                         matchup_summary.csv + team_form_summary.csv ──▶ plp.html ──▶ AWS Lambda ▶ Pushover
```

## Key conventions

- **`games.txt` is the source of truth** for the current round. Format: one
  `Home - Away` per line; an optional per-game note after a comma
  (`Home - Away, note`). Blank lines and `#` comments are ignored.
- **Short club names** everywhere player-facing: `Man Utd`, `Man City`, `Spurs`,
  `Palace`, `Forest`, `Villa`, `West Ham`, `Wolves`, `Brighton`, etc.
- **The generated CSVs must be keyed by those same short names.** `plp.html`
  matches history/form with `home.toLowerCase()|away.toLowerCase()` and
  `formSquares(teamName)` using the names straight from `games.txt`. If the CSVs
  use full names, nothing matches and badges/squares silently disappear.
- `matchup_summary.csv`: `Home Team,Away Team,Score 1..5`, scores from the
  **home team's perspective**, most recent first.
- `team_form_summary.csv`: `Team,Game 5..Game 1` — **oldest on the left, latest
  on the right** (that is how `plp.html` renders the squares).

## Gotchas (learned the hard way)

- **`fetch()` needs a real server.** The pages `fetch()` local files, which
  browsers block over `file://`. Always test via `python3 -m http.server`.
- **fixturedownload.com sends no CORS headers** — the browser can't fetch it
  directly. That's why a script snapshots it to a same-origin JSON file.
- **fixturedownload 2026/27 data is provisional** — it currently lists
  Coventry, Hull and Ipswich as promoted; re-run the fetch script when the real
  fixtures firm up.
- **api-football free plan can't access season 2026** (`API_FOOTBALL_KEY`) — it
  returns an error for 2026, so it is not used for fixtures.
- **TheSportsDB team search is unreliable.** Naive `searchteams` returns wrong
  clubs — Leeds→a basketball team, Newcastle/Ipswich→Australian sides, several
  women's teams, and IDs that don't match names (133623 is Burnley, not
  Ipswich). **Always use `tools/team_lookup.csv`** (hand-verified men's IDs), not
  live search. Verify new IDs with `lookupteam.php?id=` and check
  `strGender=Male`, `strCountry=England`.
- **TheSportsDB free vs premium:**
  - `searchevents.php?e=Home_vs_Away&s=SEASON` (head-to-head) — works on free.
  - `eventslast.php?id=ID` (last-5 form) — **free returns only 1** result;
    **premium returns 5**. Form therefore requires the premium key.
  - `eventsseason.php` is truncated to ~15 on free; `eventsround.php` returns a
    full 10-game round on free (a viable free path to rebuild form if ever
    needed).
  - Multi-word clubs in the H2H slug use underscores for spaces, URL-encoded:
    `Brighton_and_Hove_Albion_vs_Wolverhampton_Wanderers`.
  - Free key is **rate limited** (~HTTP 429 after ~20 rapid calls); the builder
    sleeps 1s between calls and backs off 60s on 429.
- **The premium key.** Account `ps9786`, key stored in the `SPORTSDB` env var,
  used **V1 with key-in-path** (`/api/v1/json/<key>/...`). Do **not** hard-code
  the key value into committed files. A newly-issued key may briefly report
  "Invalid Premium API key" until activation propagates.

## Hosting / deployment

- Served as a static site on **AWS Amplify** over HTTPS. Pages `fetch()` local
  files same-origin, so `games.txt` / the CSVs / `fixtures_2026_27.json` load
  fine in production.
- **The entire committed repo tree is publicly served** (including `tools/`).
  Never hardcode the `SPORTSDB` key (or any secret) into a file — it would be
  publicly downloadable. Keys stay in the local/cron environment only.
- The stats scripts run **locally / via cron**, not on Amplify; they commit the
  refreshed CSVs. Pushing to `main` triggers the Amplify redeploy.

## External services

- **Submissions:** `plp.html` POSTs to an AWS Lambda (`API_URL` in the file) that
  relays a Pushover notification to the organiser. (Button text says "email" but
  transport is Pushover.)
- **Fixtures:** `fixturedownload.com/feed/json/epl-2026` (2026/27 season).
- **Stats:** `thesportsdb.com` V1 API.

## Scoring

3 points exact score, 1 point correct result, 0 otherwise
(`tools/check_scores.py`). The published leaderboard is built in the **sibling**
project `~/vscode/calculate_leaderboard`, not here.

## Working style

- Match the existing vanilla-JS / inline-`<style>` style of `plp.html`; no
  dependencies or build tooling.
- Keep scripts stdlib-only where practical (the new tools use `urllib`, not
  `requests`).
- Don't commit or push unless asked. If asked, branch off `main` first.
