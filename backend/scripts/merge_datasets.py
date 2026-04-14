from __future__ import annotations

from pathlib import Path
import pandas as pd
import ast

HISTORICAL_PATH = Path("data/processed/historical_player_game_logs.csv")
RECENT_PATH = Path("data/processed/recent_player_game_logs.csv")

PLAYER_SEASON_AVG_PATH = Path("data/processed/live_context/player_season_averages.csv")
TEAM_SEASON_AVG_PATH = Path("data/processed/live_context/team_season_averages.csv")
STANDINGS_PATH = Path("data/processed/live_context/team_standings.csv")
INJURIES_PATH = Path("data/processed/live_context/player_injuries.csv")

COMBINED_OUTPUT_PATH = Path("data/processed/combined_player_game_logs.csv")
TRAINING_OUTPUT_PATH = Path("data/processed/training_features.csv")


def load_csv(path: Path, label: str, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"{label} file not found: {path}")
        print(f"Warning: optional file not found: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        print(f"Warning: {label} dataset is empty: {path}")
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "pts": "points",
        "reb": "rebounds",
        "ast": "assists",
        "min": "minutes",
        "player": "player_name",
        "date": "game_date",
    }

    cols_to_rename = {col: rename_map[col] for col in df.columns if col in rename_map}
    df = df.rename(columns=cols_to_rename)

    expected_columns = [
        "player_id",
        "player_name",
        "game_id",
        "game_date",
        "season",
        "postseason",
        "team_id",
        "team_name",
        "opponent_id",
        "opponent_name",
        "home",
        "minutes",
        "points",
        "rebounds",
        "assists",
        "stl",
        "blk",
        "turnover",
        "pf",
        "fgm",
        "fga",
        "fg_pct",
        "fg3m",
        "fg3a",
        "fg3_pct",
        "ftm",
        "fta",
        "ft_pct",
        "oreb",
        "dreb",
        "plus_minus",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = pd.NA

    return df[expected_columns].copy()


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "player_id",
        "game_id",
        "season",
        "postseason",
        "team_id",
        "opponent_id",
        "home",
        "minutes",
        "points",
        "rebounds",
        "assists",
        "stl",
        "blk",
        "turnover",
        "pf",
        "fgm",
        "fga",
        "fg_pct",
        "fg3m",
        "fg3a",
        "fg3_pct",
        "ftm",
        "fta",
        "ft_pct",
        "oreb",
        "dreb",
        "plus_minus",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df["player_name"] = df["player_name"].astype("string").str.strip()
    df["team_name"] = df["team_name"].astype("string").str.strip()
    df["opponent_name"] = df["opponent_name"].astype("string").str.strip()

    return df


def deduplicate_game_logs(df: pd.DataFrame) -> pd.DataFrame:
    if {"player_id", "game_id"}.issubset(df.columns):
        strong = df.dropna(subset=["player_id", "game_id"]).copy()
        weak = df[df["player_id"].isna() | df["game_id"].isna()].copy()

        strong = strong.drop_duplicates(subset=["player_id", "game_id"], keep="last")
        weak = weak.drop_duplicates(subset=["player_name", "game_date"], keep="last")

        df = pd.concat([strong, weak], ignore_index=True)
    else:
        df = df.drop_duplicates(subset=["player_name", "game_date"], keep="last")

    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["player_name", "game_date"]).copy()

    group = df.groupby("player_name", group_keys=False)

    for stat in ["points", "rebounds", "assists", "minutes"]:
        df[f"{stat}_last_3"] = group[stat].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        df[f"{stat}_last_5"] = group[stat].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
        df[f"{stat}_last_10"] = group[stat].transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())

    df["days_rest"] = group["game_date"].transform(lambda s: s.diff().dt.days)
    df["days_rest"] = df["days_rest"].fillna(3)

    return df


