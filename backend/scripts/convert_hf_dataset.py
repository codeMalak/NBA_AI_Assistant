from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
from huggingface_hub import snapshot_download

OUTPUT_PATH = Path("data/processed/player_game_logs.csv")


def find_first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def safe_get(row: pd.Series, column_name: str | None, default=None):
    if column_name is None:
        return default
    return row.get(column_name, default)


def clean_player_name_from_filename(stem: str) -> str:
    # Example: aaron_gordon_203932 -> Aaron Gordon
    cleaned = re.sub(r'_\d+$', '', stem)
    return cleaned.replace("_", " ").title()


def parse_matchup(matchup: str):
    """
    Example values:
      DEN @ MIL   -> team_abbr=DEN, opponent_abbr=MIL, home_flag=0
      DEN vs. LAL -> team_abbr=DEN, opponent_abbr=LAL, home_flag=1
    """
    if not matchup or pd.isna(matchup):
        return None, None, 0

    matchup = str(matchup).strip().upper()

    if " VS. " in matchup:
        left, right = matchup.split(" VS. ", 1)
        return left.strip(), right.strip(), 1

    if " @ " in matchup:
        left, right = matchup.split(" @ ", 1)
        return left.strip(), right.strip(), 0

    return None, None, 0


def main():
    print("Downloading dataset snapshot from Hugging Face...")
    repo_path = snapshot_download(
        repo_id="SupremeMonkey/NBA_betting_data",
        repo_type="dataset",
    )

    print(f"Snapshot downloaded to: {repo_path}")

    repo_path = Path(repo_path)
    players_root = repo_path / "data" / "players"

    if not players_root.exists():
        raise FileNotFoundError(f"Players folder not found: {players_root}")

    parquet_files = list(players_root.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No player parquet files found.")

    print(f"Found {len(parquet_files)} parquet files.")
    player_rows: list[dict] = []

    for idx, parquet_file in enumerate(parquet_files, start=1):
        try:
            df = pd.read_parquet(parquet_file)

            player_col = find_first_existing_column(df, [
                "player_name", "player", "name", "PLAYER_NAME"
            ])
            date_col = find_first_existing_column(df, [
                "game_date", "date", "GAME_DATE", "gameDate"
            ])
            points_col = find_first_existing_column(df, [
                "points", "pts", "PTS"
            ])
            rebounds_col = find_first_existing_column(df, [
                "rebounds", "reb", "REB", "reboundsTotal"
            ])
            assists_col = find_first_existing_column(df, [
                "assists", "ast", "AST"
            ])
            minutes_col = find_first_existing_column(df, [
                "minutes", "min", "MIN"
            ])
            matchup_col = find_first_existing_column(df, [
                "MATCHUP", "matchup"
            ])
            game_id_col = find_first_existing_column(df, [
                "game_id", "GAME_ID", "Game_ID"
            ])

            fallback_name = clean_player_name_from_filename(parquet_file.stem)

            for _, row in df.iterrows():
                matchup_value = safe_get(row, matchup_col)
                team_abbr, opponent_abbr, home_flag = parse_matchup(matchup_value)

                player_rows.append({
                    "player_name": safe_get(row, player_col, fallback_name),
                    "game_date": safe_get(row, date_col),
                    "game_id": safe_get(row, game_id_col),
                    "points": safe_get(row, points_col),
                    "rebounds": safe_get(row, rebounds_col),
                    "assists": safe_get(row, assists_col),
                    "minutes": safe_get(row, minutes_col),
                    "team_abbr": team_abbr,
                    "opponent_abbr": opponent_abbr,
                    "home_flag": home_flag,
                })

            if idx % 100 == 0:
                print(f"Processed {idx}/{len(parquet_files)} files...")

        except Exception as e:
            print(f"Skipping {parquet_file.name}: {e}")

    df_final = pd.DataFrame(player_rows)

    if df_final.empty:
        raise ValueError("No usable player rows were created.")

    df_final["game_date"] = pd.to_datetime(df_final["game_date"], errors="coerce")
    df_final = df_final.dropna(subset=["player_name", "game_date"])

    numeric_cols = ["points", "rebounds", "assists", "minutes", "home_flag"]
    for col in numeric_cols:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

    df_final["team_abbr"] = df_final["team_abbr"].fillna("").astype(str).str.strip().str.upper()
    df_final["opponent_abbr"] = df_final["opponent_abbr"].fillna("").astype(str).str.strip().str.upper()
    df_final["player_name"] = df_final["player_name"].fillna("").astype(str).str.strip()
    df_final["home_flag"] = df_final["home_flag"].fillna(0).astype(int)

    df_final = df_final.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved dataset to: {OUTPUT_PATH.resolve()}")
    print(f"Total rows: {len(df_final)}")
    print("Columns:")
    print(df_final.columns.tolist())
    print(df_final[["player_name", "team_abbr", "opponent_abbr", "home_flag"]].head(10).to_string())


if __name__ == "__main__":
    main()