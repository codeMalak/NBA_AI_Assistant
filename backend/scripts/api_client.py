from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io"
DEFAULT_PER_PAGE = 100

# GOAT = 600 req/min. Stay comfortably under that.
MIN_SECONDS_BETWEEN_REQUESTS = 0.12
_last_request_ts = 0.0


def require_api_key() -> str:
    if not API_KEY:
        raise ValueError("Missing BALLDONTLIE_API_KEY in backend/.env")
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


def request_json(
    path: str,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    throttle()
    url = f"{BASE_URL}{path}"
    response = requests.get(url, headers=get_headers(), params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_paginated(
    path: str,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    per_page: int = DEFAULT_PER_PAGE,
) -> list[dict[str, Any]]:
    """
    BALLDONTLIE uses cursor pagination, not offset pagination.
    """
    all_rows: list[dict[str, Any]] = []
    cursor = None

    while True:
        if isinstance(params, list):
            request_params = list(params)
            request_params.append(("per_page", per_page))
            if cursor is not None:
                request_params.append(("cursor", cursor))
        else:
            request_params = dict(params or {})
            request_params["per_page"] = per_page
            if cursor is not None:
                request_params["cursor"] = cursor

        payload = request_json(path, request_params)
        rows = payload.get("data", [])
        meta = payload.get("meta", {}) or {}

        all_rows.extend(rows)

        cursor = meta.get("next_cursor")
        if cursor is None:
            break

    return all_rows