from __future__ import annotations

import os
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/nba/v1"

DATA_DIR = Path("data/processed")
LIVE_CONTEXT_DIR = DATA_DIR / "live_context"

RECENT_GAMES_PATH = DATA_DIR / "recent_games.csv"
RECENT_PLAYER_LOGS_PATH = DATA_DIR / "recent_player_game_logs.csv"
PLAYER_SEASON_AVG_PATH = LIVE_CONTEXT_DIR / "player_season_averages.csv"
TEAM_SEASON_AVG_PATH = LIVE_CONTEXT_DIR / "team_season_averages.csv"
STANDINGS_PATH = LIVE_CONTEXT_DIR / "team_standings.csv"
INJURIES_PATH = LIVE_CONTEXT_DIR / "player_injuries.csv"

PER_PAGE = 100
MIN_SECONDS_BETWEEN_REQUESTS = 0.15  # GOAT is generous; keep it polite
_last_request_ts = 0.0


def require_api_key() -> str:
    if not API_KEY:
        raise ValueError(
            "Missing BALLDONTLIE_API_KEY in backend/.env. "
            "Add BALLDONTLIE_API_KEY=your_key_here"
        )
    return API_KEY


def get_headers() -> dict[str, str]:
    return {"Authorization": require_api_key()}


def throttle() -> None:
    global _last_request_ts
    now = time.time()
    elapsed = now - _last_request_ts
    if elapsed < MIN_SECONDS_BETWEEN_REQUESTS:
        time.sleep(MIN_SECONDS_BETWEEN_REQUESTS - elapsed)
    _last_request_ts = time.time()


