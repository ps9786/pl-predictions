import sys
import requests

def get_match_outcome(score_team1, score_team2):
    """Returns '1' for team1 win, '2' for team2 win, or 'X' for a draw."""
    if score_team1 > score_team2:
        return '1'
    elif score_team2 > score_team1:
        return '2'
    else:
        return 'X'

def calculate_points(actual_t1, actual_t2, pred_t1, pred_t2):
    """Calculates points based on actual vs predicted scores."""
    # 1) Exact score match -> 3 points
    if actual_t1 == pred_t1 and actual_t2 == pred_t2:
        return 3
    
    # 2) Correct result match (outcome) -> 1 point
    actual_outcome = get_match_outcome(actual_t1, actual_t2)
    pred_outcome = get_match_outcome(pred_t1, pred_t2)
    
    if actual_outcome == pred_outcome:
        return 1
        
    return 0

def main():
    # Check if a command line argument was passed
    if len(sys.argv) < 2:
        print("Error: Please provide a prediction score.")
        print("Usage: python script.py <score1>,<score2>  (e.g., python script.py 1,1)")
        sys.exit(1)

    # Parse the command line argument
    pred_input = sys.argv[1]
    try:
        pred_t1_str, pred_t2_str = pred_input.split(',')
        pred_t1 = int(pred_t1_str.strip())
        pred_t2 = int(pred_t2_str.strip())
    except ValueError:
        print("Error: Invalid prediction format. Please use 'score1,score2' (e.g., 1,1 or 2,0)")
        sys.exit(1)

    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

    matches = data.get("matches", [])
    played_matches = [m for m in matches if m.get("score") and "ft" in m["score"]]

    if not played_matches:
        print("No completed matches found in the dataset yet.")
        return

    print(f"Evaluating prediction ({pred_t1}-{pred_t2}) across {len(played_matches)} completed matches:\n")
    
    total_points = 0
    
    for match in played_matches:
        team1 = match["team1"]
        team2 = match["team2"]
        actual_t1, actual_t2 = match["score"]["ft"]
        
        points = calculate_points(actual_t1, actual_t2, pred_t1, pred_t2)
        total_points += points
        
        # Only show matches where you actually scored points to keep terminal clean,
        # or list them all depending on preference.
        if points > 0:
            match_status = "EXACT SCORE! (3pts)" if points == 3 else "Correct Outcome (1pt)"
            print(f"✓ {team1} {actual_t1}-{actual_t2} {team2} -> {match_status}")

    print("-" * 50)
    print(f"Total Points Earned: {total_points}")

if __name__ == "__main__":
    main()
