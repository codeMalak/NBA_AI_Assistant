from __future__ import annotations

import os
import pandas as pd
import json

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "player_game_logs.csv")
# SAMPLE_PATH = os.path.join(BASE_DIR, "data", "processed", "nba_player_games_sample.csv")
#
#
# def load_games() -> pd.DataFrame:
#     if os.path.exists(PROCESSED_PATH):
#         path = PROCESSED_PATH
#     elif os.path.exists(SAMPLE_PATH):
#         path = SAMPLE_PATH
#     else:
#         raise FileNotFoundError(
#             f"Neither processed dataset nor sample dataset was found.\n"
#             f"Expected one of:\n- {PROCESSED_PATH}\n- {SAMPLE_PATH}"
#         )
#
#     df = pd.read_csv(path)
#     df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
#     df = df.dropna(subset=["player_name", "game_date"])
#
#     # Optional columns that older code may expect
#     if "home_flag" not in df.columns:
#         df["home_flag"] = 0
#
#     return df.sort_values(["player_name", "game_date"]).reset_index(drop=True)
#
#
# def get_all_players() -> list[str]:
#     df = load_games()
#     return sorted(df["player_name"].dropna().unique().tolist())





BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TRAINING_PATH = os.path.join(BASE_DIR, "data", "processed", "training_features.csv")
COMBINED_PATH = os.path.join(BASE_DIR, "data", "processed", "combined_player_game_logs.csv")
PROCESSED_PATH = os.path.join(BASE_DIR, "data", "processed", "player_game_logs.csv")
SAMPLE_PATH = os.path.join(BASE_DIR, "data", "processed", "nba_player_games_sample.csv")
PLAYER_ROSTER_PATH = os.path.join(BASE_DIR, "data", "processed", "player_roster.csv")

def load_players():
    df = pd.read_csv(PLAYER_ROSTER_PATH)
    data = df.to_dict(orient="records")

    print(json.dumps(data, indent=2))
    return data

def load_games() -> pd.DataFrame:
    # ONLY for UI usage
    if os.path.exists(PROCESSED_PATH):
        path = PROCESSED_PATH
    elif os.path.exists(SAMPLE_PATH):
        path = SAMPLE_PATH
    else:
        raise FileNotFoundError("No base dataset found")

    df = pd.read_csv(path)
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
    df = df.dropna(subset=["player_name", "game_date"])

    if "home_flag" not in df.columns:
        df["home_flag"] = 0

    return df.sort_values(["player_name", "game_date"]).reset_index(drop=True)

def load_training_data() -> pd.DataFrame:
    TRAINING_PATH = os.path.join(BASE_DIR, "data", "processed", "training_features.csv")

    if not os.path.exists(TRAINING_PATH):
        raise FileNotFoundError(f"{TRAINING_PATH} not found")

    df = pd.read_csv(TRAINING_PATH, low_memory=False)

    if "game_date" in df.columns:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")

    return df


def get_all_players() -> list[str]:
    df = load_games()
    return sorted(df["player_name"].dropna().unique().tolist())

if __name__ == "__main__":
    load_players()