def request_json(endpoint: str, params: dict[str, Any] | list[tuple[str, Any]] | None = None) -> dict[str, Any]:
    throttle()
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_paginated(
    endpoint: str,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    cursor = None

    while True:
        if isinstance(params, list):
            request_params = list(params)
            request_params.append(("per_page", PER_PAGE))
            if cursor is not None:
                request_params.append(("cursor", cursor))
        else:
            request_params = dict(params or {})
            request_params["per_page"] = PER_PAGE
            if cursor is not None:
                request_params["cursor"] = cursor

        payload = request_json(endpoint, request_params)
        rows = payload.get("data", [])
        meta = payload.get("meta", {}) or {}

        all_rows.extend(rows)

        cursor = meta.get("next_cursor")
        if cursor is None:
            break

    return all_rows


def choose_recent_window(days_back: int = 3) -> tuple[str, str]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    start = yesterday - timedelta(days=days_back - 1)
    return start.isoformat(), yesterday.isoformat()


def fetch_games(start_date: str, end_date: str) -> list[dict[str, Any]]:
    return fetch_paginated(
        "games",
        params={
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def fetch_stats(start_date: str, end_date: str) -> list[dict[str, Any]]:
    return fetch_paginated(
        "stats",
        params={
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def normalize_minutes(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    if ":" in value:
        try:
            mins_str, secs_str = value.split(":", 1)
            mins = int(mins_str)
            secs = int(secs_str)
            return round(mins + secs / 60.0, 2)
        except ValueError:
            return None

    try:
        return float(value)
    except ValueError:
        return None


def flatten_games(games: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for g in games:
        home_team = g.get("home_team") or {}
        visitor_team = g.get("visitor_team") or {}

        rows.append(
            {
                "game_id": g.get("id"),
                "game_date": g.get("date"),
                "season": g.get("season"),
                "status": g.get("status"),
                "period": g.get("period"),
                "time": g.get("time"),
                "postseason": g.get("postseason"),
                "home_team_id": home_team.get("id"),
                "home_team_name": home_team.get("full_name") or home_team.get("name"),
                "visitor_team_id": visitor_team.get("id"),
                "visitor_team_name": visitor_team.get("full_name") or visitor_team.get("name"),
                "home_team_score": g.get("home_team_score"),
                "visitor_team_score": g.get("visitor_team_score"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df = df.sort_values(["game_date", "game_id"]).reset_index(drop=True)

    return df


def flatten_stats(stats_rows: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for idx, row in enumerate(stats_rows):
        player = row.get("player") or {}
        team = row.get("team") or {}
        game = row.get("game") or {}
        home_team = game.get("home_team") or {}
        visitor_team = game.get("visitor_team") or {}

        if idx == 0:
            print("[DEBUG] sample player object:", player)
            print("[DEBUG] sample team object:", team)
            print("[DEBUG] sample game object:", game)

        team_id = team.get("id")
        home_team_id = home_team.get("id")
        visitor_team_id = visitor_team.get("id")

        home = None
        opponent_id = None
        opponent_name = None

        if team_id == home_team_id:
            home = 1
            opponent_id = visitor_team_id
            opponent_name = visitor_team.get("full_name") or visitor_team.get("name")
        elif team_id == visitor_team_id:
            home = 0
            opponent_id = home_team_id
            opponent_name = home_team.get("full_name") or home_team.get("name")

        first_name = player.get("first_name", "") or ""
        last_name = player.get("last_name", "") or ""
        player_name = f"{first_name} {last_name}".strip()

        rows.append(
            {
                "player_id": player.get("id"),
                "player_name": player_name,
                "game_id": game.get("id"),
                "game_date": game.get("date"),
                "season": game.get("season"),
                "postseason": game.get("postseason"),
                "team_id": team_id,
                "team_name": team.get("full_name") or team.get("name"),
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "home": home,
                "minutes": normalize_minutes(row.get("min")),
                "points": row.get("pts"),
                "rebounds": row.get("reb"),
                "assists": row.get("ast"),
                "stl": row.get("stl"),
                "blk": row.get("blk"),
                "turnover": row.get("turnover"),
                "pf": row.get("pf"),
                "fgm": row.get("fgm"),
                "fga": row.get("fga"),
                "fg_pct": row.get("fg_pct"),
                "fg3m": row.get("fg3m"),
                "fg3a": row.get("fg3a"),
                "fg3_pct": row.get("fg3_pct"),
                "ftm": row.get("ftm"),
                "fta": row.get("fta"),
                "ft_pct": row.get("ft_pct"),
                "oreb": row.get("oreb"),
                "dreb": row.get("dreb"),
                "plus_minus": row.get("plus_minus"),
            }
        )

    df = pd.DataFrame(rows)

    print(f"[DEBUG] rows before cleaning in flatten_stats: {len(df)}")

    if not df.empty:
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df = df.dropna(subset=["player_name", "game_date", "game_id"])
        print(f"[DEBUG] rows after dropna in flatten_stats: {len(df)}")
        df = df.sort_values(["player_name", "game_date"]).reset_index(drop=True)

    return df


def unique_player_ids(stats_df: pd.DataFrame) -> list[int]:
    if stats_df.empty or "player_id" not in stats_df.columns:
        return []
    ids = stats_df["player_id"].dropna().astype(int).unique().tolist()
    return sorted(ids)


def fetch_player_season_averages(player_ids: list[int], season: int) -> pd.DataFrame:
    """
    Pull a practical subset of player season averages using only valid
    category/type pairings from the BALLDONTLIE NBA docs.
    """
    if not player_ids:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    # Valid pairings per BALLDONTLIE NBA docs
    category_type_pairs = [
        ("general", "base"),
        ("general", "advanced"),
        ("general", "scoring"),
        ("general", "defense"),
        ("shooting", "by_zone"),
        ("defense", "overall"),
    ]

    for category, subtype in category_type_pairs:
        print(f"[DEBUG] fetching player season averages: category={category}, type={subtype}")

        for i in range(0, len(player_ids), 100):
            chunk = player_ids[i : i + 100]

            params: list[tuple[str, Any]] = [
                ("season", season),
                ("season_type", "regular"),
                ("type", subtype),
            ]

            for pid in chunk:
                params.append(("player_ids[]", pid))

            rows = fetch_paginated(f"season_averages/{category}", params=params)

            if rows:
                df = pd.DataFrame(rows)
                if df.empty:
                    continue

                # Extract player_id BEFORE flattening stats
                if "player" in df.columns:
                    player_norm = pd.json_normalize(df["player"])
                    if "id" in player_norm.columns:
                        df["player_id"] = player_norm["id"]

                # Extract player_id BEFORE flattening stats
                if "player" in df.columns:
                    player_norm = pd.json_normalize(df["player"])
                    if "id" in player_norm.columns:
                        df["player_id"] = player_norm["id"]

                # Extract team_id if present
                if "team" in df.columns:
                    team_norm = pd.json_normalize(df["team"])
                    if "id" in team_norm.columns:
                        df["team_id"] = team_norm["id"]

                # Now flatten stats
                if "stats" in df.columns:
                    stats_df = pd.json_normalize(df["stats"]).add_prefix(f"{category}_{subtype}_")
                    df = pd.concat([df.drop(columns=["stats"]), stats_df], axis=1)

                # KEEP ONLY keys that actually exist
                base_keep_cols = ["player_id", "team_id", "season", "season_type"]
                keep_cols = [col for col in base_keep_cols if col in df.columns]
                stat_cols = [c for c in df.columns if c.startswith(f"{category}_{subtype}_")]

                df = df[keep_cols + stat_cols]
                if "player_id" not in df.columns:
                    raise KeyError(
                        f"player_id missing in season averages response for category={category}, type={subtype}. "
                        f"Available columns: {list(df.columns)}"
                    )
                frames.append(df)

    if not frames:
        return pd.DataFrame()

    # Combine ALL rows instead of merging columns
    result = pd.concat(frames, ignore_index=True)

    # Remove duplicate rows per player-season
    if {"player_id", "season", "season_type"}.issubset(result.columns):
        result = result.drop_duplicates(
            subset=["player_id", "season", "season_type"],
            keep="last"
        )

    return result


def fetch_team_season_averages(season: int) -> pd.DataFrame:
    """
    Pull a practical subset of team season averages using valid team
    category/type pairings from the BALLDONTLIE NBA docs.
    """
    category_type_pairs = [
        ("general", "base"),
        ("general", "advanced"),
        ("general", "scoring"),
        ("general", "defense"),
        ("general", "opponent"),
        ("shooting", "by_zone_base"),
        ("shooting", "5ft_range_base"),
    ]

    frames: list[pd.DataFrame] = []

    for category, subtype in category_type_pairs:
        print(f"[DEBUG] fetching team season averages: category={category}, type={subtype}")

        rows = fetch_paginated(
            f"team_season_averages/{category}",
            params={
                "season": season,
                "season_type": "regular",
                "type": subtype,
            },
        )

        if not rows:
            continue

        df = pd.DataFrame(rows)
        if df.empty:
            continue

        if "stats" in df.columns:
            stats_df = pd.json_normalize(df["stats"]).add_prefix(f"team_{category}_{subtype}_")
            df = pd.concat([df.drop(columns=["stats"]), stats_df], axis=1)
        else:
            rename_map = {
                col: f"team_{category}_{subtype}_{col}"
                for col in df.columns
                if col not in {"team", "team_id", "season", "season_type"}
            }
            df = df.rename(columns=rename_map)

        frames.append(df)

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)

    if {"team_id", "season", "season_type"}.issubset(result.columns):
        result = result.drop_duplicates(
            subset=["team_id", "season", "season_type"],
            keep="last"
        )

    return result


def fetch_standings(season: int) -> pd.DataFrame:
    rows = fetch_paginated(
        "standings",
        params={
            "season": season,
        },
    )
    return pd.DataFrame(rows)


def fetch_injuries() -> pd.DataFrame:
    """
    BALLDONTLIE player injuries endpoint is NOT under /nba/v1.
    Official path:
      GET https://api.balldontlie.io/v1/player_injuries
    """
    all_rows = []
    cursor = None

    while True:
        params = {"per_page": PER_PAGE}
        if cursor is not None:
            params["cursor"] = cursor

        throttle()
        response = requests.get(
            "https://api.balldontlie.io/v1/player_injuries",
            headers=get_headers(),
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        rows = payload.get("data", [])
        meta = payload.get("meta", {}) or {}

        all_rows.extend(rows)

        cursor = meta.get("next_cursor")
        if cursor is None:
            break

    return pd.DataFrame(all_rows)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

    start_date, end_date = choose_recent_window(days_back=3)
    print(f"Fetching recent games from {start_date} to {end_date}...")

    games = fetch_games(start_date, end_date)
    print(f"[DEBUG] raw games returned: {len(games)}")

    games_df = flatten_games(games)
    print(f"[DEBUG] flattened games rows: {len(games_df)}")

    if not games_df.empty:
        games_df.to_csv(RECENT_GAMES_PATH, index=False)
        print(f"Saved games: {RECENT_GAMES_PATH} ({len(games_df)} rows)")
    else:
        print("Warning: no recent games rows to save")

    stats_rows = fetch_stats(start_date, end_date)
    print(f"[DEBUG] raw stats returned: {len(stats_rows)}")

    if stats_rows:
        print("[DEBUG] first stats row keys:", list(stats_rows[0].keys()))

    stats_df = flatten_stats(stats_rows)
    print(f"[DEBUG] flattened stats rows: {len(stats_df)}")

    if stats_df.empty:
        raise ValueError("No recent player stats found after flattening.")

    stats_df.to_csv(RECENT_PLAYER_LOGS_PATH, index=False)
    print(f"Saved player logs: {RECENT_PLAYER_LOGS_PATH} ({len(stats_df)} rows)")

    season = int(stats_df["season"].dropna().mode().iloc[0])
    player_ids = unique_player_ids(stats_df)
    print(f"[DEBUG] unique player ids: {len(player_ids)}")

    player_avg_df = fetch_player_season_averages(player_ids, season)
    print(f"[DEBUG] player season averages rows: {len(player_avg_df)}")
    if not player_avg_df.empty:
        player_avg_df.to_csv(PLAYER_SEASON_AVG_PATH, index=False)

    team_avg_df = fetch_team_season_averages(season)
    print(f"[DEBUG] team season averages rows: {len(team_avg_df)}")
    if not team_avg_df.empty:
        team_avg_df.to_csv(TEAM_SEASON_AVG_PATH, index=False)

    standings_df = fetch_standings(season)
    print(f"[DEBUG] standings rows: {len(standings_df)}")
    if not standings_df.empty:
        standings_df.to_csv(STANDINGS_PATH, index=False)

    injuries_df = fetch_injuries()
    print(f"[DEBUG] injuries rows: {len(injuries_df)}")
    if not injuries_df.empty:
        injuries_df.to_csv(INJURIES_PATH, index=False)

    print("Done.")
    print(stats_df.head())


if __name__ == "__main__":
    main()