from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated

GAMES_PATH = Path("data/raw/games.csv")
OUTPUT_PATH = Path("data/raw/game_player_stats.csv")


def normalize_minutes(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if ":" in value:
        try:
            mins, secs = value.split(":", 1)
            return round(int(mins) + int(secs) / 60.0, 2)
        except Exception:
            return None
    try:
        return float(value)
    except Exception:
        return None


def flatten_stats(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for row in rows:
        player = row.get("player") or {}
        team = row.get("team") or {}
        game = row.get("game") or {}

        team_id = team.get("id")
        home_team_id = game.get("home_team_id")
        visitor_team_id = game.get("visitor_team_id")

        home = None
        opponent_id = None
        if team_id == home_team_id:
            home = 1
            opponent_id = visitor_team_id
        elif team_id == visitor_team_id:
            home = 0
            opponent_id = home_team_id

        flattened.append(
            {
                "stat_id": row.get("id"),
                "game_id": game.get("id"),
                "game_date": game.get("date"),
                "season": game.get("season"),
                "postseason": game.get("postseason"),
                "player_id": player.get("id"),
                "player_name": f'{player.get("first_name", "")} {player.get("last_name", "")}'.strip(),
                "team_id": team_id,
                "team_name": team.get("full_name") or team.get("name"),
                "team_abbr": team.get("abbreviation"),
                "opponent_id": opponent_id,
                "home": home,
                "minutes": normalize_minutes(row.get("min")),
                "points": row.get("pts"),
                "rebounds": row.get("reb"),
                "assists": row.get("ast"),
                "stl": row.get("stl"),
                "blk": row.get("blk"),
                "turnover": row.get("turnover"),
                "pf": row.get("pf"),
                "fgm": row.get("fgm"),
                "fga": row.get("fga"),
                "fg_pct": row.get("fg_pct"),
                "fg3m": row.get("fg3m"),
                "fg3a": row.get("fg3a"),
                "fg3_pct": row.get("fg3_pct"),
                "ftm": row.get("ftm"),
                "fta": row.get("fta"),
                "ft_pct": row.get("ft_pct"),
                "oreb": row.get("oreb"),
                "dreb": row.get("dreb"),
                "plus_minus": row.get("plus_minus"),
            }
        )

    df = pd.DataFrame(flattened)
    if not df.empty:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df = df.sort_values(["game_date", "game_id", "player_id"]).reset_index(drop=True)
    return df


def main():
    if not GAMES_PATH.exists():
        raise FileNotFoundError(f"Missing {GAMES_PATH}. Run fetch_historical_games.py first.")

    games_df = pd.read_csv(GAMES_PATH, low_memory=False)
    game_ids = games_df["game_id"].dropna().astype(int).unique().tolist()

    all_rows = []

    batch_size = 25
    for i in range(0, len(game_ids), batch_size):
        chunk = game_ids[i:i + batch_size]
        print(f"Fetching stats batch {i // batch_size + 1}")

        params = []
        for gid in chunk:
            params.append(("game_ids[]", gid))

        rows = fetch_paginated("/nba/v1/stats", params=params)
        all_rows.extend(rows)

    df = flatten_stats(all_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} stats rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()