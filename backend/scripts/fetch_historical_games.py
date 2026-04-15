from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated

OUTPUT_PATH = Path("data/raw/games.csv")


def flatten_games(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for g in rows:
        home_team = g.get("home_team") or {}
        visitor_team = g.get("visitor_team") or {}

        flattened.append(
            {
                "game_id": g.get("id"),
                "date": g.get("date"),
                "season": g.get("season"),
                "status": g.get("status"),
                "postseason": g.get("postseason"),
                "home_team_id": home_team.get("id") or g.get("home_team_id"),
                "home_team_abbr": home_team.get("abbreviation"),
                "home_team_name": home_team.get("full_name") or home_team.get("name"),
                "visitor_team_id": visitor_team.get("id") or g.get("visitor_team_id"),
                "visitor_team_abbr": visitor_team.get("abbreviation"),
                "visitor_team_name": visitor_team.get("full_name") or visitor_team.get("name"),
                "home_team_score": g.get("home_team_score"),
                "visitor_team_score": g.get("visitor_team_score"),
            }
        )

    df = pd.DataFrame(flattened)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(["season", "date", "game_id"]).reset_index(drop=True)
    return df


def main():
    # Example: pull 3 most recent season-ids
    seasons = [2023, 2024, 2025]

    all_rows = []
    for season in seasons:
        print(f"Fetching games for season={season}")
        rows = fetch_paginated("/nba/v1/games", params=[("seasons[]", season)])
        all_rows.extend(rows)

    df = flatten_games(all_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} games to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()