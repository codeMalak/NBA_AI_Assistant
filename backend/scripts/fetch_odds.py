from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated

GAMES_PATH = Path("data/raw/games.csv")
OUTPUT_PATH = Path("data/raw/context/odds.csv")


def flatten_odds(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for row in rows:
        market = row.get("market") or {}

        flattened.append(
            {
                "odds_id": row.get("id"),
                "game_id": row.get("game_id"),
                "vendor": row.get("vendor"),
                "home_team_id": row.get("home_team_id"),
                "visitor_team_id": row.get("visitor_team_id"),
                "market_type": market.get("type"),
                "home_odds": market.get("home_odds"),
                "visitor_odds": market.get("visitor_odds"),
                "spread": market.get("spread"),
                "total": market.get("total"),
                "updated_at": row.get("updated_at"),
            }
        )

    df = pd.DataFrame(flattened)
    if not df.empty:
        df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    return df


def main():
    if not GAMES_PATH.exists():
        raise FileNotFoundError(f"Missing {GAMES_PATH}. Run fetch_historical_games.py first.")

    games_df = pd.read_csv(GAMES_PATH, low_memory=False)

    # Odds are current/live only, so fetch for the most recent season's games.
    # You can later narrow this to upcoming games only if preferred.
    recent_games = games_df.copy()
    recent_games["date"] = pd.to_datetime(recent_games["date"], errors="coerce")
    recent_games = recent_games.dropna(subset=["date"])

    # Keep only games from the latest season present in your games table
    latest_season = int(recent_games["season"].dropna().astype(int).max())
    recent_games = recent_games[recent_games["season"] == latest_season]

    game_ids = recent_games["game_id"].dropna().astype(int).unique().tolist()
    if not game_ids:
        raise ValueError("No game_ids found for odds fetch.")

    all_rows = []

    # /v2/odds requires at least dates[] or game_ids[]
    batch_size = 100
    for i in range(0, len(game_ids), batch_size):
        chunk = game_ids[i:i + batch_size]
        print(f"Fetching odds batch {i // batch_size + 1}")

        params = []
        for gid in chunk:
            params.append(("game_ids[]", gid))

        rows = fetch_paginated("/v2/odds", params=params)
        all_rows.extend(rows)

    df = flatten_odds(all_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} odds rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()