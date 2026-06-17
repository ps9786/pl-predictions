cd ~/vscode/world-cup-2026-selections-explorer
git pull
cd ~/vscode/pl-predictions
git pull
cd ~/Downloads
if [ -f world-cup-2026-selections-explorer.zip ]; then
  cp world-cup-2026-selections-explorer.zip ~/vscode/world-cup-2026-selections-explorer
  rm world-cup-2026-selections-explorer.zip
  cd ~/vscode/world-cup-2026-selections-explorer
  unzip -o world-cup-2026-selections-explorer.zip
fi
cd ~/vscode/world-cup-2026-selections-explorer
curl https://fixturedownload.com/download/fifa-world-cup-2026-UTC.csv -o ./public/wc2026.csv
curl https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json -o ./public/worldcup.json
python3 calculate_league_table.py --output public/league_table.csv
rm -fr dist/
npm run build
cp -a dist/wc/* ~/vscode/pl-predictions/wc
cd ~/vscode/pl-predictions
git add .
git commit -m "New day"
git push
