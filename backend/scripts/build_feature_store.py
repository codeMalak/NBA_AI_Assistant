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


def aggregate_odds(odds_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build compact market features per game from multi-book odds.
    """
    if odds_df.empty:
        return pd.DataFrame()

    work = odds_df.copy()

    numeric_cols = ["home_odds", "visitor_odds", "spread", "total"]
    for col in numeric_cols:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")

    agg = (
        work.groupby("game_id", as_index=False)
        .agg(
            odds_vendor_count=("vendor", "nunique"),
            odds_home_odds_avg=("home_odds", "mean"),
            odds_visitor_odds_avg=("visitor_odds", "mean"),
            odds_spread_avg=("spread", "mean"),
            odds_total_avg=("total", "mean"),
            odds_home_odds_best=("home_odds", "max"),
            odds_visitor_odds_best=("visitor_odds", "max"),
            odds_spread_min=("spread", "min"),
            odds_spread_max=("spread", "max"),
            odds_total_min=("total", "min"),
            odds_total_max=("total", "max"),
        )
    )

    # Useful consensus-dispersion features
    agg["odds_spread_range"] = agg["odds_spread_max"] - agg["odds_spread_min"]
    agg["odds_total_range"] = agg["odds_total_max"] - agg["odds_total_min"]

    return agg


def main():
    stats_df = pd.read_csv(RAW_DIR / "game_player_stats.csv", low_memory=False)
    stats_df["game_date"] = pd.to_datetime(stats_df["game_date"], errors="coerce")

    player_avg = pd.read_csv(CTX_DIR / "player_season_averages.csv", low_memory=False)
    team_avg = pd.read_csv(CTX_DIR / "team_season_averages.csv", low_memory=False)

    odds_path = CTX_DIR / "odds.csv"
    odds_df = pd.read_csv(odds_path, low_memory=False) if odds_path.exists() else pd.DataFrame()

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

    # odds context
    if not odds_df.empty and "game_id" in odds_df.columns:
        odds_features = aggregate_odds(odds_df)
        if not odds_features.empty:
            stats_df = stats_df.merge(odds_features, on="game_id", how="left")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(OUT_PATH, index=False)
    print(f"Saved feature store to {OUT_PATH} with {len(stats_df)} rows")


if __name__ == "__main__":
    main()