def prepare_player_season_averages(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    # If there is a nested player object column serialized strangely, try to flatten it
    if "player" in work.columns:
        try:
            player_norm = pd.json_normalize(work["player"])
            player_norm.columns = [f"player_{c}" for c in player_norm.columns]
            work = pd.concat([work.drop(columns=["player"]), player_norm], axis=1)
        except Exception:
            pass

    # Recover player_id if it came through nested/renamed
    candidate_player_id_cols = [
        "player_id",
        "player.id",
        "player_id_x",
        "player_player_id",
        "player_id_y",
        "player_id.1",
        "player_id_",
        "player_id__",
        "player_id___",
        "player_id____",
        "player_id_____",
        "player_id______",
        "player_id_______",
        "player_id________",
        "player_id_________",
        "player_id__________",
        "player_id___________",
        "player_id____________",
        "player_id_____________",
        "player_id______________",
        "player_id_______________",
        "player_id________________",
        "player_id_________________",
        "player_id__________________",
        "player_id___________________",
        "player_id____________________",
        "player_id_____________________",
        "player_id______________________",
        "player_id_______________________",
        "player_id________________________",
        "player_id_________________________",
        "player_id__________________________",
        "player_id___________________________",
        "player_id____________________________",
        "player_id_____________________________",
        "player_id______________________________",
        "player_id_______________________________",
        "player_id________________________________",
        "player_id_________________________________",
        "player_id__________________________________",
        "player_id___________________________________",
        "player_id____________________________________",
        "player_id_____________________________________",
        "player_id______________________________________",
        "player_id_______________________________________",
        "player_id________________________________________",
        "player_id_________________________________________",
        "player_id__________________________________________",
        "player_id___________________________________________",
        "player_id____________________________________________",
        "player_id_____________________________________________",
        "player_id______________________________________________",
        "player_id_______________________________________________",
        "player_id________________________________________________",
        "player_id_________________________________________________",
        "player_id__________________________________________________",
        "player_id___________________________________________________",
        "player_id____________________________________________________",
        "player_id_____________________________________________________",
        "player_id______________________________________________________",
        "player_id_______________________________________________________",
        "player_id________________________________________________________",
        "player_id_________________________________________________________",
        "player_id__________________________________________________________",
        "player_id___________________________________________________________",
        "player_id____________________________________________________________",
        "player_id_____________________________________________________________",
        "player_id______________________________________________________________",
        "player_id_______________________________________________________________",
        "player_id________________________________________________________________",
        "player_id_________________________________________________________________",
        "player_id__________________________________________________________________",
        "player_id___________________________________________________________________",
        "player_id____________________________________________________________________",
        "player_id_____________________________________________________________________",
        "player_id______________________________________________________________________",
        "player_id_______________________________________________________________________",
        "player_id________________________________________________________________________",
        "player_id_________________________________________________________________________",
        "player_id__________________________________________________________________________",
        "player_id___________________________________________________________________________",
        "player_id____________________________________________________________________________",
        "player_id_____________________________________________________________________________",
        "player_id______________________________________________________________________________",
        "player_id_______________________________________________________________________________",
        "player_id________________________________________________________________________________",
        "player_id_________________________________________________________________________________",
        "player_id__________________________________________________________________________________",
        "player_id___________________________________________________________________________________",
        "player_id____________________________________________________________________________________",
        "player_id_____________________________________________________________________________________",
        "player_id______________________________________________________________________________________",
        "player_id_______________________________________________________________________________________",
        "player_id________________________________________________________________________________________",
        "player_id_________________________________________________________________________________________",
        "player_id__________________________________________________________________________________________",
        "player_id___________________________________________________________________________________________",
        "player_id____________________________________________________________________________________________",
        "player_id_____________________________________________________________________________________________",
        "player_id______________________________________________________________________________________________",
        "player_id_______________________________________________________________________________________________",
        "player_id________________________________________________________________________________________________",
        "player_id_________________________________________________________________________________________________",
        "player_id__________________________________________________________________________________________________",
        "player_id___________________________________________________________________________________________________",
        "player_id____________________________________________________________________________________________________",
        "player_id_____________________________________________________________________________________________________",
        "player_id______________________________________________________________________________________________________",
        "player_id_______________________________________________________________________________________________________",
        "player_id________________________________________________________________________________________________________",
        "player_id_________________________________________________________________________________________________________",
        "player_id__________________________________________________________________________________________________________",
        "player_id___________________________________________________________________________________________________________",
        "player_id____________________________________________________________________________________________________________",
        "player_id_____________________________________________________________________________________________________________",
        "player_id______________________________________________________________________________________________________________",
        "player_id_______________________________________________________________________________________________________________",
        "player_id________________________________________________________________________________________________________________",
        "player_id_________________________________________________________________________________________________________________",
        "player_id__________________________________________________________________________________________________________________",
        "player_id___________________________________________________________________________________________________________________",
        "player_id____________________________________________________________________________________________________________________",
        "player_id_____________________________________________________________________________________________________________________",
        "player_id______________________________________________________________________________________________________________________",
        "player_id_______________________________________________________________________________________________________________________",
        "player_id________________________________________________________________________________________________________________________",
        "player_id_________________________________________________________________________________________________________________________",
        "player_id__________________________________________________________________________________________________________________________",
        "player_id___________________________________________________________________________________________________________________________",
        "player_player_id",
        "player_id",
    ]

    if "player_id" not in work.columns:
        for col in candidate_player_id_cols:
            if col in work.columns:
                work["player_id"] = work[col]
                break

    # Sometimes json_normalize of nested player creates player_id via player_id or player_id-like cols
    if "player_id" not in work.columns:
        for col in work.columns:
            if col.lower().endswith("player_id") or col.lower() == "playerid":
                work["player_id"] = work[col]
                break

    # Ensure season exists
    if "season" not in work.columns:
        season_like = [c for c in work.columns if c.lower() == "season"]
        if season_like:
            work["season"] = work[season_like[0]]

    keep_cols = [c for c in work.columns if c != "team"]
    work = work[keep_cols].copy()

    if "player_id" not in work.columns:
        raise KeyError(
            f"player_id not found in player season averages. Available columns: {list(work.columns)}"
        )

    if "season" not in work.columns:
        raise KeyError(
            f"season not found in player season averages. Available columns: {list(work.columns)}"
        )

    work["player_id"] = pd.to_numeric(work["player_id"], errors="coerce")
    work["season"] = pd.to_numeric(work["season"], errors="coerce")

    work = work.drop_duplicates(subset=["player_id", "season"], keep="last")

    return work

def prepare_team_season_averages(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    # Recover team_id from serialized "team" column
    if "team" in work.columns and "team_id" not in work.columns:
        parsed_team_ids = []

        for value in work["team"]:
            team_id = None

            if isinstance(value, dict):
                team_id = value.get("id")

            elif isinstance(value, str):
                try:
                    parsed = ast.literal_eval(value)
                    if isinstance(parsed, dict):
                        team_id = parsed.get("id")
                except Exception:
                    team_id = None

            parsed_team_ids.append(team_id)

        work["team_id"] = parsed_team_ids

    # Backup recovery: any column ending in team_id
    if "team_id" not in work.columns:
        for col in work.columns:
            if col.lower().endswith("team_id") or col.lower() == "teamid":
                work["team_id"] = work[col]
                break

    if "season" not in work.columns:
        raise KeyError(f"season missing in team season averages")

    if "team_id" not in work.columns:
        raise KeyError(
            f"team_id not found. Available columns: {list(work.columns)}"
        )

    work["team_id"] = pd.to_numeric(work["team_id"], errors="coerce")
    work["season"] = pd.to_numeric(work["season"], errors="coerce")

    work = work.dropna(subset=["team_id", "season"])
    work = work.drop_duplicates(subset=["team_id", "season"], keep="last")

    return work


def prepare_standings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "team" in df.columns:
        team_norm = pd.json_normalize(df["team"])
        team_norm.columns = [f"standings_team_{c}" for c in team_norm.columns]
        df = pd.concat([df.drop(columns=["team"]), team_norm], axis=1)

    if {"team_id", "season"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["team_id", "season"], keep="last")

    return df


def prepare_injuries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    if "player" in work.columns:
        player_norm = pd.json_normalize(work["player"])
        player_norm.columns = [f"injury_player_{c}" for c in player_norm.columns]
        work = pd.concat([work.drop(columns=["player"]), player_norm], axis=1)

    if "team" in work.columns:
        team_norm = pd.json_normalize(work["team"])
        team_norm.columns = [f"injury_team_{c}" for c in team_norm.columns]
        work = pd.concat([work.drop(columns=["team"]), team_norm], axis=1)

    team_col = None
    for candidate in ["team_id", "injury_team_id"]:
        if candidate in work.columns:
            team_col = candidate
            break

    if team_col is None:
        return pd.DataFrame()

    work["injury_count"] = 1
    injury_counts = (
        work.groupby(team_col, dropna=False)["injury_count"]
        .sum()
        .reset_index()
        .rename(columns={team_col: "team_id"})
    )

    return injury_counts


def merge_context(game_logs: pd.DataFrame) -> pd.DataFrame:
    player_avg = prepare_player_season_averages(load_csv(PLAYER_SEASON_AVG_PATH, "player season averages", required=False))
    team_avg = prepare_team_season_averages(load_csv(TEAM_SEASON_AVG_PATH, "team season averages", required=False))
    standings = prepare_standings(load_csv(STANDINGS_PATH, "standings", required=False))
    injuries = prepare_injuries(load_csv(INJURIES_PATH, "injuries", required=False))

    df = game_logs.copy()

    if not player_avg.empty:
        df = df.merge(player_avg, on=["player_id", "season"], how="left")

    if not team_avg.empty:
        team_features = team_avg.add_prefix("team_ctx_")
        team_features = team_features.rename(
            columns={
                "team_ctx_team_id": "team_id",
                "team_ctx_season": "season",
            }
        )
        df = df.merge(team_features, on=["team_id", "season"], how="left")

        opp_features = team_avg.add_prefix("opp_ctx_")
        opp_features = opp_features.rename(
            columns={
                "opp_ctx_team_id": "opponent_id",
                "opp_ctx_season": "season",
            }
        )
        df = df.merge(opp_features, on=["opponent_id", "season"], how="left")

    if not standings.empty and "team_id" in standings.columns and "season" in standings.columns:
        team_standings = standings.add_prefix("team_standings_").rename(
            columns={
                "team_standings_team_id": "team_id",
                "team_standings_season": "season",
            }
        )
        df = df.merge(team_standings, on=["team_id", "season"], how="left")

        opp_standings = standings.add_prefix("opp_standings_").rename(
            columns={
                "opp_standings_team_id": "opponent_id",
                "opp_standings_season": "season",
            }
        )
        df = df.merge(opp_standings, on=["opponent_id", "season"], how="left")

    if not injuries.empty:
        team_inj = injuries.rename(columns={"injury_count": "team_injury_count"})
        df = df.merge(team_inj, on="team_id", how="left")

        opp_inj = injuries.rename(
            columns={
                "team_id": "opponent_id",
                "injury_count": "opponent_injury_count",
            }
        )
        df = df.merge(opp_inj, on="opponent_id", how="left")

    if "team_injury_count" in df.columns:
        df["team_injury_count"] = df["team_injury_count"].fillna(0)
    else:
        df["team_injury_count"] = 0

    if "opponent_injury_count" in df.columns:
        df["opponent_injury_count"] = df["opponent_injury_count"].fillna(0)
    else:
        df["opponent_injury_count"] = 0

    return df


def main():
    print("Loading historical game logs...")
    historical_df = load_csv(HISTORICAL_PATH, "historical")

    print("Loading recent game logs...")
    recent_df = load_csv(RECENT_PATH, "recent")

    historical_df = coerce_types(normalize_columns(historical_df))
    recent_df = coerce_types(normalize_columns(recent_df))

    print(f"Historical rows before merge: {len(historical_df)}")
    print(f"Recent rows before merge: {len(recent_df)}")

    combined_df = pd.concat([historical_df, recent_df], ignore_index=True)
    print(f"Rows after concat: {len(combined_df)}")

    combined_df = deduplicate_game_logs(combined_df)
    combined_df = combined_df.dropna(subset=["player_name", "game_date"])
    combined_df = combined_df.sort_values(["player_name", "game_date", "game_id"]).reset_index(drop=True)

    combined_df = add_rolling_features(combined_df)
    combined_df = merge_context(combined_df)

    COMBINED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_csv(COMBINED_OUTPUT_PATH, index=False)

    training_df = combined_df.copy()

    TRAINING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    training_df.to_csv(TRAINING_OUTPUT_PATH, index=False)

    print(f"Saved combined game logs to: {COMBINED_OUTPUT_PATH}")
    print(f"Saved training features to: {TRAINING_OUTPUT_PATH}")
    print(f"Final row count: {len(training_df)}")
    print(training_df.head())


if __name__ == "__main__":
    main()