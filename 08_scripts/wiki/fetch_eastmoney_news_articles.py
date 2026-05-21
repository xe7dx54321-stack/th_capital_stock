#!/usr/bin/env python3
"""Fetch Eastmoney news article pages from existing news-search snapshots."""

import argparse
import json
import re
import sqlite3
import sys
import urllib.parse
from datetime import datetime
from html import unescape
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import html_snapshot, persist_external_snapshot, truncate_text
from smr_fetch import fetch_url, response_extension
from smr_paths import env_or_project_path, project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import resolve_equity_targets
from smr_wiki import slugify

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")

TITLE_RE = re.compile(r'<div class="title">(.*?)</div>', re.S)
PUBLISHED_AT_RE = re.compile(r'<div class=" item">\s*([0-9]{4}年[0-9]{2}月[0-9]{2}日\s*[0-9]{2}:[0-9]{2})\s*</div>', re.S)
SOURCE_RE = re.compile(r'来源：\s*([\u4e00-\u9fffA-Za-z0-9_\-·（）()]+)\s*</div>', re.S)
CONTENT_RE = re.compile(r'<div class="txtinfos" id="ContentBody"[^>]*>(.*?)</div>', re.S)
DESCRIPTION_RE = re.compile(r'<meta name="description" content="([^"]*)"', re.S)
ORIGINAL_TITLE_RE = re.compile(r'<div class="sublab">\s*原标题：([^<]+)</div>', re.S)


def clean_tags(*values):
    return [value for value in values if value]


def normalize_text(text):
    return " ".join(unescape(str(text or "")).split())


def normalize_published_at(text):
    cleaned = normalize_text(text)
    if not cleaned:
        return ""
    return (
        cleaned.replace("年", "-")
        .replace("月", "-")
        .replace("日", "")
        .strip()
    )


def canonicalize_article_url(url):
    parsed = urllib.parse.urlparse(url or "")
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    elif parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    return urllib.parse.urlunparse(parsed)


def article_source_id(ts_code, article_code):
    stable_key = f"{ts_code}_{article_code}"
    return f"external_source__{slugify('eastmoney_news_article')}__{slugify(stable_key)[:120]}"


def article_snapshot_exists_on_disk(ts_code, article_code):
    entity_dir = project_path("11_smr_wiki", "raw", "external", "stock", slugify(ts_code))
    if not entity_dir.exists():
        return False
    pattern = f"*/{article_code}__news_article__*.meta.json"
    return any(entity_dir.glob(pattern))


def fetch_article(url, fetch_mode="auto", timeout=20):
    result = fetch_url(
        url,
        timeout=timeout,
        mode=fetch_mode,
        user_agent="Mozilla/5.0",
        accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        extra_headers={"Referer": "https://so.eastmoney.com/"},
    )
    return {
        **result,
        "raw_bytes": result["bytes"],
    }


def extract_article(html_text, fallback_title="", fallback_date="", fallback_media="", fallback_summary=""):
    title_match = TITLE_RE.search(html_text)
    title = normalize_text(title_match.group(1)) if title_match else normalize_text(fallback_title)

    published_match = PUBLISHED_AT_RE.search(html_text)
    published_at = normalize_published_at(published_match.group(1)) if published_match else normalize_text(fallback_date)

    source_match = SOURCE_RE.search(html_text)
    source_name = normalize_text(source_match.group(1)) if source_match else normalize_text(fallback_media)

    body_match = CONTENT_RE.search(html_text)
    body_html = body_match.group(1) if body_match else ""
    _unused_title, body_text = html_snapshot(body_html)
    body_text = truncate_text(normalize_text(body_text), limit=6000)

    description_match = DESCRIPTION_RE.search(html_text)
    description = normalize_text(description_match.group(1)) if description_match else normalize_text(fallback_summary)

    original_title_match = ORIGINAL_TITLE_RE.search(html_text)
    original_title = normalize_text(original_title_match.group(1)) if original_title_match else ""

    return {
        "title": title or normalize_text(fallback_title),
        "published_at": published_at or normalize_text(fallback_date),
        "source_name": source_name or normalize_text(fallback_media),
        "description": description or normalize_text(fallback_summary),
        "body_text": body_text or normalize_text(fallback_summary),
        "original_title": original_title,
    }


def resolve_targets(conn, args):
    return resolve_equity_targets(
        conn,
        explicit_ts_codes=args.ts_code,
        profile_name=args.profile,
        pool_types=args.pool_type,
        allowed_markets=["SZ", "SH", "BJ"],
        limit=args.limit,
    )


