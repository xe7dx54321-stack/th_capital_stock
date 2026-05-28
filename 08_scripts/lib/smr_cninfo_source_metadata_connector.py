#!/usr/bin/env python3
"""Phase 49 CNINFO source metadata connector."""

from __future__ import annotations
import sqlite3
from typing import Any
from smr_real_source_monitor_schema import get_sample_sources, build_real_source_metadata
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

def scan_cninfo_metadata(conn: sqlite3.Connection, ticker=TARGET_REVIEW_TICKER, *, use_network=False, use_fixture=True):
    ticker = normalize_ticker(ticker)
    sources: list[dict[str, Any]] = []
    network_used = False; fallback_used = False; fallback_reason = ""
    if use_network:
        try:
            import requests
            url = f"https://www.cninfo.com.cn/new/disclosure?stock={ticker.split('.')[0]}&pageSize=10"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select("table tbody tr")[:5]
                for row in rows:
                    cells = row.select("td")
                    if len(cells) >= 3:
                        title = cells[1].get_text(strip=True)[:80] if len(cells) > 1 else ""
                        date = cells[2].get_text(strip=True)[:10] if len(cells) > 2 else ""
                        link = cells[1].select_one("a")
                        href = link.get("href","") if link else ""
                        full_url = "https://www.cninfo.com.cn" + href if href and not href.startswith("http") else href
                        sources.append(build_real_source_metadata(ticker, "cninfo_announcement", title, date, full_url, "cninfo"))
                network_used = True
        except Exception:
            fallback_used = True; fallback_reason = "network_unavailable_or_rate_limited"
    if not network_used and use_fixture:
        sources = get_sample_sources(ticker)
        fallback_used = True; fallback_reason = "sample_fixture"
    return sources, network_used, fallback_used, fallback_reason

def build_scan_result(conn, ticker, mode="dry-run", skip_network=False):
    use_network = mode == "execute" and not skip_network
    sources, network_used, fallback_used, fallback_reason = scan_cninfo_metadata(conn, ticker, use_network=use_network)
    stypes: dict[str, int] = {}
    for s in sources:
        t = s.get("source_type","unknown")
        stypes[t] = stypes.get(t, 0) + 1
    return {"generated_at": now_ts(), "ticker": normalize_ticker(ticker),
            "cninfo_source_metadata_scan": {
                "mode": mode, "network_used": network_used, "fallback_used": fallback_used,
                "fallback_reason": fallback_reason, "sources_found": len(sources),
                "sources_written": len(sources), "duplicates_skipped": 0,
                "raw_content_saved": False, "metadata_only": True,
                "source_types": stypes, "pending_created": 0, "paper_order_created": 0, "real_trade_created": 0,
                "source_rows": sources if mode == "execute" or skip_network else [],
            },
            "safety": {"connector_creates_pending": False, "connector_creates_order": False,
                       "no_raw_saved": True, "sources_are_metadata_only": True}}
