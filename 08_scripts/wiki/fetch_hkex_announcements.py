#!/usr/bin/env python3
"""Fetch HKEX announcement search results and persist raw snapshots."""

import argparse
import html
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
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import combined_name_map, load_active_equity_universe, split_ts_code

DB_PATH = project_path("01_data", "db", "smr.db")
HKEX_SEARCH_PREFIX_URL = "https://www1.hkexnews.hk/search/prefix.do"
HKEX_SEARCH_PARTIAL_URL = "https://www1.hkexnews.hk/search/partial.do"
HKEX_TITLE_SEARCH_URL = "https://www1.hkexnews.hk/search/titleSearchServlet.do"
HKEX_FILE_PREFIX = "https://www1.hkexnews.hk"
POOL_PRIORITY = ["recommended", "candidate", "watchlist", "seed"]

# Current local HK universe is maintained in Chinese; use a small official-name hint
# table as a guardrail so a wrong stock code cannot silently pull the wrong issuer.
HKEX_EXPECTED_NAME_HINTS = {
    "00020.HK": "SENSETIME",
    "00981.HK": "SMIC",
    "01347.HK": "HUA HONG SEMI",
    "09980.HK": "UBTECH ROBOTICS",
    "09880.HK": "UBTECH ROBOTICS",
}


def strip_html(text):
    cleaned = html.unescape(text or "")
    cleaned = cleaned.replace("<br/>", " / ").replace("<br>", " / ").replace("<br />", " / ")
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_name(text):
    return re.sub(r"[^A-Z0-9]+", "", strip_html(text).upper())


def name_matches(expected, actual):
    expected_norm = normalize_name(expected)
    actual_norm = normalize_name(actual)
    return bool(expected_norm and actual_norm and (expected_norm in actual_norm or actual_norm in expected_norm))


