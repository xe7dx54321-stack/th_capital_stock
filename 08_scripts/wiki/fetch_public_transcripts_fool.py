#!/usr/bin/env python3
"""Fetch public earnings-call transcripts from The Motley Fool."""

import argparse
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot
from smr_official_intel import response_domain, response_extension
from smr_paths import project_path
from smr_public_transcripts import (
    DEFAULT_BROWSER_USER_AGENT,
    FOOL_LISTING_URL,
    extract_fool_listing_entries,
    extract_fool_transcript,
    fetch_url,
    match_target_to_entry,
    parse_public_transcript_target_registry,
    select_target_rows,
    transcript_target_mismatch_reason,
)
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
QUOTE_TRANSCRIPT_URL_RE = re.compile(r"/earnings/call-transcripts/\d{4}/\d{2}/\d{2}/[^\"\\]+/")


def resolve_targets(args):
    registry_rows = parse_public_transcript_target_registry()
    rows = select_target_rows(
        registry_rows,
        target_keys=args.target_key,
        entity_ids=args.entity_id,
        enabled_only=not args.include_disabled,
    )
    if rows:
        return [row for row in rows if row.get("provider") == "fool"]
    return [row for row in registry_rows if row.get("enabled") and row.get("provider") == "fool"]


def listing_url_for_page(page_number):
    if page_number <= 1:
        return FOOL_LISTING_URL
    return f"{FOOL_LISTING_URL}page/{page_number}/"


def fetch_fool_page(url, timeout, user_agent, retry_count):
    last_error = None
    for attempt in range(1, max(1, retry_count) + 1):
        try:
            return fetch_url(
                url,
                timeout=timeout,
                user_agent=user_agent,
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            )
        except Exception as exc:
            last_error = exc
            if attempt < max(1, retry_count):
                time.sleep(min(attempt, 2))
    raise last_error


def quote_market_slugs(target):
    market = str(target.get("market") or "").strip().upper()
    if market == "HK":
        return ["nyse", "nasdaq"]
    return ["nasdaq", "nyse"]


def quote_url_for_target(target, market_slug):
    symbol = str(target.get("symbol") or "").strip().lower()
    if not symbol:
        return None
    return f"https://www.fool.com/quote/{market_slug}/{symbol}/"


def title_from_transcript_url(url):
    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ")


def discover_quote_page_candidates(target, timeout, user_agent, retry_count, max_candidates_per_target):
    entries = []
    seen_urls = set()
    for market_slug in quote_market_slugs(target):
        quote_url = quote_url_for_target(target, market_slug)
        if not quote_url:
            continue
        try:
            response = fetch_fool_page(
                quote_url,
                timeout=timeout,
                user_agent=user_agent,
                retry_count=retry_count,
            )
        except Exception:
            continue
        for href in QUOTE_TRANSCRIPT_URL_RE.findall(response.get("text") or ""):
            article_url = f"https://www.fool.com{href}"
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)
            entries.append(
                {
                    "target": target,
                    "entry": {"url": article_url, "title": title_from_transcript_url(article_url)},
                    "page_number": None,
                    "page_url": response.get("final_url") or quote_url,
                    "discovery_method": "quote_page",
                }
            )
            if len(entries) >= max_candidates_per_target:
                return entries
    return entries


