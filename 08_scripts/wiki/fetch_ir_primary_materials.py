#!/usr/bin/env python3
"""Fetch official investor-relations materials for configured targets."""

import argparse
import sqlite3
import sys
import urllib.error
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_external_sources import persist_external_snapshot
from smr_official_intel import (
    DEFAULT_BROWSER_USER_AGENT,
    discover_links,
    extract_text_payload,
    fetch_url,
    parse_official_intel_target_registry,
    response_domain,
    response_extension,
    score_discovered_url,
    select_target_rows,
)
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")


def resolve_targets(args):
    registry_rows = parse_official_intel_target_registry()
    rows = select_target_rows(
        registry_rows,
        target_keys=args.target_key,
        entity_ids=args.entity_id,
        enabled_only=not args.include_disabled,
    )
    rows = [row for row in rows if row.get("ir_url")]
    if rows:
        return rows
    return [row for row in registry_rows if row.get("enabled") and row.get("ir_url")]


def build_landing_body_text(target, extracted):
    lines = [
        f"{target['company_name']} 官方 IR 入口页快照。",
        "",
        f"本地实体：{target['entity_id']}",
        f"官方入口：{target['ir_url']}",
        "",
        extracted.get("body_text") or "(empty)",
    ]
    return "\n".join(lines)


def persist_landing_snapshot(target, response, extracted, fetched_at):
    stable_key = f"{target['target_key']}_ir_landing"
    published_at = extracted.get("published_at") or fetched_at[:10]
    return persist_external_snapshot(
        title=extracted.get("title") or f"{target['company_name']} official IR landing",
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind="ir_landing_page",
        source_url=response["final_url"],
        source_domain=response_domain(response),
        content_type=response["content_type"] or "text/html; charset=utf-8",
        raw_bytes=response["bytes"],
        raw_extension=response_extension(response),
        note=f"official investor-relations landing page for {target['company_name']}",
        tags=["official_primary", "official_ir", "landing_page"],
        body_text=build_landing_body_text(target, extracted),
        metadata={
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "official_symbol": target.get("sec_symbol"),
            "published_at": published_at,
            "text_kind": extracted.get("text_kind"),
        },
        extra_frontmatter={
            "provider": "official_ir",
            "announcement_id": stable_key,
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "official_symbol": target.get("sec_symbol"),
            "published_at": published_at,
        },
        stable_key=stable_key,
        bucket_date=published_at[:10],
    )


def build_material_body_text(target, link_url, link_text, extracted):
    lines = [
        f"{target['company_name']} 官方 IR 材料。",
        "",
        f"本地实体：{target['entity_id']}",
        f"官方入口：{target['ir_url']}",
        f"材料链接：{link_url}",
        f"链接文字：{link_text or '-'}",
        "",
        extracted.get("body_text") or "(empty)",
    ]
    return "\n".join(lines)


