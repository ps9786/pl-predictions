cd ~/vscode/pl-predictions/tools
python ./world_cup_predictions.py 
mv wc2026_predictions.json ../wc/
cd ..
git add .
git commit -m "New Predictions"
git push

