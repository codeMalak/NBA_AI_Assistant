from __future__ import annotations

from pathlib import Path
import pandas as pd

from api_client import fetch_paginated, request_json

OUT_DIR = Path("data/raw/context")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def test_endpoint(path: str):
    try:
        rows = fetch_paginated(path)
        print(f"[OK] {path}: {len(rows)} rows")
        return rows
    except Exception as exc:
        print(f"[FAIL] {path}: {exc}")
        return []

def fetch_player_season_averages(season: int, player_ids: list[int]) -> pd.DataFrame:
    category_type_pairs = [
        ("general", "base"),
        ("general", "advanced"),
        ("general", "scoring"),
        ("general", "defense"),
        ("shooting", "by_zone"),
        ("defense", "overall"),
    ]

    frames = []

    for category, subtype in category_type_pairs:
        for i in range(0, len(player_ids), 100):
            chunk = player_ids[i:i + 100]
            params = [("season", season), ("season_type", "regular"), ("type", subtype)]
            for pid in chunk:
                params.append(("player_ids[]", pid))

            rows = fetch_paginated(f"/nba/v1/season_averages/{category}", params=params)
            if not rows:
                continue

            df = pd.DataFrame(rows)
            if df.empty:
                continue

            if "player" in df.columns:
                pnorm = pd.json_normalize(df["player"])
                if "id" in pnorm.columns:
                    df["player_id"] = pnorm["id"]

            if "team" in df.columns:
                tnorm = pd.json_normalize(df["team"])
                if "id" in tnorm.columns:
                    df["team_id"] = tnorm["id"]

            if "stats" in df.columns:
                stats_df = pd.json_normalize(df["stats"]).add_prefix(f"{category}_{subtype}_")
                df = pd.concat([df.drop(columns=["stats"]), stats_df], axis=1)

            keep = [c for c in ["player_id", "team_id", "season", "season_type"] if c in df.columns]
            stat_cols = [c for c in df.columns if c.startswith(f"{category}_{subtype}_")]
            df = df[keep + stat_cols]
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    result = frames[0]
    for df in frames[1:]:
        join_cols = [c for c in ["player_id", "team_id", "season", "season_type"] if
                     c in result.columns and c in df.columns]
        overlap = [c for c in df.columns if c in result.columns and c not in join_cols]
        if overlap:
            df = df.drop(columns=overlap)
        result = result.merge(df, on=join_cols, how="outer")

    return result


def fetch_team_season_averages(season: int) -> pd.DataFrame:
    category_type_pairs = [
        ("general", "base"),
        ("general", "advanced"),
        ("general", "scoring"),
        ("general", "defense"),
        ("general", "opponent"),
        ("shooting", "by_zone_base"),
        ("shooting", "5ft_range_base"),
    ]

    frames = []

    for category, subtype in category_type_pairs:
        rows = fetch_paginated(
            f"/nba/v1/team_season_averages/{category}",
            params={"season": season, "season_type": "regular", "type": subtype},
        )
        if not rows:
            continue

        df = pd.DataFrame(rows)
        if df.empty:
            continue

        if "team" in df.columns:
            tnorm = pd.json_normalize(df["team"])
            if "id" in tnorm.columns:
                df["team_id"] = tnorm["id"]

        if "stats" in df.columns:
            stats_df = pd.json_normalize(df["stats"]).add_prefix(f"team_{category}_{subtype}_")
            df = pd.concat([df.drop(columns=["stats"]), stats_df], axis=1)

        keep = [c for c in ["team_id", "season", "season_type"] if c in df.columns]
        stat_cols = [c for c in df.columns if c.startswith(f"team_{category}_{subtype}_")]
        df = df[keep + stat_cols]
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    result = frames[0]
    for df in frames[1:]:
        join_cols = [c for c in ["team_id", "season", "season_type"] if c in result.columns and c in df.columns]
        overlap = [c for c in df.columns if c in result.columns and c not in join_cols]
        if overlap:
            df = df.drop(columns=overlap)
        result = result.merge(df, on=join_cols, how="outer")

    return result


def fetch_standings(season: int) -> pd.DataFrame:
    rows = fetch_paginated("/nba/v1/standings", params={"season": season})
    return pd.DataFrame(rows)


def fetch_injuries() -> pd.DataFrame:
    rows = fetch_paginated("/nba/v1/player_injuries")
    return flatten_injuries(rows)


def flatten_injuries(rows: list[dict]) -> pd.DataFrame:
    flattened = []

    for row in rows:
        player = row.get("player") or {}
        team = player.get("team") or {}

        flattened.append({
            "player_id": player.get("id"),
            "player_name": f'{player.get("first_name", "")} {player.get("last_name", "")}'.strip(),
            "team_id": player.get("team_id") or team.get("id"),
            "team_abbr": team.get("abbreviation"),
            "player_position": player.get("position"),
            "return_date": row.get("return_date"),
            "injury_description": row.get("description"),
            "injury_status": row.get("status"),
        })

    return pd.DataFrame(flattened)


def fetch_active_players() -> pd.DataFrame:
    rows = fetch_paginated("/v1/active_players")
    return pd.DataFrame(rows)


def main():
    stats_path = Path("data/raw/game_player_stats.csv")
    test_endpoint("/v1/active_players")
    if not stats_path.exists():
        raise FileNotFoundError(f"Missing {stats_path}. Run fetch_historical_stats.py first.")

    stats_df = pd.read_csv(stats_path, low_memory=False)

    seasons = sorted(stats_df["season"].dropna().astype(int).unique().tolist())
    player_ids = sorted(stats_df["player_id"].dropna().astype(int).unique().tolist())

    all_player_avg = []
    all_team_avg = []
    all_standings = []

    for season in seasons:
        print(f"Fetching context for season={season}")

        pavg = fetch_player_season_averages(season, player_ids)
        if not pavg.empty:
            all_player_avg.append(pavg)

        tavg = fetch_team_season_averages(season)
        if not tavg.empty:
            all_team_avg.append(tavg)

        s = fetch_standings(season)
        if not s.empty:
            all_standings.append(s)

    if all_player_avg:
        pd.concat(all_player_avg, ignore_index=True).to_csv(OUT_DIR / "player_season_averages.csv", index=False)

    if all_team_avg:
        pd.concat(all_team_avg, ignore_index=True).to_csv(OUT_DIR / "team_season_averages.csv", index=False)

    if all_standings:
        pd.concat(all_standings, ignore_index=True).to_csv(OUT_DIR / "team_standings.csv", index=False)

    fetch_injuries().to_csv(OUT_DIR / "player_injuries.csv", index=False)

    try:
        active_df = fetch_active_players()
        active_df.to_csv(OUT_DIR / "active_players.csv", index=False)
        print(f"Saved active players: {len(active_df)} rows")
    except Exception as exc:
        print(f"[WARN] Skipping active players fetch: {exc}")

    print("Saved context snapshots.")


if __name__ == "__main__":
    main()