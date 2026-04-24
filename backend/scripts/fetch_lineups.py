from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated

GAMES_PATH = Path("data/raw/games.csv")
OUTPUT_PATH = Path("data/raw/context/lineups.csv")


def flatten_lineups(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for row in rows:
        player = row.get("player") or {}

        flattened.append({
            "lineup_id": row.get("id"),
            "game_id": row.get("game_id"),
            "starter_flag": 1 if row.get("starter") is True else 0,
            "bench_flag": 0 if row.get("starter") is True else 1,
            "lineup_position": row.get("position"),

            "player_id": player.get("id"),
            "player_name": f'{player.get("first_name", "")} {player.get("last_name", "")}'.strip(),
            "player_position": player.get("position"),
            "player_height": player.get("height"),
            "player_weight": player.get("weight"),
            "team_id": player.get("team_id"),
        })

    df = pd.DataFrame(flattened)

    if not df.empty:
        df = df.drop_duplicates(subset=["game_id", "player_id"], keep="last")

    return df


def main():
    if not GAMES_PATH.exists():
        raise FileNotFoundError(f"Missing {GAMES_PATH}. Run fetch_historical_games.py first.")

    games_df = pd.read_csv(GAMES_PATH, low_memory=False)
    games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")

    print(f"Total games loaded: {len(games_df)}")

    games_df = games_df[games_df["season"].astype("Int64") >= 2025].copy()
    games_df = games_df[games_df["date"] < pd.Timestamp.today()].copy()

    print(f"Games after 2025/completed filter: {len(games_df)}")

    game_ids = games_df["game_id"].dropna().astype(int).unique().tolist()
    print(f"Game IDs to fetch lineups for: {len(game_ids)}")

    all_rows = []
    batch_size = 100

    for i in range(0, len(game_ids), batch_size):
        chunk = game_ids[i:i + batch_size]
        print(f"Fetching lineups batch {i // batch_size + 1}")

        params = []
        for gid in chunk:
            params.append(("game_ids[]", gid))

        rows = fetch_paginated("/nba/v1/lineups", params=params)
        print(f"Rows returned: {len(rows)}")
        all_rows.extend(rows)

    df = flatten_lineups(all_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} lineup rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()