#!/usr/bin/env python3
"""Fetch Eastmoney public stock-report listings and persist raw snapshots."""

import argparse
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot, truncate_text
from smr_paths import env_or_project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import resolve_equity_targets

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
EASTMONEY_REPORT_API = "https://reportapi.eastmoney.com/report/list2"
EASTMONEY_REPORT_PAGE = "https://data.eastmoney.com/report/stock.jshtml"


def fetch_report_list(code, start_date, end_date, page_size):
    payload = {
        "code": code,
        "industryCode": "*",
        "ratingChange": "*",
        "rating": "*",
        "orgCode": "*",
        "rcode": "",
        "pageNo": 1,
        "pageSize": page_size,
        "beginTime": start_date,
        "endTime": end_date,
    }
    req = urllib.request.Request(
        EASTMONEY_REPORT_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://data.eastmoney.com/report/stock.jshtml",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
        return json.loads(body), body.encode("utf-8"), payload


def resolve_targets(conn, args):
    targets = resolve_equity_targets(
        conn,
        explicit_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
        allowed_markets=["SZ", "SH", "BJ"],
        limit=args.limit,
    )
    for target in targets:
        target["pool_type"] = target.get("primary_pool_type")
    return targets


def market_prefixed_code(target):
    return f"{target['market']}{target['code']}"


def build_page_url(target):
    params = urllib.parse.urlencode({"scode": market_prefixed_code(target)})
    return EASTMONEY_REPORT_PAGE + "?" + params


def build_body_text(target, rows, total_hits, start_date, end_date):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"来源页面：{build_page_url(target)}",
        f"查询区间：{start_date} ~ {end_date}",
        f"命中研报数：{total_hits}",
        "",
        "Top Reports:",
    ]
    for index, item in enumerate(rows, start=1):
        lines.extend(
            [
                f"{index}. {item.get('publishDate', '')[:10]} | {item.get('orgSName') or item.get('orgName') or '-'} | "
                f"{item.get('emRatingName') or '-'} | {item.get('title') or '-'}",
                f"   infoCode={item.get('infoCode') or '-'} | stockCode={item.get('stockCode') or '-'} | researcher={item.get('researcher') or '-'}",
            ]
        )
    return truncate_text("\n".join(lines), limit=5000)


def persist_snapshot(target, response_json, raw_bytes, request_payload, fetched_at):
    matched_rows = [item for item in response_json.get("data") or [] if str(item.get("stockCode") or "").strip() == target["code"]]
    total_hits = len(matched_rows) if response_json.get("hits") in (None, "") else response_json.get("hits")
    if not matched_rows:
        return None

    page_url = build_page_url(target)
    title = f"{target['ts_code']} 东方财富公开研报快照 {fetched_at[:10]}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="research_search",
        source_url=page_url,
        source_domain=urllib.parse.urlparse(page_url).netloc,
        content_type="application/json",
        raw_bytes=raw_bytes,
        raw_extension=".json",
        note=f"eastmoney stock report list for {target['name']}",
        tags=[target.get("sector") or "", "eastmoney", "public_research", target.get("pool_type") or ""],
        body_text=build_body_text(
            target,
            matched_rows,
            total_hits,
            request_payload["beginTime"],
            request_payload["endTime"],
        ),
        metadata={
            "api_url": EASTMONEY_REPORT_API,
            "request_payload": request_payload,
            "matched_report_count": len(matched_rows),
            "hits": response_json.get("hits"),
            "items": matched_rows[:10],
        },
        extra_frontmatter={
            "provider": "eastmoney_report",
            "query_code": target["code"],
            "query_market": target["market"],
            "report_count": len(matched_rows),
        },
        stable_key=f"{target['ts_code']}_{fetched_at[:10]}",
        bucket_date=fetched_at[:10],
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch Eastmoney public research listings for current SMR A-share targets")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--days-back", type=int, default=365, help="Search window in days")
    parser.add_argument("--per-symbol-limit", type=int, default=5, help="Maximum report rows to persist for each symbol")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_date = (datetime.now() - timedelta(days=args.days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    persisted = []
    empty = []
    failed = []
    for target in targets:
        try:
            response_json, raw_bytes, request_payload = fetch_report_list(
                target["code"],
                start_date=start_date,
                end_date=end_date,
                page_size=args.per_symbol_limit,
            )
            snapshot = persist_snapshot(target, response_json, raw_bytes, request_payload, fetched_at)
            if snapshot is None:
                empty.append({"ts_code": target["ts_code"], "reason": "no_matching_reports"})
                continue
            persisted.append(
                {
                    "ts_code": target["ts_code"],
                    "title": snapshot["title"],
                    "markdown_rel_path": snapshot["markdown_rel_path"],
                    "raw_rel_path": snapshot["raw_rel_path"],
                }
            )
        except Exception as exc:
            failed.append({"ts_code": target["ts_code"], "error": str(exc)})

    register_snapshot(
        conn,
        entity_type="eastmoney_report_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="fetch_eastmoney_stock_reports.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "days_back": args.days_back,
            "per_symbol_limit": args.per_symbol_limit,
        },
        payload={
            "persisted_count": len(persisted),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_eastmoney_stock_reports.py",
        "success" if not failed else "warning",
        "eastmoney public reports fetched",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "persisted_count": len(persisted),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    print(f"Eastmoney report snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} -> {item['markdown_rel_path']}")
    if empty:
        print("Empty:")
        for item in empty[:20]:
            print(f"- {item['ts_code']}: {item['reason']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']}: {item['error']}")


if __name__ == "__main__":
    main()
