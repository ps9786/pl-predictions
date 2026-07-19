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
    if actual_t1 == pred_t1 and actual_t2 == pred_t2:
        return 3
    
    actual_outcome = get_match_outcome(actual_t1, actual_t2)
    pred_outcome = get_match_outcome(pred_t1, pred_t2)
    
    if actual_outcome == pred_outcome:
        return 1
        
    return 0

def main():
    url = "https://raw.githubusercontent.com/openfootball/worldcup.json/refs/heads/master/2026/worldcup.json"
    
    print("Fetching World Cup 2026 data...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    matches = data.get("matches", [])
    played_matches = [m for m in matches if m.get("score") and "ft" in m["score"]]

    if not played_matches:
        print("No completed matches found in the dataset yet.")
        return

    # Extract actual scores
    actual_scores = [tuple(m["score"]["ft"]) for m in played_matches]
    unique_scores = sorted(list(set(actual_scores)))
    
    print(f"Analyzed {len(played_matches)} completed matches.")
    print(f"Found {len(unique_scores)} unique score lines recorded in the data.\n")
    
    results = []
    
    for pred_t1, pred_t2 in unique_scores:
        total_points = 0
        exact_matches = 0
        correct_outcomes = 0
        
        for actual_t1, actual_t2 in actual_scores:
            pts = calculate_points(actual_t1, actual_t2, pred_t1, pred_t2)
            total_points += pts
            if pts == 3:
                exact_matches += 1
            elif pts == 1:
                correct_outcomes += 1
        
        # Total correct is any prediction that successfully earned points (Exact + Outcome)
        total_correct = exact_matches + correct_outcomes
                
        results.append({
            "prediction": f"{pred_t1},{pred_t2}",
            "points": total_points,
            "exact": exact_matches,
            "outcome": correct_outcomes,
            "total_correct": total_correct
        })
        
    # Sort results by points descending, then by exact matches descending
    results.sort(key=lambda x: (x["points"], x["exact"]), reverse=True)
    
    # Print the leaderboard with the new column
    header = f"{'Rank':<5} | {'Prediction':<10} | {'Total Points':<12} | {'Correct Preds':<14} | {'Exact (3pts)':<14} | {'Outcome (1pt)':<14}"
    print(header)
    print("-" * len(header))
    
    for rank, res in enumerate(results, 1):
        print(f"{rank:<5} | {res['prediction']:<10} | {res['points']:<12} | {res['total_correct']:<14} | {res['exact']:<14} | {res['outcome']:<14}")

if __name__ == "__main__":
    main()
