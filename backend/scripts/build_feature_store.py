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

def aggregate_lineups(lineups_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if lineups_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    work = lineups_df.copy()

    for col in ["game_id", "player_id", "team_id", "starter_flag", "bench_flag"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")

    player_game = (
        work.groupby(["game_id", "player_id"], as_index=False)
        .agg(
            starter_flag=("starter_flag", "max"),
            bench_flag=("bench_flag", "max"),
        )
    )

    team_game = (
        work.groupby(["game_id", "team_id"], as_index=False)
        .agg(
            team_lineup_starters_count=("starter_flag", "sum"),
            team_lineup_bench_count=("bench_flag", "sum"),
        )
    )

    return player_game, team_game


def aggregate_injuries(injuries_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
    """
    Approximate injury impact using injured player's recent average minutes and starter likelihood.
    This estimates how much opportunity is missing from a team because injured players are out.
    """
    if injuries_df.empty:
        return pd.DataFrame()

    work = injuries_df.copy()

    if "team_id" not in work.columns or "player_id" not in work.columns:
        return pd.DataFrame()

    work["team_id"] = pd.to_numeric(work["team_id"], errors="coerce")
    work["player_id"] = pd.to_numeric(work["player_id"], errors="coerce")

    stats = stats_df.copy()
    stats["game_date"] = pd.to_datetime(stats["game_date"], errors="coerce")
    stats["minutes"] = pd.to_numeric(stats.get("minutes"), errors="coerce")

    recent_minutes = (
        stats.sort_values("game_date")
        .groupby("player_id", as_index=False)
        .tail(10)
        .groupby("player_id", as_index=False)
        .agg(
            injured_player_recent_minutes=("minutes", "mean"),
            injured_player_recent_points=("points", "mean"),
        )
    )

    injury_context = work.merge(recent_minutes, on="player_id", how="left")

    injury_context["injured_player_recent_minutes"] = (
        pd.to_numeric(injury_context["injured_player_recent_minutes"], errors="coerce")
        .fillna(0)
    )

    injury_context["injured_player_recent_points"] = (
        pd.to_numeric(injury_context["injured_player_recent_points"], errors="coerce")
        .fillna(0)
    )

    # Approximate starter injury: injured player averaged 24+ minutes recently
    injury_context["injured_starter_proxy"] = (
        injury_context["injured_player_recent_minutes"] >= 24
    ).astype(int)

    team_injury_features = (
        injury_context.groupby("team_id", as_index=False)
        .agg(
            team_injured_count=("player_id", "nunique"),
            team_starter_injured_count=("injured_starter_proxy", "sum"),
            team_injured_minutes_lost=("injured_player_recent_minutes", "sum"),
            team_injured_points_lost=("injured_player_recent_points", "sum"),
        )
    )

    return team_injury_features


def main():
    stats_path = RAW_DIR / "game_player_stats.csv"
    player_avg_path = CTX_DIR / "player_season_averages.csv"
    team_avg_path = CTX_DIR / "team_season_averages.csv"
    odds_path = CTX_DIR / "odds.csv"
    lineups_path = CTX_DIR / "lineups.csv"
    injuries_path = CTX_DIR / "player_injuries.csv"

    if not stats_path.exists():
        raise FileNotFoundError(f"Missing {stats_path}. Run fetch_historical_stats.py first.")

    stats_df = pd.read_csv(stats_path, low_memory=False)
    stats_df["game_date"] = pd.to_datetime(stats_df["game_date"], errors="coerce")

    player_avg = (
        pd.read_csv(player_avg_path, low_memory=False)
        if player_avg_path.exists()
        else pd.DataFrame()
    )

    team_avg = (
        pd.read_csv(team_avg_path, low_memory=False)
        if team_avg_path.exists()
        else pd.DataFrame()
    )

    odds_df = (
        pd.read_csv(odds_path, low_memory=False)
        if odds_path.exists()
        else pd.DataFrame()
    )

    lineups_df = (
        pd.read_csv(lineups_path, low_memory=False)
        if lineups_path.exists()
        else pd.DataFrame()
    )

    injuries_df = (
        pd.read_csv(injuries_path, low_memory=False)
        if injuries_path.exists()
        else pd.DataFrame()
    )

    print(f"[INFO] Base stats rows: {len(stats_df)}")
    print(f"[INFO] Player averages rows: {len(player_avg)}")
    print(f"[INFO] Team averages rows: {len(team_avg)}")
    print(f"[INFO] Odds rows: {len(odds_df)}")
    print(f"[INFO] Lineup rows: {len(lineups_df)}")
    print(f"[INFO] Injury rows: {len(injuries_df)}")

    # Normalize common join columns
    for col in ["game_id", "player_id", "team_id", "opponent_id", "season"]:
        if col in stats_df.columns:
            stats_df[col] = pd.to_numeric(stats_df[col], errors="coerce")

    # Rolling player features
    stats_df = add_rolling_features(stats_df)

    # Player season priors
    if not player_avg.empty and {"player_id", "season"}.issubset(player_avg.columns):
        player_avg = player_avg.copy()
        player_avg["player_id"] = pd.to_numeric(player_avg["player_id"], errors="coerce")
        player_avg["season"] = pd.to_numeric(player_avg["season"], errors="coerce")

        stats_df = stats_df.merge(
            player_avg.drop_duplicates(subset=["player_id", "season"]),
            on=["player_id", "season"],
            how="left",
        )

    # Team and opponent season context
    if not team_avg.empty and {"team_id", "season"}.issubset(team_avg.columns):
        team_avg = team_avg.copy()
        team_avg["team_id"] = pd.to_numeric(team_avg["team_id"], errors="coerce")
        team_avg["season"] = pd.to_numeric(team_avg["season"], errors="coerce")

        team_ctx = team_avg.add_prefix("team_ctx_").rename(
            columns={
                "team_ctx_team_id": "team_id",
                "team_ctx_season": "season",
            }
        )

        stats_df = stats_df.merge(
            team_ctx,
            on=["team_id", "season"],
            how="left",
        )

        opp_ctx = team_avg.add_prefix("opp_ctx_").rename(
            columns={
                "opp_ctx_team_id": "opponent_id",
                "opp_ctx_season": "season",
            }
        )

        stats_df = stats_df.merge(
            opp_ctx,
            on=["opponent_id", "season"],
            how="left",
        )

    # Betting odds context
    if not odds_df.empty and "game_id" in odds_df.columns:
        odds_df = odds_df.copy()
        odds_df["game_id"] = pd.to_numeric(odds_df["game_id"], errors="coerce")

        odds_features = aggregate_odds(odds_df)

        if not odds_features.empty:
            odds_features["game_id"] = pd.to_numeric(odds_features["game_id"], errors="coerce")

            stats_df = stats_df.merge(
                odds_features,
                on="game_id",
                how="left",
            )

    # Lineup context
    if not lineups_df.empty and {"game_id", "player_id"}.issubset(lineups_df.columns):
        lineups_df = lineups_df.copy()

        for col in ["game_id", "player_id", "team_id", "starter_flag", "bench_flag"]:
            if col in lineups_df.columns:
                lineups_df[col] = pd.to_numeric(lineups_df[col], errors="coerce")

        player_lineups, team_lineups = aggregate_lineups(lineups_df)

        if not player_lineups.empty:
            stats_df = stats_df.merge(
                player_lineups,
                on=["game_id", "player_id"],
                how="left",
            )

        if not team_lineups.empty:
            team_lineups["game_id"] = pd.to_numeric(team_lineups["game_id"], errors="coerce")
            team_lineups["team_id"] = pd.to_numeric(team_lineups["team_id"], errors="coerce")

            stats_df = stats_df.merge(
                team_lineups,
                on=["game_id", "team_id"],
                how="left",
            )

            opp_lineups = team_lineups.rename(
                columns={
                    "team_id": "opponent_id",
                    "team_lineup_starters_count": "opp_lineup_starters_count",
                    "team_lineup_bench_count": "opp_lineup_bench_count",
                }
            )

            stats_df = stats_df.merge(
                opp_lineups,
                on=["game_id", "opponent_id"],
                how="left",
            )

    # Injury context
    injury_features = aggregate_injuries(injuries_df, stats_df)

    if not injury_features.empty:
        injury_features["team_id"] = pd.to_numeric(injury_features["team_id"], errors="coerce")

        stats_df = stats_df.merge(
            injury_features,
            on="team_id",
            how="left",
        )

        opp_injury_features = injury_features.rename(
            columns={
                "team_id": "opponent_id",
                "team_injured_count": "opponent_injured_count",
                "team_starter_injured_count": "opponent_starter_injured_count",
                "team_injured_minutes_lost": "opponent_injured_minutes_lost",
                "team_injured_points_lost": "opponent_injured_points_lost",
            }
        )

        stats_df = stats_df.merge(
            opp_injury_features,
            on="opponent_id",
            how="left",
        )

    # Fill missing lineup/injury values
    fill_zero_cols = [
        "starter_flag",
        "bench_flag",
        "team_lineup_starters_count",
        "team_lineup_bench_count",
        "opp_lineup_starters_count",
        "opp_lineup_bench_count",
        "team_injured_count",
        "team_starter_injured_count",
        "team_injured_minutes_lost",
        "team_injured_points_lost",
        "opponent_injured_count",
        "opponent_starter_injured_count",
        "opponent_injured_minutes_lost",
        "opponent_injured_points_lost",
    ]

    for col in fill_zero_cols:
        if col in stats_df.columns:
            stats_df[col] = pd.to_numeric(stats_df[col], errors="coerce").fillna(0)

    # Role boost features
    if {"starter_flag", "team_starter_injured_count"}.issubset(stats_df.columns):
        stats_df["role_boost_flag"] = (
            (stats_df["starter_flag"] == 1)
            & (stats_df["team_starter_injured_count"] > 0)
        ).astype(int)

    if {"starter_flag", "team_injured_minutes_lost"}.issubset(stats_df.columns):
        stats_df["role_boost_score"] = (
            pd.to_numeric(stats_df["starter_flag"], errors="coerce").fillna(0)
            * pd.to_numeric(stats_df["team_injured_minutes_lost"], errors="coerce").fillna(0)
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(OUT_PATH, index=False)

    print(f"Saved feature store to {OUT_PATH} with {len(stats_df)} rows")

    debug_cols = [
        "starter_flag",
        "bench_flag",
        "team_starter_injured_count",
        "team_injured_minutes_lost",
        "opponent_starter_injured_count",
        "role_boost_flag",
        "role_boost_score",
    ]

    for col in debug_cols:
        if col in stats_df.columns:
            non_null = stats_df[col].notna().sum()
            total = len(stats_df)
            total_sum = pd.to_numeric(stats_df[col], errors="coerce").fillna(0).sum()
            print(f"[CHECK] {col}: non-null={non_null}/{total}, sum={total_sum}")

if __name__ == "__main__":
    main()