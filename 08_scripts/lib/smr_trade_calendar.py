"""Shared trade-calendar helpers for A-share, Hong Kong, and US market views."""

from __future__ import annotations

from datetime import date, datetime, timedelta

# Official A-share 2026 holiday schedule based on SSE / SZSE notices published
# on 2025-12-22. We only hard-code the market where the current system already
# has a known holiday mismatch. HK / US keep weekday fallback until official
# calendars are wired into the project.
A_SHARE_HOLIDAYS = {
    2026: {
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
        date(2026, 2, 15),
        date(2026, 2, 16),
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 2, 19),
        date(2026, 2, 20),
        date(2026, 2, 21),
        date(2026, 2, 22),
        date(2026, 2, 23),
        date(2026, 4, 4),
        date(2026, 4, 5),
        date(2026, 4, 6),
        date(2026, 5, 1),
        date(2026, 5, 2),
        date(2026, 5, 3),
        date(2026, 5, 4),
        date(2026, 5, 5),
        date(2026, 6, 19),
        date(2026, 6, 20),
        date(2026, 6, 21),
        date(2026, 9, 25),
        date(2026, 9, 26),
        date(2026, 9, 27),
        date(2026, 10, 1),
        date(2026, 10, 2),
        date(2026, 10, 3),
        date(2026, 10, 4),
        date(2026, 10, 5),
        date(2026, 10, 6),
        date(2026, 10, 7),
    }
}

MARKET_HOLIDAYS = {
    "A": A_SHARE_HOLIDAYS,
    "H": {},
    "US": {},
}

MARKET_CLOSE_HOUR = {
    "A": 16,
    "H": 16,
}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d")


def holiday_dates(market: str, year: int) -> set[date]:
    market_map = MARKET_HOLIDAYS.get(market) or {}
    return market_map.get(year, set())


def is_trade_day(value: date, market: str) -> bool:
    if value.weekday() >= 5:
        return False
    return value not in holiday_dates(market, value.year)


def previous_trade_day(value: date, market: str) -> date:
    cursor = value - timedelta(days=1)
    while not is_trade_day(cursor, market):
        cursor -= timedelta(days=1)
    return cursor


def expected_trade_date(now: datetime, market: str, mode: str = "status") -> date:
    today = now.date()
    if market == "US":
        return previous_trade_day(today, market)

    if mode == "morning":
        return previous_trade_day(today, market)
    if mode == "afternoon":
        if is_trade_day(today, market):
            return today
        return previous_trade_day(today, market)

    close_hour = MARKET_CLOSE_HOUR.get(market, 16)
    if is_trade_day(today, market) and now.hour >= close_hour:
        return today
    return previous_trade_day(today, market)


def expected_trade_dates(now: datetime, mode: str = "status") -> dict[str, date]:
    a_expected = expected_trade_date(now, "A", mode=mode)
    hk_expected = expected_trade_date(now, "H", mode=mode)
    us_expected = expected_trade_date(now, "US", mode=mode)
    return {
        "a_expected": a_expected,
        "hk_expected": hk_expected,
        "us_expected": us_expected,
        "cn_factor_expected": max(a_expected, hk_expected),
    }


def trade_day_lag(latest: date | None, expected: date | None, market: str) -> int | None:
    if latest is None or expected is None:
        return None
    if latest >= expected:
        return 0

    lag = 0
    cursor = latest
    while cursor < expected:
        cursor += timedelta(days=1)
        if is_trade_day(cursor, market):
            lag += 1
    return lag
