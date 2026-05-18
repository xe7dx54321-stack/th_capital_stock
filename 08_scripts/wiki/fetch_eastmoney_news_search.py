#!/usr/bin/env python3
"""Fetch Eastmoney news-search results and persist raw snapshots."""

import argparse
import json
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import datetime
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
EASTMONEY_NEWS_API = "https://search-api-web.eastmoney.com/search/jsonp"
EASTMONEY_NEWS_PAGE = "https://so.eastmoney.com/news/s"

SEARCH_SCOPE_LABELS = {
    "default": "全部",
    "title": "标题",
    "content": "正文",
}

SORT_LABELS = {
    "default": "默认排序",
    "score": "按相关度排序",
    "time": "按时间排序",
}


def clean_tags(*values):
    return [value for value in values if value]


def normalize_text(text):
    return " ".join(str(text or "").split())


def parse_jsonp(body_text):
    stripped = (body_text or "").strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    start = stripped.find("(")
    end = stripped.rfind(")")
    if start < 0 or end <= start:
        raise ValueError("unexpected eastmoney news jsonp payload")
    return json.loads(stripped[start + 1 : end])


def build_page_url(keyword, search_scope, sort):
    params = urllib.parse.urlencode(
        {
            "keyword": keyword,
            "type": search_scope,
            "sort": sort,
        }
    )
    return EASTMONEY_NEWS_PAGE + "?" + params


def fetch_news_search(keyword, search_scope, sort, page_size):
    request_payload = {
        "uid": "",
        "keyword": keyword,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientVersion": "curr",
        "clientType": "web",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": search_scope,
                "sort": sort,
                "pageIndex": 1,
                "pageSize": page_size,
                "preTag": "",
                "postTag": "",
            }
        },
    }
    query = urllib.parse.urlencode(
        {
            "cb": "jQuery_smr",
            "param": json.dumps(request_payload, ensure_ascii=False, separators=(",", ":")),
        }
    )
    page_url = build_page_url(keyword, search_scope, sort)
    request = urllib.request.Request(
        EASTMONEY_NEWS_API + "?" + query,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": page_url,
            "Accept": "*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        raw_bytes = response.read()
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        body_text = raw_bytes.decode(charset, errors="replace")
        return parse_jsonp(body_text), raw_bytes, request_payload, content_type


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
        target["keyword"] = target["name"]
        target["pool_type"] = target.get("primary_pool_type")
    return targets


def build_body_text(target, items, total_hits, search_scope, sort):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"搜索关键词：{target['keyword']}",
        f"来源页面：{build_page_url(target['keyword'], search_scope, sort)}",
        f"搜索范围：{SEARCH_SCOPE_LABELS.get(search_scope, search_scope)}",
        f"排序方式：{SORT_LABELS.get(sort, sort)}",
        f"命中资讯数：{total_hits}",
        "",
        "Top News:",
    ]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"{index}. {normalize_text(item.get('date') or '-')} | "
                f"{normalize_text(item.get('mediaName') or '-')} | "
                f"{normalize_text(item.get('title') or '-')}",
                f"   url={normalize_text(item.get('url') or '-')}",
                f"   summary={normalize_text(item.get('content') or '-')}",
            ]
        )
    return truncate_text("\n".join(lines), limit=5000)


def persist_snapshot(target, response_json, raw_bytes, request_payload, content_type, fetched_at, search_scope, sort):
    items = response_json.get("result", {}).get("cmsArticleWebOld") or []
    total_hits = response_json.get("hitsTotal") or len(items)
    if not items:
        return None

    page_url = build_page_url(target["keyword"], search_scope, sort)
    title = f"{target['ts_code']} 东方财富资讯搜索快照 {fetched_at[:10]}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="news_search",
        source_url=page_url,
        source_domain=urllib.parse.urlparse(page_url).netloc,
        content_type=content_type or "text/javascript;charset=UTF-8",
        raw_bytes=raw_bytes,
        raw_extension=".jsonp",
        note=f"eastmoney news search for {target['name']}",
        tags=clean_tags(target.get("sector"), "eastmoney", "public_news", target.get("pool_type")),
        body_text=build_body_text(target, items, total_hits, search_scope, sort),
        metadata={
            "api_url": EASTMONEY_NEWS_API,
            "request_payload": request_payload,
            "hits_total": total_hits,
            "returned_item_count": len(items),
            "search_id": response_json.get("searchId"),
            "items": items[:10],
        },
        extra_frontmatter={
            "provider": "eastmoney_news_search",
            "query_keyword": target["keyword"],
            "search_scope": search_scope,
            "sort": sort,
            "article_count": len(items),
        },
        stable_key=f"{target['ts_code']}_{fetched_at[:10]}_{search_scope}_{sort}",
        bucket_date=fetched_at[:10],
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch Eastmoney news-search snapshots for current SMR A-share targets")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument(
        "--search-scope",
        default="default",
        choices=sorted(SEARCH_SCOPE_LABELS),
        help="Eastmoney news search scope",
    )
    parser.add_argument(
        "--sort",
        default="time",
        choices=sorted(SORT_LABELS),
        help="Eastmoney news sort mode",
    )
    parser.add_argument("--per-symbol-limit", type=int, default=5, help="Maximum news rows to persist for each symbol")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    persisted = []
    empty = []
    failed = []
    for target in targets:
        try:
            response_json, raw_bytes, request_payload, content_type = fetch_news_search(
                target["keyword"],
                search_scope=args.search_scope,
                sort=args.sort,
                page_size=args.per_symbol_limit,
            )
            snapshot = persist_snapshot(
                target,
                response_json,
                raw_bytes,
                request_payload,
                content_type,
                fetched_at,
                search_scope=args.search_scope,
                sort=args.sort,
            )
            if snapshot is None:
                empty.append({"ts_code": target["ts_code"], "reason": "no_news_results"})
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
        entity_type="eastmoney_news_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="fetch_eastmoney_news_search.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "search_scope": args.search_scope,
            "sort": args.sort,
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
        "fetch_eastmoney_news_search.py",
        "success" if not failed else "warning",
        "eastmoney news search fetched",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "search_scope": args.search_scope,
            "sort": args.sort,
            "persisted_count": len(persisted),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    print(f"Eastmoney news snapshots: {len(persisted)}")
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
