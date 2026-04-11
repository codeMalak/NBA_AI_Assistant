from __future__ import annotations

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io"

# cache date -> {"timestamp": ..., "games": [...]}
_GAMES_CACHE: dict[str, dict] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_games_for_date(target_date: str) -> list[dict]:
    if not BALLDONTLIE_API_KEY:
        raise ValueError("BALLDONTLIE_API_KEY is missing from .env")

    now = time.time()

    cached = _GAMES_CACHE.get(target_date)
    if cached and now - cached["timestamp"] < CACHE_TTL_SECONDS:
        return cached["games"]

    response = requests.get(
        f"{BASE_URL}/nba/v1/games",
        headers={"Authorization": BALLDONTLIE_API_KEY},
        params={"dates[]": target_date},
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    games = payload.get("data", [])

    _GAMES_CACHE[target_date] = {
        "timestamp": now,
        "games": games,
    }

    return games