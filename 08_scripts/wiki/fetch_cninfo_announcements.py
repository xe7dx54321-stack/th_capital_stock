#!/usr/bin/env python3
"""Fetch CNINFO announcement search results and persist raw snapshots."""

import argparse
import json
import re
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
CNINFO_SEARCH_URL = "https://www.cninfo.com.cn/new/fulltextSearch/full"
CNINFO_STATIC_PREFIX = "https://static.cninfo.com.cn/"


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.cninfo.com.cn/new/fulltextSearch",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return response.read(), content_type, dict(response.headers.items())


def announcement_search(keyword, start_date, end_date, page_size):
    params = {
        "searchkey": keyword,
        "sdate": start_date,
        "edate": end_date,
        "isfulltext": "false",
        "sortName": "pubdate",
        "sortType": "desc",
        "pageNum": "1",
        "pageSize": str(page_size),
        "type": "shj",
    }
    return fetch_json(CNINFO_SEARCH_URL + "?" + urllib.parse.urlencode(params))


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


def build_body_text(target, item, raw_url):
    notice_date = datetime.fromtimestamp((item["announcementTime"] or 0) / 1000).strftime("%Y-%m-%d")
    parts = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"公告标题：{strip_html(item.get('announcementTitle'))}",
        f"公告日期：{notice_date}",
        f"公告类型：{item.get('announcementType') or ''}",
        f"披露板块：{item.get('pageColumn') or ''}",
        f"原始文件：{raw_url}",
    ]
    return truncate_text("\n".join(parts), limit=4000)


def persist_item(target, item, fetched_at):
    raw_url = urllib.parse.urljoin(CNINFO_STATIC_PREFIX, item["adjunctUrl"])
    raw_bytes, content_type, headers = fetch_bytes(raw_url)
    clean_title = strip_html(item.get("announcementTitle")) or f"{target['name']} 公告"
    source_domain = urllib.parse.urlparse(raw_url).netloc
    notice_date = datetime.fromtimestamp((item["announcementTime"] or 0) / 1000).strftime("%Y-%m-%d")
    title = f"{target['ts_code']} {notice_date} {clean_title}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="announcement",
        source_url=raw_url,
        source_domain=source_domain,
        content_type=content_type,
        raw_bytes=raw_bytes,
        raw_extension="." + (item.get("adjunctType") or "bin").lower(),
        note=f"cninfo search result for {target['name']}",
        tags=[target.get("sector") or "", "cninfo", "announcement", target.get("pool_type") or ""],
        body_text=build_body_text(target, item, raw_url),
        metadata={
            "announcement_id": item.get("announcementId"),
            "announcement_time": item.get("announcementTime"),
            "announcement_type": item.get("announcementType"),
            "announcement_type_name": item.get("announcementTypeName"),
            "page_column": item.get("pageColumn"),
            "sec_code": item.get("secCode"),
            "sec_name": item.get("secName"),
            "adjunct_url": item.get("adjunctUrl"),
            "adjunct_type": item.get("adjunctType"),
            "adjunct_size_mb": item.get("adjunctSize"),
            "headers": headers,
        },
        extra_frontmatter={
            "provider": "cninfo",
            "notice_date": notice_date,
            "announcement_id": item.get("announcementId"),
            "sec_code": item.get("secCode"),
        },
        stable_key=item.get("announcementId") or item.get("adjunctUrl"),
        bucket_date=notice_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch CNINFO announcements for current SMR A-share targets")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--days-back", type=int, default=90, help="Search window in days")
    parser.add_argument("--per-symbol-limit", type=int, default=3, help="Maximum files to persist for each symbol")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_date = (datetime.now() - timedelta(days=args.days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    persisted = []
    failed = []
    for target in targets:
        try:
            payload = announcement_search(target["name"], start_date, end_date, args.per_symbol_limit * 4)
            matches = []
            for item in payload.get("announcements") or []:
                if str(item.get("secCode") or "").strip() != target["code"]:
                    continue
                if not item.get("adjunctUrl"):
                    continue
                matches.append(item)
                if len(matches) >= args.per_symbol_limit:
                    break
            for item in matches:
                snapshot = persist_item(target, item, fetched_at)
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
        entity_type="cninfo_announcement_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="fetch_cninfo_announcements.py",
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
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_cninfo_announcements.py",
        "success" if not failed else "warning",
        "cninfo announcements fetched",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "persisted_count": len(persisted),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "failed": failed[:20],
        },
    )
    print(f"CNINFO announcement snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} -> {item['markdown_rel_path']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']}: {item['error']}")


if __name__ == "__main__":
    main()
