import os
import pandas as pd
from pathlib import Path

from fetch_recent_games import DATA_DIR, fetch_paginated


# Your API key
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/v1/players"

PLAYER_ROSTER_PATH = DATA_DIR / "player_roster.csv"


# Grab current roster information
def fetch_players():
    return fetch_paginated("players")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    players = fetch_players()
    print(f"[DEBUG] raw games returned: {len(players)}")

    # Flatten players
    df = pd.json_normalize(players)

    if not df.empty:
        df.to_csv(PLAYER_ROSTER_PATH, index=False)
        print(f"Saved players: {PLAYER_ROSTER_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    main()
