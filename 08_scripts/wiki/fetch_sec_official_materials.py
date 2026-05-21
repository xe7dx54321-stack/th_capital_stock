#!/usr/bin/env python3
"""Fetch official SEC filing materials for configured targets."""

import argparse
import json
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
    DEFAULT_SEC_USER_AGENT,
    extract_text_payload,
    fetch_sec_index,
    fetch_sec_submissions,
    fetch_url,
    filter_sec_filings,
    list_recent_sec_filings,
    parse_official_intel_target_registry,
    response_domain,
    response_extension,
    sec_company_lookup,
    sec_document_url,
    sec_index_url,
    select_sec_material_entries,
    select_target_rows,
)
from smr_paths import project_path
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
DEFAULT_FORMS = ("8-K", "6-K", "10-K", "10-Q", "20-F")


def resolve_targets(args):
    if args.symbol and not (args.target_key or args.entity_id):
        return [
            {
                "target_key": f"ad_hoc_{str(raw_symbol or '').strip().lower()}",
                "entity_type": "stock",
                "entity_id": str(raw_symbol or "").strip().upper(),
                "company_name": str(raw_symbol or "").strip().upper(),
                "market": "US",
                "sec_symbol": str(raw_symbol or "").strip().upper(),
                "ir_url": "",
                "include_keywords": [],
                "exclude_keywords": [],
                "max_links": args.max_materials,
                "status": "ad_hoc",
                "enabled": True,
                "notes": "ad hoc SEC target",
            }
            for raw_symbol in args.symbol
            if str(raw_symbol or "").strip()
        ]
    registry_rows = parse_official_intel_target_registry()
    selected = select_target_rows(
        registry_rows,
        target_keys=args.target_key,
        entity_ids=args.entity_id,
        enabled_only=not args.include_disabled,
    )
    existing_symbols = {row.get("sec_symbol") for row in selected if row.get("sec_symbol")}
    for raw_symbol in args.symbol or []:
        symbol = str(raw_symbol or "").strip().upper()
        if not symbol or symbol in existing_symbols:
            continue
        selected.append(
            {
                "target_key": f"ad_hoc_{symbol.lower()}",
                "entity_type": "stock",
                "entity_id": symbol,
                "company_name": symbol,
                "market": "US",
                "sec_symbol": symbol,
                "ir_url": "",
                "include_keywords": [],
                "exclude_keywords": [],
                "max_links": args.max_materials,
                "status": "ad_hoc",
                "enabled": True,
                "notes": "ad hoc SEC target",
            }
        )
    if selected:
        return selected
    return [row for row in registry_rows if row.get("enabled") and row.get("sec_symbol")]


def summarize_submissions(company_name, sec_symbol, cik, filings):
    lines = [
        f"{company_name}（{sec_symbol}）SEC 官方申报列表快照。",
        "",
        f"本地实体：{sec_symbol}",
        f"CIK：{cik}",
        f"最近命中表单数：{len(filings)}",
        "",
        "最近表单：",
    ]
    for filing in filings[:12]:
        lines.append(
            "- {date} | {form} | accession={accession} | primary={primary}".format(
                date=filing.get("filingDate") or "-",
                form=filing.get("form") or "-",
                accession=filing.get("accessionNumber") or "-",
                primary=filing.get("primaryDocument") or "-",
            )
        )
    return "\n".join(lines)


def persist_submissions_snapshot(target, sec_meta, payload, filings, fetched_at):
    raw_bytes = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    stable_key = f"{target['sec_symbol']}_submissions"
    filing_date = (filings[0].get("filingDate") if filings else "") or fetched_at[:10]
    return persist_external_snapshot(
        title=f"{target['company_name']} SEC submissions snapshot",
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind="sec_submissions_json",
        source_url=f"https://data.sec.gov/submissions/CIK{int(sec_meta['cik']):010d}.json",
        source_domain="data.sec.gov",
        content_type="application/json; charset=utf-8",
        raw_bytes=raw_bytes,
        raw_extension=".json",
        note=f"official SEC submissions feed for {target['company_name']}",
        tags=["official_primary", "sec", "submissions"],
        body_text=summarize_submissions(target["company_name"], target["sec_symbol"], sec_meta["cik"], filings),
        metadata={
            "official_symbol": target["sec_symbol"],
            "company_name": target["company_name"],
            "cik": sec_meta["cik"],
            "exchange": sec_meta.get("exchange"),
            "latest_filing_date": filings[0].get("filingDate") if filings else None,
            "filing_count": len(filings),
        },
        extra_frontmatter={
            "provider": "sec",
            "announcement_id": stable_key,
            "official_symbol": target["sec_symbol"],
            "company_name": target["company_name"],
            "cik": sec_meta["cik"],
            "published_at": filing_date,
        },
        stable_key=stable_key,
        bucket_date=filing_date,
    )


