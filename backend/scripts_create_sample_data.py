from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUT_PATH = BASE_DIR / "data" / "processed" / "nba_player_games_sample.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)
players = [
    ("Stephen Curry", 29, 5, 6, 34),
    ("LeBron James", 26, 8, 8, 35),
    ("Jayson Tatum", 28, 8, 4, 36),
    ("Nikola Jokic", 27, 12, 9, 34),
]

start_date = pd.Timestamp("2025-10-01")
rows = []

for player_name, base_points, base_rebounds, base_assists, base_minutes in players:
    for i in range(30):
        game_date = start_date + pd.Timedelta(days=i * 2)
        points = max(5, int(rng.normal(base_points, 6)))
        rebounds = max(1, int(rng.normal(base_rebounds, 3)))
        assists = max(0, int(rng.normal(base_assists, 2)))
        minutes = float(max(20, rng.normal(base_minutes, 3)))
        home_away = "home" if i % 2 == 0 else "away"
        rows.append(
            {
                "player_name": player_name,
                "game_date": game_date,
                "home_away": home_away,
                "points": points,
                "rebounds": rebounds,
                "assists": assists,
                "minutes": round(minutes, 1),
            }
        )

df = pd.DataFrame(rows).sort_values(["player_name", "game_date"])
df.to_csv(OUT_PATH, index=False)
print(f"Wrote sample data to {OUT_PATH}")
