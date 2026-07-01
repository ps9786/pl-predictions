from datetime import datetime, timedelta
import json
import os
import sys
import requests


def get_world_cup_fixtures():
    OUTPUT_FILE = '../wc/next_7_days.json'
    # 1. Retrieve the API key from the environment variable
    api_key = os.getenv("API_FOOTBALL_KEY")
    if not api_key:
        print(
            "Error: The 'API_FOOTBALL_KEY' environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Define the date parameters for the next 7 days
    # api-football expects dates in the format YYYY-MM-DD
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # 3. Setup API configuration
    # League ID 1 is the default ID for the FIFA World Cup on api-football
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": "1",
        "season": "2026",
        "from": start_date,
        "to": end_date,
    }
    headers = {"x-apisports-key": api_key}

    # 4. Make the HTTP GET request
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # 5. Output the results in clean JSON format
        print(json.dumps(data, indent=2))
        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
          json.dump(data, fh, indent=2, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    get_world_cup_fixtures()
