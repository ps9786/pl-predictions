# Premier League Predictions

A small web app + set of scripts that friends use to predict scorelines in the
English Premier League. Players open a mobile-friendly page, enter predicted
scores, and submit them; the organiser sets which fixtures are in play and
generates the supporting stats (head-to-head history and recent form).

The 2025/26 **World Cup** edition (the `wc/` folder, `plpb.html`, `*_b`
files and `world_cup_*` / `wc` tools) is **finished and archived** — it is kept
for reference but is no longer updated.

---

## How the game works

For each fixture a player predicts a scoreline. Scoring (see
`tools/check_scores.py`):

- **3 points** — exact score correct
- **1 point** — correct result (home win / draw / away win) but wrong score
- **0 points** — otherwise

---

## Repository layout

| Path | What it is |
|------|------------|
| `plp.html` | **Main predictions page.** Reads `games.txt`, `matchup_summary.csv`, `team_form_summary.csv`; submits predictions via an AWS Lambda → Pushover. |
| `select_games.html` | **Fixture picker.** Shows the whole 2026/27 season by matchweek, lets you tick games and copy them in `games.txt` format (to paste/email). |
| `games.txt` | **Source of truth** for the fixtures currently in play. One `Home - Away` per line (optionally `Home - Away, note`). |
| `fixtures_2026_27.json` | Snapshot of the full 2026/27 fixture list, read by `select_games.html`. |
| `matchup_summary.csv` | Head-to-head results (last 5 meetings) per fixture. Generated. |
| `team_form_summary.csv` | Last-5 form (W/D/L) per team. Generated. |
| `tools/` | Python + bash scripts (see below). |
| `wc/`, `plpb.html`, `*_b.*` | Archived World Cup edition. |

---

## Prerequisites

- **Python 3** (standard library only for the fixture/stats scripts; the World
  Cup scripts use `requests`).
- A static web server to open the HTML pages (browsers block `fetch()` from
  `file://`). In production the site is hosted on **AWS Amplify** (HTTPS); for
  local testing:
  ```bash
  python3 -m http.server 8000     # then browse to http://localhost:8000/plp.html
  ```
  Note: Amplify publishes the whole repo tree publicly (including `tools/`), so
  never commit secrets — keep the `SPORTSDB` key in your environment only.
- **TheSportsDB premium API key** for head-to-head + form data, provided via the
  `SPORTSDB` environment variable (account `ps9786`). The free test key `123`
  works for head-to-head but returns only **1** game for form instead of 5.
- No key is needed for fixtures (they come from `fixturedownload.com`).

---

## Weekly workflow

### 1. Refresh the fixture list (occasionally)
Pulls the full 2026/27 schedule into `fixtures_2026_27.json`:
```bash
bash tools/fetch_pl_fixtures.sh
```
Or, to keep only fixtures from the current football week onward (most recent
Saturday and later):
```bash
bash tools/update_current_fixtures.sh
```

### 2. Choose this round's fixtures
Open `select_games.html` in a browser, tick the games you want (there's a
**Select all** button per matchweek), click **Generate games.txt**, and **Copy**
(or **Email**) the result. Paste it into `games.txt`.

`games.txt` uses **short club names** (e.g. `Man Utd`, `Spurs`, `Palace`,
`Forest`, `Villa`) — the picker maps to these automatically.

### 3. Generate head-to-head + form stats
Reads `games.txt`, looks up each club, and regenerates the two CSVs:
```bash
./tools/update_predictions_data.sh
# SPORTSDB is read from the environment; override per-run with:
# SPORTSDB=<key> ./tools/update_predictions_data.sh
```
This is the step to put behind your **cronjob**.

### 4. Players predict
Serve the folder and share `plp.html`. Players enter scores and tap **Send
Predictions** — this POSTs to the AWS Lambda in `plp.html` (`API_URL`), which
forwards a Pushover notification to the organiser.

### 5. Score & leaderboard
Result checking uses the 3/1/0 rules in `tools/check_scores.py` /
`check_scores_all.py`. The published league table is produced by the sibling
project `~/vscode/calculate_leaderboard` (out of scope for this repo).

---

## Tools reference

Active (Premier League 2026/27):

| Script | Purpose |
|--------|---------|
| `tools/fetch_pl_fixtures.sh` | Download the full 2026/27 fixture list → `fixtures_2026_27.json`. |
| `tools/update_current_fixtures.sh` | Same, but drops fixtures before the most recent Saturday. |
| `tools/build_predictions_data.py` | Build `matchup_summary.csv` + `team_form_summary.csv` from `games.txt`. |
| `tools/update_predictions_data.sh` | Wrapper for the above. |
| `tools/team_lookup.csv` | Short name → TheSportsDB club name + men's-team ID. |
| `tools/check_scores.py` / `check_scores_all.py` | Score a prediction against an actual result. |

Archived (World Cup 2026):
`tools/world_cup_*.py`, `tools/quirky.py`, `tools/calculate_league_table.py`,
`tools/get_ft_scores.sh`, `tools/make_wc_data.sh`, `tools/update_wc.sh`,
`tools/update_leaderboard.sh`, `tools/world_up_next_7_days.py`.

---

## Maintaining the team lookup

`tools/team_lookup.csv` maps each `games.txt` short name to the correct
TheSportsDB **men's** club and ID. This mapping is required because naive name
search returns wrong clubs (women's teams, overseas sides, even a basketball
team). If a new club is promoted in, add a row:
```csv
short,thesportsdb_name,thesportsdb_id
Luton,Luton Town,133888
```
If the builder prints `'<name>' not in team_lookup.csv`, add that club and re-run.

---

## Environment variables

| Variable | Used by | Notes |
|----------|---------|-------|
| `SPORTSDB` | `build_predictions_data.py` | TheSportsDB premium key (V1, key-in-path). Falls back to free `123`. |
| `API_FOOTBALL_KEY` | archived World Cup scripts | api-football key; free plan cannot access season 2026. |
