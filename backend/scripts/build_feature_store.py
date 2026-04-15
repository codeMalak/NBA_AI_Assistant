from __future__ import annotations

from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
CTX_DIR = RAW_DIR / "context"
OUT_PATH = Path("data/processed/feature_store_points.csv")


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["player_id", "game_date"]).copy()
    group = df.groupby("player_id", group_keys=False)

    for stat in ["points", "rebounds", "assists", "minutes"]:
        df[f"{stat}_last_3"] = group[stat].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        df[f"{stat}_last_5"] = group[stat].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
        df[f"{stat}_last_10"] = group[stat].transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())

    df["days_rest"] = group["game_date"].transform(lambda s: s.diff().dt.days).fillna(3)
    return df


def main():
    stats_df = pd.read_csv(RAW_DIR / "game_player_stats.csv", low_memory=False)
    stats_df["game_date"] = pd.to_datetime(stats_df["game_date"], errors="coerce")

    player_avg = pd.read_csv(CTX_DIR / "player_season_averages.csv", low_memory=False)
    team_avg = pd.read_csv(CTX_DIR / "team_season_averages.csv", low_memory=False)

    stats_df = add_rolling_features(stats_df)

    # player priors
    if {"player_id", "season"}.issubset(player_avg.columns):
        stats_df = stats_df.merge(
            player_avg.drop_duplicates(subset=["player_id", "season"]),
            on=["player_id", "season"],
            how="left",
        )

    # team context
    if {"team_id", "season"}.issubset(team_avg.columns):
        team_ctx = team_avg.add_prefix("team_ctx_").rename(
            columns={"team_ctx_team_id": "team_id", "team_ctx_season": "season"}
        )
        stats_df = stats_df.merge(team_ctx, on=["team_id", "season"], how="left")

        opp_ctx = team_avg.add_prefix("opp_ctx_").rename(
            columns={"opp_ctx_team_id": "opponent_id", "opp_ctx_season": "season"}
        )
        stats_df = stats_df.merge(opp_ctx, on=["opponent_id", "season"], how="left")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(OUT_PATH, index=False)
    print(f"Saved feature store to {OUT_PATH} with {len(stats_df)} rows")


if __name__ == "__main__":
    main()