def fetch_text(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=EN&market=SEHK",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=EN&market=SEHK",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return response.read(), content_type, dict(response.headers.items())


def parse_jsonp(body):
    start = body.find("(")
    end = body.rfind(")")
    if start < 0 or end <= start:
        raise ValueError("invalid jsonp payload")
    return json.loads(body[start + 1 : end])


def primary_pool(pool_types):
    for pool_type in POOL_PRIORITY:
        if pool_type in pool_types:
            return pool_type
    return pool_types[0] if pool_types else "seed"


def resolve_targets(conn, args):
    universe = load_active_equity_universe(conn, include_seed=True)
    names = combined_name_map(conn)

    if args.ts_code:
        targets = []
        for ts_code in args.ts_code:
            code, market = split_ts_code(ts_code)
            if market != "HK":
                continue
            meta = universe.get(ts_code, {})
            targets.append(
                {
                    "ts_code": ts_code,
                    "code": code,
                    "name": meta.get("name") or names.get(ts_code, code),
                    "sector": meta.get("sector"),
                    "pool_type": primary_pool(meta.get("source_pool_types", []) or ["seed"]),
                }
            )
        return targets

    targets = []
    for ts_code, meta in sorted(universe.items()):
        if meta.get("market") != "HK":
            continue
        targets.append(
            {
                "ts_code": ts_code,
                "code": split_ts_code(ts_code)[0],
                "name": meta.get("name") or names.get(ts_code, split_ts_code(ts_code)[0]),
                "sector": meta.get("sector"),
                "pool_type": primary_pool(meta.get("source_pool_types", []) or ["seed"]),
            }
        )
    return targets


def lookup_hkex_stock(query, partial):
    endpoint = HKEX_SEARCH_PARTIAL_URL if partial else HKEX_SEARCH_PREFIX_URL
    params = urllib.parse.urlencode(
        {
            "callback": "callback",
            "lang": "EN",
            "type": "A",
            "name": query,
            "market": "SEHK",
        }
    )
    return parse_jsonp(fetch_text(endpoint + "?" + params))


def resolve_stock_identity(target):
    expected_name = HKEX_EXPECTED_NAME_HINTS.get(target["ts_code"])
    search_queries = [target["code"]]
    if expected_name and expected_name not in search_queries:
        search_queries.append(expected_name)

    candidates = []
    seen = set()
    for query in search_queries:
        for partial in (False, True):
            payload = lookup_hkex_stock(query, partial=partial)
            for item in payload.get("stockInfo") or []:
                stock_id = str(item.get("stockId") or "").strip()
                code = str(item.get("code") or "").strip()
                name = strip_html(item.get("name"))
                key = (stock_id, code, name)
                if not stock_id or not code or key in seen:
                    continue
                seen.add(key)
                candidates.append({"stock_id": stock_id, "code": code, "name": name})

    exact_code = [item for item in candidates if item["code"] == target["code"]]
    if not exact_code:
        raise ValueError(f"hkex stock lookup failed for {target['ts_code']}")

    selected = exact_code[0]
    if expected_name:
        matched_by_hint = next((item for item in candidates if name_matches(expected_name, item["name"])), None)
        if not name_matches(expected_name, selected["name"]):
            if matched_by_hint and matched_by_hint["code"] != target["code"]:
                raise ValueError(
                    "registry code mismatch: "
                    f"{target['ts_code']} expected {expected_name}, hkex matched {matched_by_hint['code']} {matched_by_hint['name']}"
                )
            raise ValueError(
                "hkex name mismatch: "
                f"{target['ts_code']} expected {expected_name}, got {selected['code']} {selected['name']}"
            )
    return selected


def title_search(stock_id, start_date, end_date, row_range):
    params = urllib.parse.urlencode(
        {
            "sortDir": "0",
            "sortByOptions": "DateTime",
            "category": "0",
            "market": "SEHK",
            "stockId": str(stock_id),
            "documentType": "-1",
            "fromDate": start_date,
            "toDate": end_date,
            "title": "",
            "searchType": "0",
            "t1code": "-2",
            "t2Gcode": "-2",
            "t2code": "-2",
            "rowRange": str(row_range),
            "lang": "E",
        }
    )
    payload = fetch_json(HKEX_TITLE_SEARCH_URL + "?" + params)
    result_json = payload.get("result") or "[]"
    return payload, json.loads(result_json)


def parse_notice_date(raw_value):
    notice_dt = datetime.strptime(raw_value, "%d/%m/%Y %H:%M")
    return notice_dt.strftime("%Y-%m-%d"), notice_dt.strftime("%Y-%m-%d %H:%M:%S")


def build_body_text(target, identity, item, raw_url, notice_ts):
    parts = [
        f"证券代码：{target['ts_code']}",
        f"本地名称：{target['name']}",
        f"官方简称：{identity['name']}",
        f"公告标题：{strip_html(item.get('TITLE'))}",
        f"发布时间：{notice_ts}",
        f"公告分类：{strip_html(item.get('LONG_TEXT'))}",
        f"文件类型：{item.get('FILE_TYPE') or ''}",
        f"原始文件：{raw_url}",
    ]
    return truncate_text("\n".join(parts), limit=4000)


def raw_extension(item, raw_url):
    suffix = Path(urllib.parse.urlparse(raw_url).path).suffix
    if suffix:
        return suffix.lower()
    file_type = str(item.get("FILE_TYPE") or "bin").strip().lower()
    return "." + file_type if file_type else ".bin"


def persist_item(target, identity, item, fetched_at):
    relative_link = item.get("FILE_LINK") or ""
    raw_url = urllib.parse.urljoin(HKEX_FILE_PREFIX, relative_link)
    raw_bytes, content_type, headers = fetch_bytes(raw_url)
    notice_date, notice_ts = parse_notice_date(item["DATE_TIME"])
    clean_title = strip_html(item.get("TITLE")) or f"{identity['name']} announcement"
    title = f"{target['ts_code']} {notice_date} {clean_title}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="announcement",
        source_url=raw_url,
        source_domain=urllib.parse.urlparse(raw_url).netloc,
        content_type=content_type,
        raw_bytes=raw_bytes,
        raw_extension=raw_extension(item, raw_url),
        note=f"hkex title search result for {identity['name']}",
        tags=[target.get("sector") or "", "hkex", "announcement", target.get("pool_type") or ""],
        body_text=build_body_text(target, identity, item, raw_url, notice_ts),
        metadata={
            "stock_id": identity["stock_id"],
            "stock_name_official": identity["name"],
            "stock_code_official": strip_html(item.get("STOCK_CODE")),
            "news_id": item.get("NEWS_ID"),
            "date_time": item.get("DATE_TIME"),
            "file_type": item.get("FILE_TYPE"),
            "file_info": item.get("FILE_INFO"),
            "short_text": strip_html(item.get("SHORT_TEXT")),
            "long_text": strip_html(item.get("LONG_TEXT")),
            "title": strip_html(item.get("TITLE")),
            "dod_web_path": item.get("DOD_WEB_PATH"),
            "file_link": relative_link,
            "headers": headers,
        },
        extra_frontmatter={
            "provider": "hkexnews",
            "notice_date": notice_date,
            "news_id": item.get("NEWS_ID"),
            "stock_id": identity["stock_id"],
            "stock_name_official": identity["name"],
        },
        stable_key=item.get("NEWS_ID") or relative_link,
        bucket_date=notice_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch HKEX announcement snapshots for current SMR H-share targets")
    parser.add_argument("--ts-code", action="append", help="Specific H-share ts_code; can be repeated")
    parser.add_argument("--days-back", type=int, default=365, help="Search window in days")
    parser.add_argument("--per-symbol-limit", type=int, default=3, help="Maximum files to persist for each symbol")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_date = (datetime.now() - timedelta(days=args.days_back)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    persisted = []
    failed = []
    for target in targets:
        try:
            identity = resolve_stock_identity(target)
            _payload, announcements = title_search(
                stock_id=identity["stock_id"],
                start_date=start_date,
                end_date=end_date,
                row_range=args.per_symbol_limit,
            )
            for item in announcements[: args.per_symbol_limit]:
                snapshot = persist_item(target, identity, item, fetched_at)
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
        entity_type="hkex_announcement_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="fetch_hkex_announcements.py",
        relationships={
            "target_count": len(targets),
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
        "fetch_hkex_announcements.py",
        "success" if not failed else "warning",
        "hkex announcements fetched",
        {
            "target_count": len(targets),
            "persisted_count": len(persisted),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "failed": failed[:20],
        },
    )
    print(f"HKEX announcement snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} -> {item['markdown_rel_path']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']}: {item['error']}")


if __name__ == "__main__":
    main()
