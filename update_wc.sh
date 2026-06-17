cd ~/vscode/pl-predictions
git pull
cd ~/Downloads
if [ ! -f world-cup-2026-selections-explorer.zip ]; then
  cp world-cup-2026-selections-explorer.zip ~/vscode/wc
  rm world-cup-2026-selections-explorer.zip
  cd ~/vscode/wc
  unzip -o world-cup-2026-selections-explorer.zip
fi
curl https://fixturedownload.com/download/fifa-world-cup-2026-UTC.csv -o ./public/wc2026.csv
curl https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json -o ./public/worldcup.json
npm run build
cp -a dist/wc/* ~/vscode/pl-predictions/wc
cd ~/vscode/pl-predictions
git add .
git commit -m "New day"
git push
