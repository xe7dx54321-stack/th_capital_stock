#!/usr/bin/env python3
"""Small shared helpers for Phase 25 reporting and validation."""

from __future__ import annotations

from typing import Any

from smr_phase6_watchlists import load_watchlist_config
from smr_supplier_exposure_model import load_supply_chain_pilot_watchlist, normalize_ticker


DEFAULT_PHASE25_TICKERS = ["300394.SZ", "300308.SZ", "688041.SH", "002230.SZ"]


def parse_tickers(raw: str | None) -> list[str]:
    return [normalize_ticker(item) for item in str(raw or "").split(",") if normalize_ticker(item)]


def resolve_phase25_tickers(tickers: str | None = None, watchlist: str | None = None) -> list[str]:
    parsed = parse_tickers(tickers)
    if parsed:
        return parsed
    if watchlist in {None, "", "supply_chain_pilot"}:
        try:
            pilot = load_supply_chain_pilot_watchlist()
            resolved = [normalize_ticker(ticker) for ticker in pilot.get("tickers") or [] if normalize_ticker(ticker)]
            return resolved or DEFAULT_PHASE25_TICKERS
        except FileNotFoundError:
            return DEFAULT_PHASE25_TICKERS
    payload = load_watchlist_config(watchlist)
    return [normalize_ticker(item.get("ticker")) for item in payload.get("tickers") or [] if normalize_ticker(item.get("ticker"))]


def unique_list(items: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for item in items:
        marker = str(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result
