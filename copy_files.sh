#cp ../ClaudeCode/plp.html ./plp.html
#cp ../ClaudeCode/plp.html ./plpb.html
cp ../football-predictions/matchup_summary.csv .
cp ../football-predictions/team_form_summary.csv .
cd ../football-predictions/
bash ./make_games_text.sh
cd ../pl-predictions
cp ../football-predictions/games.txt .
