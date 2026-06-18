#cd ~/vscode/world-cup-2026-selections-explorer
#git pull
#cd ~/vscode/pl-predictions
#git pull
#if [ -f ~/Downloads/world-cup-2026-selections-explorer.zip ]; then
#  cd ~/Downloads
#  cp world-cup-2026-selections-explorer.zip ~/vscode/world-cup-2026-selections-explorer
#  rm world-cup-2026-selections-explorer.zip
#  cd ~/vscode/world-cup-2026-selections-explorer
#  unzip -o world-cup-2026-selections-explorer.zip
#  git add .
#  NOW=$(date)
#  git commit -m "New update of world-cup-2026-selections-explorer: ${NOW}"
#  git push
#fi
#cd ~/vscode/world-cup-2026-selections-explorer
#curl https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json -o ./public/worldcup.json
#python3 calculate_league_table.py --output public/league_table.csv
#rm -fr ~/vscode/pl-predictions/wc/*
#rm -fr dist/
#npm run build
#cp -a dist/wc/* ~/vscode/pl-predictions/wc
cd ~/vscode/knipey
curl https://fixturedownload.com/download/fifa-world-cup-2026-UTC.csv -o ./public/wc2026.csv
python3 ./calculate_league_table.py --output ~/vscode/pl-predictions/wc/league_table.csv
cd ~/vscode/pl-predictions
date +%d > ./wc/current_date.txt
cp ~/vscode/pl-predictions/wc/public/wc2026.csv ./wc/wc2026.csv
git add .
NOW=$(date)
git commit -m "New Leaderboard: ${NOW}"
git push

