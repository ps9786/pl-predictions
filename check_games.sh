echo GamesB
cat games_b.txt | awk -F- '{print NF}'  | sort -u
echo Games
cat games.txt | awk -F- '{print NF}'  | sort -u
