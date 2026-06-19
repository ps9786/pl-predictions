cd ~/vscode/pl-predictions/tools
python ./world_cup_predictions.py 
python ./quirky.py
mv worldcup_quirky.json ../wc/
mv wc2026_predictions.json ../wc/
cd ..
git add .
git commit -m "New Predictions"
git push

