from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated

GAMES_PATH = Path("data/raw/games.csv")
OUTPUT_PATH = Path("data/raw/context/advanced_stats.csv")


def flatten_advanced_stats(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for row in rows:
        player = row.get("player") or {}
        team = row.get("team") or {}
        game = row.get("game") or {}

        base = {
            "advanced_stat_id": row.get("id"),
            "game_id": row.get("game_id") or game.get("id"),
            "game_date": row.get("game_date") or game.get("date"),
            "season": row.get("season") or game.get("season"),
            "player_id": row.get("player_id") or player.get("id"),
            "player_name": (
                row.get("player_name")
                or f'{player.get("first_name", "")} {player.get("last_name", "")}'.strip()
            ),
            "team_id": row.get("team_id") or team.get("id"),
            "team_abbr": team.get("abbreviation"),
        }

        for key, value in row.items():
            if key in {"id", "player", "team", "game"}:
                continue

            if isinstance(value, (dict, list)):
                continue

            base[f"adv_{key}"] = value

        flattened.append(base)

    df = pd.DataFrame(flattened)

    if not df.empty:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df = df.drop_duplicates(subset=["game_id", "player_id"], keep="last")

    return df


def main():
    if not GAMES_PATH.exists():
        raise FileNotFoundError(f"Missing {GAMES_PATH}. Run fetch_historical_games.py first.")

    games_df = pd.read_csv(GAMES_PATH, low_memory=False)
    games_df["date"] = pd.to_datetime(games_df["date"], errors="coerce")

    # Advanced stats are most useful for completed games.
    games_df = games_df[games_df["date"] < pd.Timestamp.today()].copy()

    game_ids = games_df["game_id"].dropna().astype(int).unique().tolist()
    print(f"Game IDs to fetch advanced stats for: {len(game_ids)}")

    existing_game_ids = set()
    if OUTPUT_PATH.exists():
        existing_df = pd.read_csv(OUTPUT_PATH, low_memory=False)
        if "game_id" in existing_df.columns:
            existing_game_ids = set(existing_df["game_id"].dropna().astype(int).unique().tolist())
        print(f"Existing game_ids with advanced stats: {len(existing_game_ids)}")

    game_ids = [gid for gid in game_ids if gid not in existing_game_ids]
    print(f"Game IDs still needing advanced stats: {len(game_ids)}")

    all_rows = []
    batch_size = 25

    for i in range(0, len(game_ids), batch_size):
        chunk = game_ids[i:i + batch_size]
        print(f"Fetching advanced stats batch {i // batch_size + 1}")

        params = []
        for gid in chunk:
            params.append(("game_ids[]", gid))

        rows = fetch_paginated("/nba/v2/stats/advanced", params=params)
        print(f"Rows returned: {len(rows)}")
        all_rows.extend(rows)

    new_df = flatten_advanced_stats(all_rows)

    if OUTPUT_PATH.exists():
        old_df = pd.read_csv(OUTPUT_PATH, low_memory=False)
        final_df = pd.concat([old_df, new_df], ignore_index=True)

        if {"game_id", "player_id"}.issubset(final_df.columns):
            final_df = final_df.drop_duplicates(subset=["game_id", "player_id"], keep="last")
    else:
        final_df = new_df

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Added {len(new_df)} advanced stat rows")
    print(f"Saved {len(final_df)} total advanced stat rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()