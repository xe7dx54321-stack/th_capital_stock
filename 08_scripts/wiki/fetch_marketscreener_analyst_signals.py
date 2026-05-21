#!/usr/bin/env python3
"""Fetch public analyst consensus snapshots from MarketScreener."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot
from smr_fetch import fetch_url, response_domain, response_extension
from smr_paths import project_path
from smr_public_analyst_signals import (
    DEFAULT_BROWSER_USER_AGENT,
    extract_marketscreener_consensus,
    parse_public_analyst_signal_target_registry,
    select_target_rows,
)
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")


def resolve_targets(args):
    registry_rows = parse_public_analyst_signal_target_registry()
    rows = select_target_rows(
        registry_rows,
        target_keys=args.target_key,
        entity_ids=args.entity_id,
        enabled_only=not args.include_disabled,
    )
    if rows:
        return [row for row in rows if row.get("provider") == "marketscreener" and row.get("consensus_url")]
    return [
        row
        for row in registry_rows
        if row.get("enabled") and row.get("provider") == "marketscreener" and row.get("consensus_url")
    ]


def build_body_text(target, extracted, snapshot_date):
    lines = [
        f"{target['company_name']} MarketScreener 公开卖方信号摘要。",
        "",
        f"本地实体：{target['entity_id']}",
        f"股票代码：{target.get('symbol') or target['entity_id']}",
        f"快照日期：{snapshot_date}",
        f"共识评级：{extracted.get('mean_consensus') or '-'}",
        f"覆盖分析师数量：{extracted.get('analysts_count') or '-'}",
        f"最新收盘价：{extracted.get('last_close_raw') or '-'}",
        f"平均目标价：{extracted.get('average_target_raw') or '-'}",
        f"平均目标空间：{format_percent(extracted.get('spread_avg_target_pct'))}",
        f"最高目标价：{extracted.get('high_target_raw') or '-'}",
        f"最高目标空间：{format_percent(extracted.get('spread_high_target_pct'))}",
        f"最低目标价：{extracted.get('low_target_raw') or '-'}",
        f"最低目标空间：{format_percent(extracted.get('spread_low_target_pct'))}",
        "",
        "说明：这是一手公开卖方摘要页快照，不等于授权全文研报。",
    ]
    return "\n".join(lines)


def format_percent(value):
    if value is None:
        return "-"
    if value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"


def persist_snapshot(target, response, extracted, fetched_at):
    snapshot_date = fetched_at[:10]
    stable_key = f"{target['target_key']}_{snapshot_date}"
    return persist_external_snapshot(
        title=extracted.get("title") or f"{target['company_name']} MarketScreener consensus",
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind="public_analyst_signal",
        source_url=response["final_url"],
        source_domain=response_domain(response),
        content_type=response["content_type"] or "text/html; charset=utf-8",
        raw_bytes=response["bytes"],
        raw_extension=response_extension(response),
        note=f"public analyst consensus summary from MarketScreener for {target['company_name']}",
        tags=["public_sellside_signal", "marketscreener", "consensus"],
        body_text=build_body_text(target, extracted, snapshot_date),
        metadata={
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "symbol": target.get("symbol") or target["entity_id"],
            "market": target.get("market"),
            "provider": "marketscreener",
            "fetch_engine": response.get("fetch_engine"),
            "fetch_mode": response.get("fetch_mode"),
            "fetch_policy": response.get("fetch_policy"),
            "fallback_chain": response.get("fallback_chain"),
            "fetch_warning": response.get("fetch_warning"),
            "rendered": response.get("rendered"),
            "content_hash": response.get("content_hash"),
            "snapshot_date": snapshot_date,
            "published_at": snapshot_date,
            "mean_consensus": extracted.get("mean_consensus"),
            "analysts_count": extracted.get("analysts_count"),
            "last_close_price": extracted.get("last_close_price"),
            "last_close_currency": extracted.get("last_close_currency"),
            "last_close_raw": extracted.get("last_close_raw"),
            "average_target_price": extracted.get("average_target_price"),
            "average_target_currency": extracted.get("average_target_currency"),
            "average_target_raw": extracted.get("average_target_raw"),
            "spread_avg_target_pct": extracted.get("spread_avg_target_pct"),
            "high_target_price": extracted.get("high_target_price"),
            "high_target_currency": extracted.get("high_target_currency"),
            "high_target_raw": extracted.get("high_target_raw"),
            "spread_high_target_pct": extracted.get("spread_high_target_pct"),
            "low_target_price": extracted.get("low_target_price"),
            "low_target_currency": extracted.get("low_target_currency"),
            "low_target_raw": extracted.get("low_target_raw"),
            "spread_low_target_pct": extracted.get("spread_low_target_pct"),
            "page_title": extracted.get("page_title"),
            "consensus_url": extracted.get("consensus_url"),
        },
        extra_frontmatter={
            "provider": "marketscreener",
            "announcement_id": stable_key,
            "company_name": target["company_name"],
            "official_symbol": target.get("symbol") or target["entity_id"],
            "published_at": snapshot_date,
        },
        stable_key=stable_key,
        bucket_date=snapshot_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch MarketScreener consensus pages into SMR raw storage")
    parser.add_argument("--target-key", action="append", help="Target key from public_analyst_signal_target_registry.md")
    parser.add_argument("--entity-id", action="append", help="Local entity id from public_analyst_signal_target_registry.md")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--user-agent", default=DEFAULT_BROWSER_USER_AGENT)
    parser.add_argument(
        "--fetch-mode",
        default="auto",
        choices=["auto", "urllib", "scrapling-static", "dynamic", "stealth"],
        help="Fetch engine policy. auto uses 00_control/source_fetch_policy.json",
    )
    parser.add_argument("--wait-selector", default="body", help="CSS selector to wait for in dynamic/stealth mode")
    parser.add_argument(
        "--no-dynamic-retry-on-parse-failure",
        action="store_true",
        help="Disable dynamic retry when the static page fetched but required fields were not found",
    )
    parser.add_argument("--include-disabled", action="store_true", help="Allow disabled target rows from registry")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = resolve_targets(args)

    outputs = []
    failures = []

    for target in targets:
        try:
            response = fetch_url(
                target["consensus_url"],
                timeout=args.timeout,
                mode=args.fetch_mode,
                user_agent=args.user_agent,
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                wait_selector=args.wait_selector,
            )
            response["fetch_mode"] = args.fetch_mode
            try:
                extracted = extract_marketscreener_consensus(response, target)
            except ValueError as exc:
                if args.fetch_mode == "auto" and not args.no_dynamic_retry_on_parse_failure:
                    retry_response = fetch_url(
                        target["consensus_url"],
                        timeout=max(args.timeout, 45),
                        mode="dynamic",
                        user_agent=args.user_agent,
                        accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        wait_selector=args.wait_selector,
                    )
                    retry_response["fetch_mode"] = "dynamic_retry_after_parse_failure"
                    retry_response["parse_retry_reason"] = str(exc)
                    response = retry_response
                    extracted = extract_marketscreener_consensus(response, target)
                else:
                    raise
            snapshot = persist_snapshot(target, response, extracted, fetched_at)
            outputs.append(
                {
                    "target_key": target["target_key"],
                    "entity_id": target["entity_id"],
                    "provider": "marketscreener",
                    "mean_consensus": extracted.get("mean_consensus"),
                    "analysts_count": extracted.get("analysts_count"),
                    "spread_avg_target_pct": extracted.get("spread_avg_target_pct"),
                    **snapshot,
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "target_key": target["target_key"],
                    "entity_id": target["entity_id"],
                    "url": target.get("consensus_url"),
                    "error": str(exc),
                }
            )

    entry = register_snapshot(
        conn,
        entity_type="public_analyst_signal_fetch",
        entity_id=f"marketscreener__{fetched_at[:10]}",
        status="fetched",
        source="fetch_marketscreener_analyst_signals.py",
        relationships={
            "target_count": len(targets),
            "target_keys": [row["target_key"] for row in targets],
            "provider": "marketscreener",
        },
        payload={
            "target_count": len(targets),
            "output_count": len(outputs),
            "provider": "marketscreener",
            "outputs": outputs,
            "failures": failures,
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_marketscreener_analyst_signals.py",
        "success",
        "public analyst signals fetched from MarketScreener",
        {
            "target_count": len(targets),
            "output_count": len(outputs),
            "registry_entry_id": entry["id"],
            "failures": failures,
        },
    )
    print(f"MarketScreener targets: {len(targets)}")
    print(f"Fetched analyst signal snapshots: {len(outputs)}")
    if failures:
        print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