def discover_target_articles(targets, timeout, user_agent, max_pages, retry_count, max_candidates_per_target=3):
    candidates = {target["target_key"]: [] for target in targets}
    listing_pages = []

    remaining_targets = []
    for target in targets:
        target_key = target["target_key"]
        quote_candidates = discover_quote_page_candidates(
            target,
            timeout=timeout,
            user_agent=user_agent,
            retry_count=retry_count,
            max_candidates_per_target=max_candidates_per_target,
        )
        if quote_candidates:
            candidates[target_key].extend(quote_candidates)
            continue
        remaining_targets.append(target)

    if not remaining_targets:
        return candidates, listing_pages

    for page_number in range(1, max_pages + 1):
        page_url = listing_url_for_page(page_number)
        try:
            response = fetch_fool_page(
                page_url,
                timeout=timeout,
                user_agent=user_agent,
                retry_count=retry_count,
            )
        except Exception as exc:
            listing_pages.append(
                {
                    "page_number": page_number,
                    "page_url": page_url,
                    "entry_count": 0,
                    "error": str(exc),
                }
            )
            continue
        entries = extract_fool_listing_entries(response.get("text") or "")
        listing_pages.append(
            {
                "page_number": page_number,
                "page_url": response.get("final_url") or page_url,
                "entry_count": len(entries),
            }
        )
        if not entries:
            break
        for entry in entries:
            for target in remaining_targets:
                target_key = target["target_key"]
                if len(candidates[target_key]) >= max_candidates_per_target:
                    continue
                if not match_target_to_entry(target, entry):
                    continue
                candidates[target_key].append(
                    {
                        "target": target,
                        "entry": entry,
                        "page_number": page_number,
                        "page_url": response.get("final_url") or page_url,
                        "discovery_method": "listing_page",
                    }
                )
    return candidates, listing_pages


def build_body_text(target, extracted):
    lines = [
        f"{target['company_name']} The Motley Fool 公开电话会文字稿。",
        "",
        f"本地实体：{target['entity_id']}",
        f"股票代码：{extracted.get('symbol') or target.get('symbol') or target['entity_id']}",
        f"发布时间：{extracted.get('published_at') or '-'}",
        f"季度标签：{extracted.get('quarter_label') or '-'}",
        f"发言人数：{extracted.get('speaker_count') or 0}",
        f"发言人：{', '.join(extracted.get('speakers') or []) or '-'}",
        f"摘要：{extracted.get('summary') or '-'}",
        "",
        extracted.get("transcript_text") or "(empty)",
    ]
    return "\n".join(lines)


