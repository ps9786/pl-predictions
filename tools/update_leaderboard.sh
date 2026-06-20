cd ~/vscode/knipey
curl https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json -o ./wc/worldcup.json
curl https://fixturedownload.com/download/fifa-world-cup-2026-UTC.csv -o ./public/wc2026.csv
python3 ./calculate_league_table.py --output ~/vscode/pl-predictions/wc/league_table.csv
cd ~/vscode/pl-predictions
date +%d > ./wc/current_date.txt
cp ~/vscode/pl-predictions/wc/public/wc2026.csv ./wc/wc2026.csv
git add .
NOW=$(date)
git commit -m "New Leaderboard: ${NOW}"
git push