def latest_news_search_meta_path(conn, ts_code):
    row = conn.execute(
        """
        SELECT metadata_json
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND source_id LIKE 'external_source__eastmoney_news_search__%'
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_id DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    if row is None:
        return None
    metadata = json.loads(row[0] or "{}")
    meta_rel_path = metadata.get("meta_rel_path")
    if not meta_rel_path:
        return None
    return project_path(meta_rel_path)


def load_article_candidates(conn, ts_code, article_limit):
    meta_path = latest_news_search_meta_path(conn, ts_code)
    if meta_path is None or not meta_path.exists():
        return None, []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["_meta_rel_path"] = str(meta_path.relative_to(project_path()))
    items = meta.get("items") or []
    candidates = []
    seen = set()
    for item in items:
        url = item.get("url")
        code = item.get("code")
        if not url or not code:
            continue
        dedupe_key = (code, url)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidates.append(item)
        if len(candidates) >= article_limit:
            break
    return meta, candidates


def article_exists(conn, ts_code, article_url, article_code):
    if article_code:
        row = conn.execute(
            """
            SELECT 1
            FROM source_manifest
            WHERE source_type='external_source_snapshot'
              AND entity_id=?
              AND source_id=?
            LIMIT 1
            """,
            (ts_code, article_source_id(ts_code, article_code)),
        ).fetchone()
        if row is not None:
            return True
        if article_snapshot_exists_on_disk(ts_code, article_code):
            return True

    canonical_url = canonicalize_article_url(article_url)
    row = conn.execute(
        """
        SELECT 1
        FROM source_manifest
        WHERE source_type='external_source_snapshot'
          AND entity_id=?
          AND json_extract(metadata_json, '$.source_url') IN (?, ?)
        LIMIT 1
        """,
        (ts_code, article_url, canonical_url),
    ).fetchone()
    return row is not None


def build_body_text(target, article_code, source_name, published_at, article_title, description, article_url, body_text):
    lines = [
        f"证券代码：{target['ts_code']}",
        f"证券简称：{target['name']}",
        f"文章编号：{article_code}",
        f"发布时间：{published_at or '-'}",
        f"来源媒体：{source_name or '-'}",
        f"文章标题：{article_title or '-'}",
        f"原文链接：{article_url}",
        "",
    ]
    if description:
        lines.extend(["摘要：", description, ""])
    lines.extend(["正文：", body_text or "(empty)"])
    return truncate_text("\n".join(lines), limit=8000)


def persist_article_snapshot(target, search_meta, article_item, page_result, page_fields, fetched_at):
    final_url = page_result["final_url"]
    article_code = article_item.get("code")
    entity_article_key = f"{target['ts_code']}_{article_code}"
    published_at = page_fields["published_at"] or normalize_text(article_item.get("date"))
    bucket_date = (published_at[:10] if published_at else fetched_at[:10]) or fetched_at[:10]
    title = f"{target['ts_code']} 东方财富资讯正文 {page_fields['title'] or article_code}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type="stock",
        entity_id=target["ts_code"],
        source_kind="news_article",
        source_url=final_url,
        source_domain=urllib.parse.urlparse(final_url).netloc,
        content_type=page_result["content_type"] or "text/html; charset=utf-8",
        raw_bytes=page_result["raw_bytes"],
        raw_extension=response_extension(page_result),
        note=f"eastmoney news article for {target['name']}",
        tags=clean_tags("eastmoney", "public_news", "article_detail"),
        body_text=build_body_text(
            target,
            article_code,
            page_fields["source_name"],
            published_at,
            page_fields["title"],
            page_fields["description"],
            final_url,
            page_fields["body_text"],
        ),
        metadata={
            "requested_url": article_item.get("url"),
            "search_snapshot_meta_rel_path": str(search_meta.get("_meta_rel_path") or ""),
            "status_code": page_result["status_code"],
            "fetch_engine": page_result.get("fetch_engine"),
            "fetch_mode": page_result.get("fetch_mode"),
            "fetch_policy": page_result.get("fetch_policy"),
            "fallback_chain": page_result.get("fallback_chain"),
            "fetch_warning": page_result.get("fetch_warning"),
            "rendered": page_result.get("rendered"),
            "content_hash": page_result.get("content_hash"),
            "article_code": article_code,
            "published_at": published_at,
            "media_name": page_fields["source_name"] or article_item.get("mediaName"),
            "search_item": article_item,
        },
        extra_frontmatter={
            "provider": "eastmoney_news_article",
            "announcement_id": entity_article_key,
            "published_at": published_at,
            "media_name": page_fields["source_name"] or article_item.get("mediaName"),
            "original_title": page_fields["original_title"],
        },
        stable_key=article_code,
        bucket_date=bucket_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch Eastmoney article detail pages from existing news-search snapshots")
    parser.add_argument("--ts-code", action="append", help="Specific A-share ts_code; can be repeated")
    parser.add_argument("--profile", default="standard_external", help="Coverage profile from research_amplification_registry.md")
    parser.add_argument("--pool-type", action="append", help="Override pool type; can be repeated")
    parser.add_argument("--limit", type=int, help="Override maximum number of target symbols")
    parser.add_argument("--article-limit", type=int, default=2, help="Maximum article detail pages to persist for each symbol")
    parser.add_argument(
        "--fetch-mode",
        default="auto",
        choices=["auto", "urllib", "scrapling-static", "dynamic", "stealth"],
        help="Fetch engine policy. auto uses 00_control/source_fetch_policy.json",
    )
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--force", action="store_true", help="Fetch even if the article already exists in source_manifest")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    targets = resolve_targets(conn, args)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    persisted = []
    skipped = []
    empty = []
    failed = []
    page_cache = {}

    for target in targets:
        search_meta, items = load_article_candidates(conn, target["ts_code"], args.article_limit)
        if search_meta is None:
            empty.append({"ts_code": target["ts_code"], "reason": "missing_news_search_snapshot"})
            continue
        if not items:
            empty.append({"ts_code": target["ts_code"], "reason": "news_search_snapshot_has_no_items"})
            continue

        for item in items:
            article_url = item.get("url") or ""
            article_code = item.get("code") or ""
            if not article_url or not article_code:
                failed.append({"ts_code": target["ts_code"], "error": "missing_article_url_or_code"})
                continue
            if (not args.force) and article_exists(conn, target["ts_code"], article_url, article_code):
                skipped.append({"ts_code": target["ts_code"], "article_code": article_code, "reason": "already_exists"})
                continue
            try:
                if article_url not in page_cache:
                    page_cache[article_url] = fetch_article(article_url, fetch_mode=args.fetch_mode, timeout=args.timeout)
                    page_cache[article_url]["fetch_mode"] = args.fetch_mode
                page_result = page_cache[article_url]
                final_url = page_result["final_url"]
                if "eastmoney.com" not in urllib.parse.urlparse(final_url).netloc:
                    skipped.append({"ts_code": target["ts_code"], "article_code": article_code, "reason": "unsupported_domain"})
                    continue
                page_fields = extract_article(
                    page_result["text"],
                    fallback_title=item.get("title", ""),
                    fallback_date=item.get("date", ""),
                    fallback_media=item.get("mediaName", ""),
                    fallback_summary=item.get("content", ""),
                )
                snapshot = persist_article_snapshot(target, search_meta, item, page_result, page_fields, fetched_at)
                persisted.append(
                    {
                        "ts_code": target["ts_code"],
                        "article_code": article_code,
                        "title": snapshot["title"],
                        "markdown_rel_path": snapshot["markdown_rel_path"],
                        "raw_rel_path": snapshot["raw_rel_path"],
                    }
                )
            except Exception as exc:
                failed.append({"ts_code": target["ts_code"], "article_code": article_code, "error": str(exc)})

    register_snapshot(
        conn,
        entity_type="eastmoney_news_article_batch",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="fetched" if persisted else "empty",
        source="fetch_eastmoney_news_articles.py",
        relationships={
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "article_limit": args.article_limit,
            "force": args.force,
        },
        payload={
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_eastmoney_news_articles.py",
        "success" if not failed else "warning",
        "eastmoney news articles fetched",
        {
            "target_count": len(targets),
            "profile": args.profile,
            "requested_pool_types": args.pool_type or [],
            "limit": args.limit,
            "article_limit": args.article_limit,
            "persisted_count": len(persisted),
            "skipped_count": len(skipped),
            "empty_count": len(empty),
            "failed_count": len(failed),
            "persisted": persisted[:20],
            "skipped": skipped[:20],
            "empty": empty[:20],
            "failed": failed[:20],
        },
    )
    print(f"Eastmoney news article snapshots: {len(persisted)}")
    for item in persisted[:20]:
        print(f"- {item['ts_code']} | {item['article_code']} -> {item['markdown_rel_path']}")
    if skipped:
        print("Skipped:")
        for item in skipped[:20]:
            print(f"- {item['ts_code']} | {item['article_code']}: {item['reason']}")
    if empty:
        print("Empty:")
        for item in empty[:20]:
            print(f"- {item['ts_code']}: {item['reason']}")
    if failed:
        print("Failures:")
        for item in failed[:20]:
            print(f"- {item['ts_code']} | {item.get('article_code', '-')}: {item['error']}")


if __name__ == "__main__":
    main()
