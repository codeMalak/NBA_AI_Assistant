from __future__ import annotations

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "player_game_logs.csv")
SAMPLE_PATH = os.path.join(BASE_DIR, "data", "processed", "nba_player_games_sample.csv")


def load_games() -> pd.DataFrame:
    if os.path.exists(PROCESSED_PATH):
        path = PROCESSED_PATH
    elif os.path.exists(SAMPLE_PATH):
        path = SAMPLE_PATH
    else:
        raise FileNotFoundError(
            f"Neither processed dataset nor sample dataset was found.\n"
            f"Expected one of:\n- {PROCESSED_PATH}\n- {SAMPLE_PATH}"
        )

    df = pd.read_csv(path)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.dropna(subset=["player_name", "game_date"])

    # Optional columns that older code may expect
    if "home_flag" not in df.columns:
        df["home_flag"] = 0

    return df.sort_values(["player_name", "game_date"]).reset_index(drop=True)


def get_all_players() -> list[str]:
    df = load_games()
    return sorted(df["player_name"].dropna().unique().tolist())