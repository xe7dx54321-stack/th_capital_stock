#!/usr/bin/env python3
"""Minimal CN/HK/US market calendar helpers for daily-bar freshness checks."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable


MARKET_ALIASES = {
    "A": "A",
    "CN": "A",
    "SH": "A",
    "SZ": "A",
    "BJ": "A",
    "H": "H",
    "HK": "H",
    "US": "US",
    "USA": "US",
}

# Explicit 2026 holidays cover the current operating window. Weekends are always
# excluded; missing exchange-specific half days can be added here without
# changing downstream gate logic.
HOLIDAYS_2026 = {
    "A": {
        "2026-01-01",
        "2026-02-16",
        "2026-02-17",
        "2026-02-18",
        "2026-02-19",
        "2026-02-20",
        "2026-04-06",
        "2026-05-01",
        "2026-06-19",
        "2026-09-25",
        "2026-10-01",
        "2026-10-02",
        "2026-10-05",
        "2026-10-06",
        "2026-10-07",
    },
    "H": {
        "2026-01-01",
        "2026-02-17",
        "2026-02-18",
        "2026-02-19",
        "2026-04-03",
        "2026-04-06",
        "2026-04-07",
        "2026-05-01",
        "2026-05-25",
        "2026-06-19",
        "2026-07-01",
        "2026-09-26",
        "2026-10-01",
        "2026-10-19",
        "2026-12-25",
    },
    "US": {
        "2026-01-01",
        "2026-01-19",
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
        "2026-11-26",
        "2026-12-25",
    },
}


def normalize_calendar_market(market: str | None) -> str:
    text = str(market or "A").strip().upper()
    return MARKET_ALIASES.get(text, text)


def _as_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text[:10]).date()
    except ValueError:
        return None


def _holiday_set(market: str, year: int) -> set[str]:
    if year == 2026:
        return HOLIDAYS_2026.get(normalize_calendar_market(market), set())
    return set()


def is_trading_day(market: str, day: date | datetime | str | None) -> bool:
    actual = _as_date(day)
    if actual is None:
        return False
    normalized = normalize_calendar_market(market)
    if actual.weekday() >= 5:
        return False
    return actual.isoformat() not in _holiday_set(normalized, actual.year)


def previous_trading_day(market: str, day: date | datetime | str | None, include_same: bool = True) -> date:
    actual = _as_date(day) or datetime.now().date()
    if not include_same:
        actual = actual - timedelta(days=1)
    for _ in range(370):
        if is_trading_day(market, actual):
            return actual
        actual = actual - timedelta(days=1)
    raise RuntimeError(f"Could not resolve previous trading day for {market}")


def get_expected_latest_trading_day(market: str, now: datetime | None = None) -> date:
    now = now or datetime.now()
    normalized = normalize_calendar_market(market)
    today = now.date()
    if normalized in {"A", "H"}:
        close_hour = 18 if normalized == "A" else 18
        anchor = today if now.hour >= close_hour else today - timedelta(days=1)
        return previous_trading_day(normalized, anchor, include_same=True)
    if normalized == "US":
        # From Asia/Shanghai, the latest completed US session is normally the
        # previous calendar date after the US close has fully settled locally.
        anchor = today - timedelta(days=1 if now.hour >= 7 else 2)
        return previous_trading_day("US", anchor, include_same=True)
    return previous_trading_day(normalized, today, include_same=True)


def get_missing_trading_sessions(
    market: str,
    actual_latest: date | datetime | str | None,
    expected_latest: date | datetime | str | None,
) -> list[date]:
    actual = _as_date(actual_latest)
    expected = _as_date(expected_latest)
    if expected is None:
        return []
    if actual is None:
        start = expected - timedelta(days=30)
    else:
        start = actual + timedelta(days=1)
    sessions = []
    current = start
    while current <= expected:
        if is_trading_day(market, current):
            sessions.append(current)
        current += timedelta(days=1)
    return sessions


def iso_dates(days: Iterable[date]) -> list[str]:
    return [item.isoformat() for item in days]
