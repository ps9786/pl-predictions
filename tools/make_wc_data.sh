cd ~/vscode/pl-predictions/tools
python ./world_cup_predictions.py 
python ./quirky.py
python ./world_cup_standings.py
python ./world_up_next_7_days.py > ../wc/next_7_days.json
mv worldcup_quirky.json ../wc/
mv wc2026_predictions.json ../wc/
mv wc2026_standings.json ../wc/
cd ..
git add .
git commit -m "New Predictions"
git push