def material_source_kind(reason):
    return "sec_filing_document" if reason == "primary_document" else "sec_earnings_material"


def material_title(target, filing, item, extracted_title):
    if extracted_title and extracted_title.strip() and extracted_title.strip() != item["name"]:
        return extracted_title.strip()
    return "{company} {form} {date} {name}".format(
        company=target["company_name"],
        form=filing.get("form") or "SEC",
        date=filing.get("filingDate") or "",
        name=item["name"],
    ).strip()


def material_body_text(target, filing, item, extracted_body):
    summary = "{company} {form} {date} 官方 SEC 材料。".format(
        company=target["company_name"],
        form=filing.get("form") or "SEC",
        date=filing.get("filingDate") or "",
    ).strip()
    lines = [
        summary,
        "",
        f"本地实体：{target['entity_id']}",
        f"SEC代码：{target['sec_symbol']}",
        f"表单类型：{filing.get('form') or '-'}",
        f"申报日期：{filing.get('filingDate') or '-'}",
        f"accession：{filing.get('accessionNumber') or '-'}",
        f"主文件：{filing.get('primaryDocument') or '-'}",
        f"当前材料：{item['name']}",
        f"材料判断：{item.get('reason') or '-'}",
        "",
        extracted_body or "(empty)",
    ]
    return "\n".join(lines)


