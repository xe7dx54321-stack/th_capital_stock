#!/usr/bin/env python3
"""Fetch and persist raw external web sources for SMR research provenance."""

import argparse
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import html_snapshot, persist_external_snapshot, truncate_text
from smr_fetch import DEFAULT_BROWSER_USER_AGENT, fetch_url, response_extension
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import slugify

DB_PATH = project_path("01_data", "db", "smr.db")


def main():
    parser = argparse.ArgumentParser(description="Fetch external source snapshots into SMR raw storage")
    parser.add_argument("--url", action="append", required=True, help="Source URL; can be repeated")
    parser.add_argument("--entity-type", required=True, help="Target entity type, such as stock/sector/topic")
    parser.add_argument("--entity-id", required=True, help="Target entity id, such as 300394.SZ")
    parser.add_argument("--source-kind", default="news", help="Source kind, such as news/announcement/research")
    parser.add_argument("--title", help="Optional fixed title when fetching a single URL")
    parser.add_argument("--tag", action="append", default=[], help="Extra tag; can be repeated")
    parser.add_argument("--note", help="Optional note to store in snapshot")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--fetch-mode",
        default="auto",
        choices=["auto", "urllib", "scrapling-static", "dynamic", "stealth"],
        help="Fetch engine policy. auto uses 00_control/source_fetch_policy.json",
    )
    parser.add_argument("--wait-selector", help="Optional CSS selector to wait for in dynamic/stealth mode")
    parser.add_argument("--user-agent", default=DEFAULT_BROWSER_USER_AGENT)
    args = parser.parse_args()

    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outputs = []

    for index, url in enumerate(args.url, start=1):
        result = fetch_url(
            url,
            timeout=args.timeout,
            mode=args.fetch_mode,
            user_agent=args.user_agent,
            wait_selector=args.wait_selector,
        )
        title = args.title if args.title and len(args.url) == 1 else ""
        content_type = result["content_type"] or "text/html"
        source_domain = urllib.parse.urlparse(result["final_url"]).netloc

        extracted_title = ""
        body_text = result["text"]
        if "html" in content_type.lower() or "<html" in result["text"].lower():
            extracted_title, body_text = html_snapshot(result["text"])
        body_text = truncate_text(body_text)
        final_title = title or extracted_title or f"{args.entity_id} {args.source_kind} source {index}"

        snapshot = persist_external_snapshot(
            title=final_title,
            fetched_at=fetched_at,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            source_kind=args.source_kind,
            source_url=result["final_url"],
            source_domain=source_domain,
            content_type=content_type,
            note=args.note,
            tags=args.tag,
            body_text=body_text,
            raw_bytes=result["bytes"],
            raw_extension=response_extension(result),
            metadata={
                "requested_url": url,
                "status_code": result["status_code"],
                "headers": result["headers"],
                "fetch_engine": result.get("fetch_engine"),
                "fetch_mode": args.fetch_mode,
                "fetch_policy": result.get("fetch_policy"),
                "fallback_chain": result.get("fallback_chain"),
                "fetch_warning": result.get("fetch_warning"),
                "rendered": result.get("rendered"),
                "content_hash": result.get("content_hash"),
            },
        )
        outputs.append({"url": result["final_url"], **snapshot})

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    register_snapshot(
        conn,
        entity_type="external_source_fetch",
        entity_id=f"{slugify(args.entity_type)}__{slugify(args.entity_id)}__{datetime.now().strftime('%Y%m%d')}",
        status="fetched",
        source="fetch_external_source.py",
        relationships={
            "entity_type": args.entity_type,
            "entity_id": args.entity_id,
            "source_kind": args.source_kind,
        },
        payload={
            "fetched_count": len(outputs),
            "outputs": outputs,
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_external_source.py",
        "success",
        "external sources fetched",
        {
            "entity_type": args.entity_type,
            "entity_id": args.entity_id,
            "source_kind": args.source_kind,
            "fetched_count": len(outputs),
            "outputs": outputs,
        },
    )
    print(f"Fetched external sources: {len(outputs)}")
    for item in outputs:
        print(f"- {item['title']} -> {item['markdown_rel_path']}")


if __name__ == "__main__":
    main()