def persist_material_snapshot(target, link_url, link_text, response, extracted, fetched_at):
    published_at = extracted.get("published_at") or fetched_at[:10]
    stable_key = link_url
    source_kind = "ir_material_pdf" if extracted.get("text_kind") == "pdf" else "ir_material_page"
    return persist_external_snapshot(
        title=extracted.get("title") or f"{target['company_name']} official IR material",
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind=source_kind,
        source_url=response["final_url"],
        source_domain=response_domain(response),
        content_type=response["content_type"] or "application/octet-stream",
        raw_bytes=response["bytes"],
        raw_extension=response_extension(response),
        note=f"official investor-relations material for {target['company_name']}",
        tags=["official_primary", "official_ir", extracted.get("text_kind") or "text"],
        body_text=build_material_body_text(target, link_url, link_text, extracted),
        metadata={
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "official_symbol": target.get("sec_symbol"),
            "published_at": published_at,
            "discovered_from_url": target["ir_url"],
            "discovered_link_text": link_text,
            "text_kind": extracted.get("text_kind"),
        },
        extra_frontmatter={
            "provider": "official_ir",
            "announcement_id": stable_key,
            "target_key": target["target_key"],
            "company_name": target["company_name"],
            "official_symbol": target.get("sec_symbol"),
            "published_at": published_at,
        },
        stable_key=stable_key,
        bucket_date=published_at[:10],
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch official IR materials into SMR raw storage")
    parser.add_argument("--target-key", action="append", help="Target key from official_intel_target_registry.md")
    parser.add_argument("--entity-id", action="append", help="Local entity id from official_intel_target_registry.md")
    parser.add_argument("--max-links", type=int, help="Override maximum direct links to follow per target")
    parser.add_argument("--max-asset-links", type=int, default=2, help="Maximum extra asset links to follow per HTML page")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--user-agent", default=DEFAULT_BROWSER_USER_AGENT)
    parser.add_argument("--include-disabled", action="store_true", help="Allow disabled target rows from registry")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = resolve_targets(args)

    outputs = []
    failures = []
    target_summaries = []

    for target in targets:
        max_links = args.max_links or target.get("max_links") or 6
        try:
            landing_response = fetch_url(
                target["ir_url"],
                timeout=args.timeout,
                user_agent=args.user_agent,
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            )
        except Exception as exc:
            failures.append({"target_key": target["target_key"], "error": f"landing_fetch_failed: {exc}"})
            continue

        landing_extracted = extract_text_payload(
            landing_response,
            title_hint=f"{target['company_name']} official IR landing",
        )
        landing_snapshot = persist_landing_snapshot(target, landing_response, landing_extracted, fetched_at)

        discovered = discover_links(
            landing_response["text"],
            landing_response["final_url"],
            include_keywords=target.get("include_keywords"),
            exclude_keywords=target.get("exclude_keywords"),
            max_links=max_links,
            allow_raw_urls=True,
        )
        seen_urls = {landing_response["final_url"]}

        landing_score = score_discovered_url(
            target["ir_url"],
            landing_response["final_url"],
            landing_extracted.get("title"),
            include_keywords=target.get("include_keywords"),
            exclude_keywords=target.get("exclude_keywords"),
        )
        material_count = 0
        if landing_score >= 12 and len(discovered) <= 2:
            material_snapshot = persist_material_snapshot(
                target,
                landing_response["final_url"],
                "",
                landing_response,
                landing_extracted,
                fetched_at,
            )
            outputs.append(
                {
                    "target_key": target["target_key"],
                    "entity_id": target["entity_id"],
                    "source_url": landing_response["final_url"],
                    "discovered_link_text": "",
                    **material_snapshot,
                }
            )
            material_count += 1

        queue = list(discovered)
        while queue:
            candidate = queue.pop(0)
            url = candidate["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                response = fetch_url(
                    url,
                    timeout=args.timeout,
                    user_agent=args.user_agent,
                    accept="text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,text/plain;q=0.8,*/*;q=0.7",
                )
            except Exception as exc:
                failures.append(
                    {
                        "target_key": target["target_key"],
                        "entity_id": target["entity_id"],
                        "url": url,
                        "error": f"material_fetch_failed: {exc}",
                    }
                )
                continue

            extracted = extract_text_payload(response, title_hint=candidate.get("link_text") or target["company_name"])
            snapshot = persist_material_snapshot(
                target,
                url,
                candidate.get("link_text") or "",
                response,
                extracted,
                fetched_at,
            )
            outputs.append(
                {
                    "target_key": target["target_key"],
                    "entity_id": target["entity_id"],
                    "source_url": response["final_url"],
                    "discovered_link_text": candidate.get("link_text") or "",
                    **snapshot,
                }
            )
            material_count += 1

            if extracted.get("text_kind") == "html" and args.max_asset_links > 0:
                extra_links = discover_links(
                    response["text"],
                    response["final_url"],
                    include_keywords=target.get("include_keywords"),
                    exclude_keywords=target.get("exclude_keywords"),
                    max_links=args.max_asset_links,
                    allow_raw_urls=True,
                )
                for extra in extra_links:
                    if extra["url"] not in seen_urls:
                        queue.append(extra)

        target_summaries.append(
            {
                "target_key": target["target_key"],
                "entity_id": target["entity_id"],
                "landing_snapshot": landing_snapshot,
                "direct_discovery_count": len(discovered),
                "material_count": material_count,
            }
        )

    entry = register_snapshot(
        conn,
        entity_type="official_ir_fetch",
        entity_id=f"official_ir__{fetched_at[:10]}",
        status="fetched",
        source="fetch_ir_primary_materials.py",
        relationships={
            "target_count": len(targets),
            "target_keys": [row["target_key"] for row in targets],
        },
        payload={
            "target_count": len(targets),
            "material_count": len(outputs),
            "targets": target_summaries,
            "outputs": outputs,
            "failures": failures,
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "fetch_ir_primary_materials.py",
        "success",
        "official IR materials fetched",
        {
            "target_count": len(targets),
            "material_count": len(outputs),
            "registry_entry_id": entry["id"],
            "failures": failures,
        },
    )
    print(f"IR targets: {len(targets)}")
    print(f"Fetched IR materials: {len(outputs)}")
    if failures:
        print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