def persist_material_snapshot(target, sec_meta, filing, item, response, extracted, fetched_at):
    filing_date = filing.get("filingDate") or fetched_at[:10]
    accession_number = filing.get("accessionNumber") or "unknown_accession"
    title = material_title(target, filing, item, extracted.get("title"))
    stable_key = f"{accession_number}_{item['name']}"
    return persist_external_snapshot(
        title=title,
        fetched_at=fetched_at,
        entity_type=target["entity_type"],
        entity_id=target["entity_id"],
        source_kind=material_source_kind(item.get("reason")),
        source_url=response["final_url"],
        source_domain=response_domain(response),
        content_type=response["content_type"] or "application/octet-stream",
        raw_bytes=response["bytes"],
        raw_extension=response_extension(response),
        note=f"official SEC filing material for {target['company_name']}",
        tags=[
            "official_primary",
            "sec",
            str(filing.get("form") or "").lower(),
            str(item.get("reason") or "").lower(),
        ],
        body_text=material_body_text(target, filing, item, extracted.get("body_text")),
        metadata={
            "company_name": target["company_name"],
            "official_symbol": target["sec_symbol"],
            "cik": sec_meta["cik"],
            "exchange": sec_meta.get("exchange"),
            "form_type": filing.get("form"),
            "filing_date": filing.get("filingDate"),
            "report_date": filing.get("reportDate"),
            "acceptance_datetime": filing.get("acceptanceDateTime"),
            "accession_number": accession_number,
            "primary_document": filing.get("primaryDocument"),
            "primary_doc_description": filing.get("primaryDocDescription"),
            "material_name": item["name"],
            "material_reason": item.get("reason"),
            "material_score": item.get("score"),
            "index_url": sec_index_url(sec_meta["cik"], accession_number),
            "published_at": extracted.get("published_at") or filing.get("filingDate"),
            "text_kind": extracted.get("text_kind"),
        },
        extra_frontmatter={
            "provider": "sec",
            "announcement_id": stable_key,
            "official_symbol": target["sec_symbol"],
            "company_name": target["company_name"],
            "cik": sec_meta["cik"],
            "form_type": filing.get("form"),
            "accession_number": accession_number,
            "material_name": item["name"],
            "published_at": extracted.get("published_at") or filing.get("filingDate"),
            "notice_date": filing.get("filingDate"),
        },
        stable_key=stable_key,
        bucket_date=filing_date,
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch official SEC filing materials into SMR raw storage")
    parser.add_argument("--target-key", action="append", help="Target key from official_intel_target_registry.md")
    parser.add_argument("--entity-id", action="append", help="Local entity id from official_intel_target_registry.md")
    parser.add_argument("--symbol", action="append", help="Additional SEC ticker symbol; can be repeated")
    parser.add_argument("--form", action="append", default=list(DEFAULT_FORMS), help="SEC form type; can be repeated")
    parser.add_argument("--days-back", type=int, default=240, help="Only keep filings within the last N days")
    parser.add_argument("--max-filings", type=int, default=6, help="Maximum filings to inspect per target")
    parser.add_argument("--max-materials", type=int, default=4, help="Maximum material documents to fetch per filing")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--user-agent", default=DEFAULT_SEC_USER_AGENT)
    parser.add_argument("--include-disabled", action="store_true", help="Allow disabled target rows from registry")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    targets = resolve_targets(args)

    outputs = []
    target_summaries = []
    failures = []

    for target in targets:
        sec_symbol = str(target.get("sec_symbol") or "").strip().upper()
        if not sec_symbol:
            failures.append({"entity_id": target.get("entity_id"), "error": "missing_sec_symbol"})
            continue
        sec_meta = sec_company_lookup(sec_symbol, timeout=args.timeout, user_agent=args.user_agent)
        if not sec_meta:
            failures.append({"entity_id": target.get("entity_id"), "sec_symbol": sec_symbol, "error": "sec_symbol_not_found"})
            continue

        try:
            submissions_payload, _submissions_response = fetch_sec_submissions(
                sec_meta["cik"],
                timeout=args.timeout,
                user_agent=args.user_agent,
            )
        except Exception as exc:
            failures.append({"entity_id": target.get("entity_id"), "sec_symbol": sec_symbol, "error": str(exc)})
            continue

        filings = filter_sec_filings(
            list_recent_sec_filings(submissions_payload),
            forms=args.form,
            days_back=args.days_back,
            limit=args.max_filings,
        )
        submissions_snapshot = persist_submissions_snapshot(target, sec_meta, submissions_payload, filings, fetched_at)

        material_count = 0
        for filing in filings:
            accession_number = filing.get("accessionNumber")
            if not accession_number:
                continue
            try:
                index_payload, _index_response = fetch_sec_index(
                    sec_meta["cik"],
                    accession_number,
                    timeout=args.timeout,
                    user_agent=args.user_agent,
                )
            except Exception as exc:
                failures.append(
                    {
                        "entity_id": target.get("entity_id"),
                        "sec_symbol": sec_symbol,
                        "accession_number": accession_number,
                        "error": f"index_fetch_failed: {exc}",
                    }
                )
                continue

            materials = select_sec_material_entries(
                index_payload,
                primary_document=filing.get("primaryDocument"),
                max_entries=args.max_materials,
            )
            for item in materials:
                document_url = sec_document_url(sec_meta["cik"], accession_number, item["name"])
                try:
                    response = fetch_url(
                        document_url,
                        timeout=args.timeout,
                        user_agent=args.user_agent,
                        accept="text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,text/plain;q=0.8,*/*;q=0.7",
                    )
                except Exception as exc:
                    failures.append(
                        {
                            "entity_id": target.get("entity_id"),
                            "sec_symbol": sec_symbol,
                            "accession_number": accession_number,
                            "material_name": item["name"],
                            "error": f"document_fetch_failed: {exc}",
                        }
                    )
                    continue

                extracted = extract_text_payload(
                    response,
                    title_hint="{company} {form} {date} {name}".format(
                        company=target["company_name"],
                        form=filing.get("form") or "SEC",
                        date=filing.get("filingDate") or "",
                        name=item["name"],
                    ).strip(),
                )
                snapshot = persist_material_snapshot(target, sec_meta, filing, item, response, extracted, fetched_at)
                outputs.append(
                    {
                        "target_key": target["target_key"],
                        "entity_id": target["entity_id"],
                        "sec_symbol": sec_symbol,
                        "form_type": filing.get("form"),
                        "filing_date": filing.get("filingDate"),
                        "accession_number": accession_number,
                        "material_name": item["name"],
                        "material_reason": item.get("reason"),
                        **snapshot,
                    }
                )
                material_count += 1

        target_summaries.append(
            {
                "target_key": target["target_key"],
                "entity_id": target["entity_id"],
                "sec_symbol": sec_symbol,
                "cik": sec_meta["cik"],
                "submission_snapshot": submissions_snapshot,
                "filing_count": len(filings),
                "material_count": material_count,
            }
        )

    entry = register_snapshot(
        conn,
        entity_type="sec_official_fetch",
        entity_id=f"sec_official__{fetched_at[:10]}",
        status="fetched",
        source="fetch_sec_official_materials.py",
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
        "fetch_sec_official_materials.py",
        "success",
        "official SEC materials fetched",
        {
            "target_count": len(targets),
            "material_count": len(outputs),
            "registry_entry_id": entry["id"],
            "failures": failures,
        },
    )
    print(f"SEC official targets: {len(targets)}")
    print(f"Fetched SEC materials: {len(outputs)}")
    if failures:
        print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
