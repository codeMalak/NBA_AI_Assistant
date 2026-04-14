from __future__ import annotations

from pathlib import Path
import pandas as pd
from huggingface_hub import snapshot_download

OUTPUT_PATH = Path("data/processed/historical_player_game_logs.csv")


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


def main():
    print("Downloading dataset snapshot from Hugging Face...")
    repo_path = snapshot_download(
        repo_id="SupremeMonkey/NBA_betting_data",
        repo_type="dataset",
    )

    repo_path = Path(repo_path)
    players_root = repo_path / "data" / "players"

    if not players_root.exists():
        raise FileNotFoundError(f"Players folder not found: {players_root}")

    parquet_files = list(players_root.rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No player parquet files found.")

    print(f"Found {len(parquet_files)} parquet files.")

    player_rows: list[dict] = []
    success_count = 0
    fail_count = 0

    for idx, parquet_file in enumerate(parquet_files, start=1):
        try:
            df = pd.read_parquet(parquet_file)

            player_col = find_first_existing_column(df, ["player_name", "player", "name", "PLAYER_NAME"])
            date_col = find_first_existing_column(df, ["game_date", "date", "GAME_DATE", "gameDate"])
            points_col = find_first_existing_column(df, ["points", "pts", "PTS"])
            rebounds_col = find_first_existing_column(df, ["rebounds", "reb", "REB"])
            assists_col = find_first_existing_column(df, ["assists", "ast", "AST"])
            minutes_col = find_first_existing_column(df, ["minutes", "min", "MIN"])

            fallback_name = parquet_file.stem.rsplit("_", 1)[0].replace("_", " ").title()

            before = len(player_rows)

            for _, row in df.iterrows():
                player_rows.append({
                    "player_name": safe_get(row, player_col, fallback_name),
                    "game_date": safe_get(row, date_col),
                    "points": safe_get(row, points_col),
                    "rebounds": safe_get(row, rebounds_col),
                    "assists": safe_get(row, assists_col),
                    "minutes": safe_get(row, minutes_col),
                })

            added = len(player_rows) - before
            success_count += 1

            if idx <= 5:
                print(f"[DEBUG] {parquet_file.name}")
                print(f"        columns={list(df.columns)}")
                print(f"        rows_in_file={len(df)}, rows_added={added}")

            if idx % 100 == 0:
                print(f"Processed {idx}/{len(parquet_files)} files...")

        except Exception as e:
            fail_count += 1
            if fail_count <= 20:
                print(f"Skipping {parquet_file.name}: {e}")

    df_final = pd.DataFrame(player_rows)

    print(f"Successful parquet reads: {success_count}")
    print(f"Failed parquet reads: {fail_count}")
    print(f"Rows collected before cleaning: {len(df_final)}")

    if df_final.empty:
        raise ValueError("No usable player rows were created.")

    df_final["game_date"] = pd.to_datetime(df_final["game_date"], errors="coerce")
    df_final = df_final.dropna(subset=["player_name", "game_date"])
    df_final = df_final.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved dataset to: {OUTPUT_PATH}")
    print(f"Total rows after cleaning: {len(df_final)}")
    print(df_final.head())


if __name__ == "__main__":
    main()