def persist_snapshot(target, response, extracted, fetched_at):
    published_at = extracted.get("published_at") or fetched_at
    bucket_date = published_at[:10]
    stable_key = f"{target['target_key']}_{bucket_date}"
    return persist_external_snapshot(
        title=extracted.get("title") or f"{target['company_name']} earnings call transcript",
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind="public_transcript",
        source_url=response["final_url"],
        source_domain=response_domain(response),
        content_type=response["content_type"] or "text/html; charset=utf-8",
        raw_bytes=response["bytes"],
        raw_extension=response_extension(response),
        note=f"public earnings-call transcript from The Motley Fool for {target['company_name']}",
        tags=["public_transcript", "fool", "earnings_call"],
        body_text=build_body_text(target, extracted),
        metadata={
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "symbol": extracted.get("symbol") or target.get("symbol") or target["entity_id"],
            "market": target.get("market"),
            "provider": "fool",
            "published_at": published_at,
            "article_author": extracted.get("article_author"),
            "article_type": extracted.get("article_type"),
            "collection": extracted.get("collection"),
            "page_type": extracted.get("page_type"),
            "quarter_label": extracted.get("quarter_label"),
            "company_label": extracted.get("company_label"),
            "speaker_count": extracted.get("speaker_count"),
            "speakers": extracted.get("speakers") or [],
            "transcript_word_count": extracted.get("transcript_word_count"),
            "summary": extracted.get("summary"),
        },
        extra_frontmatter={
            "provider": "fool",
            "announcement_id": stable_key,
            "company_name": target["company_name"],
            "official_symbol": extracted.get("symbol") or target.get("symbol") or target["entity_id"],
            "published_at": bucket_date,
        },
        stable_key=stable_key,
        bucket_date=bucket_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch public earnings-call transcripts from The Motley Fool")
    parser.add_argument("--target-key", action="append", help="Target key from public_transcript_target_registry.md")
    parser.add_argument("--entity-id", action="append", help="Local entity id from public_transcript_target_registry.md")
    parser.add_argument("--max-pages", type=int, default=40, help="Maximum listing pages to scan")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retry-count", type=int, default=2, help="Retry attempts per listing/article request")
    parser.add_argument("--user-agent", default=DEFAULT_BROWSER_USER_AGENT)
    parser.add_argument("--include-disabled", action="store_true", help="Allow disabled target rows from registry")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = resolve_targets(args)

    outputs = []
    failures = []

    candidates_by_target, listing_pages = discover_target_articles(
        targets,
        timeout=args.timeout,
        user_agent=args.user_agent,
        max_pages=args.max_pages,
        retry_count=args.retry_count,
    )

    for target in targets:
        target_key = target["target_key"]
        target_candidates = candidates_by_target.get(target_key) or []
        if not target_candidates:
            failures.append(
                {
                    "target_key": target_key,
                    "entity_id": target["entity_id"],
                    "provider": "fool",
                    "error": f"no_transcript_found_within_{args.max_pages}_pages",
                }
            )
            continue

        candidate_failures = []
        matched_output = None
        for match in target_candidates:
            entry = match["entry"]
            try:
                response = fetch_fool_page(
                    entry["url"],
                    timeout=args.timeout,
                    user_agent=args.user_agent,
                    retry_count=args.retry_count,
                )
                extracted = extract_fool_transcript(response, target)
                mismatch_reason = transcript_target_mismatch_reason(target, extracted)
                if mismatch_reason:
                    raise ValueError(mismatch_reason)
                snapshot = persist_snapshot(target, response, extracted, fetched_at)
                matched_output = {
                    "target_key": target_key,
                    "entity_id": target["entity_id"],
                    "provider": "fool",
                    "discovery_method": match.get("discovery_method") or "listing_page",
                    "matched_listing_page": match["page_number"],
                    "listing_page_url": match["page_url"],
                    "article_url": entry["url"],
                    "published_at": extracted.get("published_at"),
                    "quarter_label": extracted.get("quarter_label"),
                    "speaker_count": extracted.get("speaker_count"),
                    **snapshot,
                }
                break
            except Exception as exc:
                candidate_failures.append(
                    {
                        "article_url": entry["url"],
                        "matched_listing_page": match["page_number"],
                        "discovery_method": match.get("discovery_method") or "listing_page",
                        "error": str(exc),
                    }
                )

        if matched_output:
            outputs.append(matched_output)
            continue

        failure_entry = {
            "target_key": target_key,
            "entity_id": target["entity_id"],
            "provider": "fool",
            "candidate_count": len(target_candidates),
            "candidate_failures": candidate_failures,
        }
        if candidate_failures:
            failure_entry["article_url"] = candidate_failures[0]["article_url"]
            failure_entry["error"] = candidate_failures[-1]["error"]
        else:
            failure_entry["error"] = f"candidate_resolution_failed_within_{args.max_pages}_pages"
        failures.append(failure_entry)

    entry = register_snapshot(
        conn,
        entity_type="public_transcript_fetch",
        entity_id=f"fool__{fetched_at[:10]}",
        status="fetched",
        source="fetch_public_transcripts_fool.py",
        relationships={
            "target_count": len(targets),
            "target_keys": [row["target_key"] for row in targets],
            "provider": "fool",
        },
        payload={
            "target_count": len(targets),
            "output_count": len(outputs),
            "provider": "fool",
            "max_pages": args.max_pages,
            "listing_pages": listing_pages,
            "outputs": outputs,
            "failures": failures,
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_public_transcripts_fool.py",
        "success",
        "public transcripts fetched from The Motley Fool",
        {
            "target_count": len(targets),
            "output_count": len(outputs),
            "registry_entry_id": entry["id"],
            "failures": failures,
        },
    )
    print(f"Fool transcript targets: {len(targets)}")
    print(f"Fetched public transcript snapshots: {len(outputs)}")
    if failures:
        print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
