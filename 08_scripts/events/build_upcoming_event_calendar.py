#!/usr/bin/env python3
"""Extract upcoming catalyst calendar items from existing official materials."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_events import (
    EVENT_OUTPUT_DIR,
    RAW_EXTERNAL_DIR,
    detect_source_key,
    ensure_market_event_table,
    heuristic_market_effective_time,
    load_source_manifest_lookup,
    normalize_ts,
    upsert_market_events,
)
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_universe import load_active_equity_universe
from smr_wiki import dumps_json, extract_frontmatter, now_ts, read_markdown

DB_PATH = project_path("01_data", "db", "smr.db")

ELIGIBLE_SOURCE_KINDS = {
    "ir_material_page",
    "ir_material_pdf",
    "ir_landing_page",
    "sec_earnings_material",
    "sec_filing_document",
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

DATE_RE = (
    r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*,?\s+)?"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),\s*(\d{4})"
)


def normalize_text(text: str) -> str:
    return (
        str(text or "")
        .replace("\xa0", " ")
        .replace("\u202f", " ")
        .replace("\u2009", " ")
        .replace("\u200b", " ")
    )


def english_date_to_iso(month_name: str, day: str, year: str) -> str | None:
    month = MONTHS.get(str(month_name or "").strip().lower())
    if month is None:
        return None
    try:
        return date(int(year), int(month), int(day)).strftime("%Y-%m-%d")
    except ValueError:
        return None


def extract_text_body(text: str) -> str:
    marker = "## Extracted Text"
    if marker not in text:
        return normalize_text(text)
    _, tail = text.split(marker, 1)
    next_heading = re.search(r"\n##\s+", tail)
    body = tail[: next_heading.start()] if next_heading else tail
    return normalize_text(body)


def is_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith(
        (
            "本地实体：",
            "官方入口：",
            "材料链接：",
            "链接文字：",
            "Source:",
            "Source：",
        )
    ):
        return True
    if stripped.endswith(("官方 IR 材料。", "官方 SEC 材料。", "官方 IR 入口页快照。")):
        return True
    if any(
        token in stripped
        for token in (
            "window.",
            "document.",
            "function(",
            "ga(",
            "polyfill",
            "propertyToken",
            "visitorJsHash",
            "expJsHash",
            "createElement(",
            "parentNode",
            "scriptElement",
            ".css",
            ".js",
            "{",
            "}",
        )
    ):
        has_date = re.search(DATE_RE, stripped) is not None
        has_keyword = any(
            keyword in stripped.lower()
            for keyword in (
                "conference call",
                "webcast",
                "financial results",
                "annual meeting",
                "dividend",
                "payable on",
                "will report",
                "will present at",
                "will participate",
            )
        )
        if not has_date and not has_keyword:
            return True
    return False


def clean_body_lines(body: str) -> list[str]:
    rows = []
    for raw_line in body.splitlines():
        line = re.sub(r"\s+", " ", normalize_text(raw_line)).strip()
        if is_noise_line(line):
            continue
        rows.append(line)
    return rows


def parse_ice_page_props(text: str) -> dict:
    match = re.search(r"window\.__ICE_PAGE_PROPS__=(\{.*?\});", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def stable_event_id(entity_id: str, event_type: str, calendar_kind: str, event_date: str, title: str) -> str:
    payload = "|".join([entity_id or "-", event_type or "-", calendar_kind or "-", event_date or "-", title or "-"])
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:20]
    return f"event_{digest}"


def find_event_time_text(text: str) -> str | None:
    patterns = [
        r"(after the market close)",
        r"(before the market open)",
        r"(at \d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|AM|PM)\s*(?:[A-Z]{1,4}(?:\s*/\s*\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|AM|PM)\s*[A-Z]{1,4})?)?)",
        r"(\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|AM|PM)\s*(?:Pacific|Eastern|Central|Mountain)\s+Time)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" .,")
    return None


def summarize_calendar_candidate(candidate: dict) -> str:
    date_text = candidate.get("event_date") or "-"
    calendar_kind = candidate.get("calendar_kind") or "calendar_event"
    kind_text = {
        "earnings_release": "业绩披露",
        "earnings_call": "业绩电话会",
        "conference_presentation": "管理层公开路演",
        "annual_meeting": "股东会",
        "dividend_payable": "分红到账",
    }.get(calendar_kind, calendar_kind)
    if candidate.get("record_date"):
        return f"接下来最近的 {kind_text} 时间点是 {date_text}，对应登记日为 {candidate.get('record_date')}。"
    if candidate.get("event_time_text"):
        return f"接下来最近的 {kind_text} 时间点是 {date_text}，时间提示为 {candidate.get('event_time_text')}。"
    return f"接下来最近的 {kind_text} 时间点是 {date_text}。"


def date_match_iter(text: str):
    return list(re.finditer(DATE_RE, normalize_text(text), re.I))


def first_future_date(text: str, today: date) -> tuple[str | None, str | None]:
    for match in date_match_iter(text):
        event_date = english_date_to_iso(match.group(1), match.group(2), match.group(3))
        if not event_date:
            continue
        if datetime.strptime(event_date, "%Y-%m-%d").date() < today:
            continue
        return event_date, match.group(0)
    return None, None


def extract_earnings_from_quarterly_data(metadata: dict, text: str, today: date) -> dict | None:
    if str(metadata.get("source_kind") or "").strip() != "ir_landing_page":
        return None
    page_props = parse_ice_page_props(text)
    quarterly_items = page_props.get("QuarterlyData") or []
    candidates = []
    for item in quarterly_items:
        event_date = None
        if item.get("eventDateLocal"):
            match = re.search(DATE_RE, normalize_text(str(item.get("eventDateLocal"))), re.I)
            if match:
                event_date = english_date_to_iso(match.group(1), match.group(2), match.group(3))
        elif item.get("eventDate"):
            try:
                event_date = datetime.fromtimestamp(int(item["eventDate"]) / 1000).strftime("%Y-%m-%d")
            except (TypeError, ValueError, OSError):
                event_date = None
        if not event_date:
            continue
        if datetime.strptime(event_date, "%Y-%m-%d").date() < today:
            continue
        title = item.get("documentTitleWithNL") or item.get("documentTitle") or metadata.get("title")
        webcast_url = ((item.get("urls") or {}).get("webcastUrl")) or None
        candidates.append(
            {
                "event_type": "earnings_calendar_item",
                "calendar_kind": "earnings_release",
                "event_date": event_date,
                "title": str(title or metadata.get("title") or "Upcoming quarterly results").strip(),
                "importance": "high",
                "event_time_text": "官方 IR 入口页已列出该业绩节点",
                "summary": f"官方 IR 入口页显示接下来最近一次业绩节点是 {event_date} 的 {title}。",
                "confidence": 0.98,
                "source_payload": {
                    "document_id": item.get("documentId"),
                    "document_publish_time_local": item.get("documentPublishTimeLocal"),
                    "webcast_url": webcast_url,
                    "presentation_url": ((item.get("urls") or {}).get("presentationUrl")) or None,
                    "transcript_url": ((item.get("urls") or {}).get("transcriptUrl")) or None,
                },
            }
        )
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.get("event_date"), item.get("title") or ""))[0]


def extract_earnings_candidate(
    metadata: dict, title: str, source_text: str, clean_text: str, clean_lines: list[str], today: date
) -> dict | None:
    from_landing = extract_earnings_from_quarterly_data(metadata, source_text, today)
    if from_landing:
        return from_landing

    patterns = [
        (
            re.compile(rf"will report .*? on (?P<date>{DATE_RE})(?P<tail>[^.]*\.)", re.I),
            "earnings_release",
            0.96,
        ),
        (
            re.compile(rf"conference call on (?P<date>{DATE_RE})(?P<tail>[^.]*\.)", re.I),
            "earnings_call",
            0.92,
        ),
        (
            re.compile(rf"earnings conference call[\s:]+(?P<date>{DATE_RE})(?P<tail>[^\\n.]*)", re.I),
            "earnings_call",
            0.9,
        ),
    ]
    for pattern, calendar_kind, confidence in patterns:
        match = pattern.search(clean_text)
        if not match:
            continue
        event_date = english_date_to_iso(match.group(2), match.group(3), match.group(4))
        if not event_date:
            continue
        if datetime.strptime(event_date, "%Y-%m-%d").date() < today:
            continue
        tail = normalize_text(match.groupdict().get("tail") or "").strip()
        event_time_text = find_event_time_text(tail) or find_event_time_text(match.group(0))
        return {
            "event_type": "earnings_calendar_item",
            "calendar_kind": calendar_kind,
            "event_date": event_date,
            "title": title,
            "importance": "high",
            "event_time_text": event_time_text,
            "summary": summarize_calendar_candidate(
                {
                    "event_date": event_date,
                    "calendar_kind": calendar_kind,
                    "event_time_text": event_time_text,
                }
            ),
            "confidence": confidence,
            "source_payload": {
                "matched_text": re.sub(r"\s+", " ", match.group(0)).strip(),
            },
        }

    multiline = re.search(rf"earnings conference call.*?(?P<date>{DATE_RE})", source_text, re.I | re.S)
    if multiline:
        event_date = english_date_to_iso(multiline.group(2), multiline.group(3), multiline.group(4))
        if event_date and datetime.strptime(event_date, "%Y-%m-%d").date() >= today:
            event_time_text = find_event_time_text(multiline.group(0))
            return {
                "event_type": "earnings_calendar_item",
                "calendar_kind": "earnings_call",
                "event_date": event_date,
                "title": title,
                "importance": "high",
                "event_time_text": event_time_text,
                "summary": summarize_calendar_candidate(
                    {
                        "event_date": event_date,
                        "calendar_kind": "earnings_call",
                        "event_time_text": event_time_text,
                    }
                ),
                "confidence": 0.86,
                "source_payload": {
                    "matched_text": re.sub(r"\s+", " ", multiline.group(0))[:320].strip(),
                },
            }

    joined_lines = " ".join(clean_lines[:40])
    if "earnings conference call" in joined_lines.lower():
        event_date, matched = first_future_date(joined_lines, today)
        if event_date:
            event_time_text = find_event_time_text(joined_lines)
            return {
                "event_type": "earnings_calendar_item",
                "calendar_kind": "earnings_call",
                "event_date": event_date,
                "title": title,
                "importance": "high",
                "event_time_text": event_time_text,
                "summary": summarize_calendar_candidate(
                    {
                        "event_date": event_date,
                        "calendar_kind": "earnings_call",
                        "event_time_text": event_time_text,
                    }
                ),
                "confidence": 0.82,
                "source_payload": {
                    "matched_text": matched,
                },
            }
    return None


def extract_dividend_candidate(title: str, clean_text: str, today: date) -> dict | None:
    match = re.search(
        rf"dividend .*? payable on (?P<payable>{DATE_RE}) to .*? record as of (?P<record>{DATE_RE})",
        clean_text,
        re.I,
    )
    if not match:
        match = re.search(
            rf"quarterly dividend .*? payable on (?P<payable>{DATE_RE}) to stockholders of record as of (?P<record>{DATE_RE})",
            clean_text,
            re.I,
        )
    if not match:
        return None
    payable_date = english_date_to_iso(match.group(2), match.group(3), match.group(4))
    record_date = english_date_to_iso(match.group(6), match.group(7), match.group(8))
    if not payable_date:
        return None
    if datetime.strptime(payable_date, "%Y-%m-%d").date() < today:
        return None
    return {
        "event_type": "corp_action_calendar_item",
        "calendar_kind": "dividend_payable",
        "event_date": payable_date,
        "title": title,
        "importance": "high",
        "record_date": record_date,
        "summary": summarize_calendar_candidate(
            {
                "event_date": payable_date,
                "calendar_kind": "dividend_payable",
                "record_date": record_date,
            }
        ),
        "confidence": 0.97,
        "source_payload": {
            "matched_text": re.sub(r"\s+", " ", match.group(0)).strip(),
        },
    }


def extract_conference_candidate(title: str, clean_text: str, today: date) -> dict | None:
    patterns = [
        re.compile(rf"will present at .*? on (?P<date>{DATE_RE})(?P<tail>[^.]*\.)", re.I),
        re.compile(rf"will participate in .*? on (?P<date>{DATE_RE})(?P<tail>[^.]*\.)", re.I),
    ]
    for pattern in patterns:
        match = pattern.search(clean_text)
        if not match:
            continue
        event_date = english_date_to_iso(match.group(2), match.group(3), match.group(4))
        if not event_date:
            continue
        if datetime.strptime(event_date, "%Y-%m-%d").date() < today:
            continue
        event_time_text = find_event_time_text(match.groupdict().get("tail") or "")
        return {
            "event_type": "corp_action_calendar_item",
            "calendar_kind": "conference_presentation",
            "event_date": event_date,
            "title": title,
            "importance": "medium",
            "event_time_text": event_time_text,
            "summary": summarize_calendar_candidate(
                {
                    "event_date": event_date,
                    "calendar_kind": "conference_presentation",
                    "event_time_text": event_time_text,
                }
            ),
            "confidence": 0.9,
            "source_payload": {
                "matched_text": re.sub(r"\s+", " ", match.group(0)).strip(),
            },
        }
    return None


def extract_annual_meeting_candidate(title: str, clean_text: str, clean_lines: list[str], today: date) -> dict | None:
    inline = re.search(rf"annual meeting(?: of stockholders| of shareholders)? .*? on (?P<date>{DATE_RE})", clean_text, re.I)
    if inline:
        event_date = english_date_to_iso(inline.group(2), inline.group(3), inline.group(4))
        if event_date and datetime.strptime(event_date, "%Y-%m-%d").date() >= today:
            return {
                "event_type": "corp_action_calendar_item",
                "calendar_kind": "annual_meeting",
                "event_date": event_date,
                "title": title,
                "importance": "high",
                "summary": summarize_calendar_candidate(
                    {
                        "event_date": event_date,
                        "calendar_kind": "annual_meeting",
                    }
                ),
                "confidence": 0.9,
                "source_payload": {
                    "matched_text": re.sub(r"\s+", " ", inline.group(0)).strip(),
                },
            }
    for index, line in enumerate(clean_lines):
        if "annual meeting" not in line.lower():
            continue
        probe = " ".join(clean_lines[index : index + 3])
        event_date, matched = first_future_date(probe, today)
        if not event_date:
            continue
        return {
            "event_type": "corp_action_calendar_item",
            "calendar_kind": "annual_meeting",
            "event_date": event_date,
            "title": title,
            "importance": "high",
            "summary": summarize_calendar_candidate(
                {
                    "event_date": event_date,
                    "calendar_kind": "annual_meeting",
                }
            ),
            "confidence": 0.78,
            "source_payload": {
                "matched_text": matched,
            },
        }
    return None


def build_calendar_row(path: Path, metadata: dict, source_lookup: dict, candidate: dict) -> dict:
    source_rel_path = relative_to_project(path)
    publish_time = normalize_ts(metadata.get("published_at") or metadata.get("notice_date") or metadata.get("fetched_at"))
    event_date = candidate.get("event_date")
    market_effective_time = f"{event_date} 09:00:00" if event_date else heuristic_market_effective_time(publish_time)
    calendar_kind = candidate.get("calendar_kind") or "calendar_event"
    title = str(candidate.get("title") or metadata.get("title") or path.stem).strip()
    return {
        "event_id": stable_event_id(metadata.get("entity_id") or path.stem, candidate.get("event_type"), calendar_kind, event_date, title),
        "source_key": detect_source_key(metadata),
        "source_id": source_lookup.get(source_rel_path),
        "event_family": "calendar",
        "event_type": candidate.get("event_type"),
        "entity_type": metadata.get("entity_type") or "stock",
        "entity_id": metadata.get("entity_id") or path.stem,
        "title": title,
        "event_date": event_date,
        "publish_time": publish_time,
        "market_effective_time": market_effective_time,
        "importance": candidate.get("importance") or "medium",
        "status": "active",
        "source_path": str(path.resolve()),
        "source_rel_path": source_rel_path,
        "payload_json": dumps_json(
            {
                "provider": metadata.get("provider"),
                "source_kind": metadata.get("source_kind"),
                "source_url": metadata.get("source_url"),
                "source_domain": metadata.get("source_domain"),
                "published_at": metadata.get("published_at"),
                "calendar_kind": calendar_kind,
                "event_time_text": candidate.get("event_time_text"),
                "record_date": candidate.get("record_date"),
                "summary": candidate.get("summary"),
                "extraction_confidence": candidate.get("confidence"),
                **(candidate.get("source_payload") or {}),
            }
        ),
    }


def collect_rows(universe: dict, source_lookup: dict, days_forward: int) -> tuple[list[dict], list[str]]:
    today = datetime.now().date()
    cutoff_date = today + timedelta(days=days_forward)
    rows = []
    processed_paths = []
    seen_keys = set()
    for path in sorted((RAW_EXTERNAL_DIR / "stock").rglob("*.md")):
        text = read_markdown(path)
        if not text:
            continue
        metadata = extract_frontmatter(text)
        source_kind = str(metadata.get("source_kind") or "").strip()
        entity_id = str(metadata.get("entity_id") or "").strip()
        if source_kind not in ELIGIBLE_SOURCE_KINDS:
            continue
        if entity_id not in universe:
            continue
        processed_paths.append(relative_to_project(path))
        title = str(metadata.get("title") or path.stem).strip()
        body = extract_text_body(text)
        clean_lines = clean_body_lines(body)
        clean_text = "\n".join(clean_lines)
        if not clean_text:
            continue

        for candidate in (
            extract_earnings_candidate(metadata, title, body, clean_text, clean_lines, today),
            extract_dividend_candidate(title, clean_text, today),
            extract_conference_candidate(title, clean_text, today),
            extract_annual_meeting_candidate(title, clean_text, clean_lines, today),
        ):
            if not candidate:
                continue
            event_date = candidate.get("event_date")
            if not event_date:
                continue
            event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
            if event_dt < today or event_dt > cutoff_date:
                continue
            dedupe_key = (
                entity_id,
                candidate.get("event_type"),
                candidate.get("calendar_kind"),
                candidate.get("event_date"),
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            rows.append(build_calendar_row(path, metadata, source_lookup, candidate))
    rows.sort(key=lambda item: (item.get("event_date") or "9999-12-31", item.get("entity_id") or "", item.get("title") or ""))
    return rows, processed_paths


def delete_stale_calendar_events(conn, processed_paths: list[str], keep_event_ids: list[str]) -> int:
    processed = sorted({path for path in processed_paths if path})
    keep_ids = sorted({event_id for event_id in keep_event_ids if event_id})
    if not processed:
        return 0
    path_placeholders = ",".join("?" for _ in processed)
    params = [*processed]
    query = f"""
        SELECT COUNT(*)
        FROM market_event
        WHERE event_family='calendar'
          AND source_rel_path IN ({path_placeholders})
    """
    delete_query = f"""
        DELETE FROM market_event
        WHERE event_family='calendar'
          AND source_rel_path IN ({path_placeholders})
    """
    if keep_ids:
        keep_placeholders = ",".join("?" for _ in keep_ids)
        query += f" AND event_id NOT IN ({keep_placeholders})"
        delete_query += f" AND event_id NOT IN ({keep_placeholders})"
        params.extend(keep_ids)
    stale_count = conn.execute(query, params).fetchone()[0]
    if stale_count:
        conn.execute(delete_query, params)
    return stale_count


def write_summary(path: Path, created_at: str, rows: list[dict], stale_deleted_count: int, days_forward: int) -> None:
    lines = [
        "# SMR 未来催化日历抽取",
        "",
        f"- created_at: {created_at}",
        f"- days_forward: {days_forward}",
        f"- upcoming_event_count: {len(rows)}",
        f"- stale_deleted_count: {stale_deleted_count}",
        "",
        "| Event Date | Entity | Type | Importance | Title | Summary |",
        "|------------|--------|------|------------|-------|---------|",
    ]
    for row in rows:
        payload = json.loads(row["payload_json"])
        lines.append(
            "| {event_date} | {entity_id} | {event_type} | {importance} | {title} | {summary} |".format(
                event_date=row.get("event_date") or "-",
                entity_id=row.get("entity_id") or "-",
                event_type=payload.get("calendar_kind") or row.get("event_type") or "-",
                importance=row.get("importance") or "-",
                title=str(row.get("title") or "-").replace("|", "/"),
                summary=str(payload.get("summary") or "-").replace("|", "/"),
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract upcoming catalyst calendar items from existing official materials")
    parser.add_argument("--days-forward", type=int, default=90, help="Only keep upcoming events within today+N days")
    args = parser.parse_args()

    created_at = now_ts()
    snapshot_date = created_at[:10]

    conn = sqlite3.connect(DB_PATH)
    ensure_market_event_table(conn)
    universe = load_active_equity_universe(conn, include_seed=True)
    source_lookup = load_source_manifest_lookup(conn)
    rows, processed_paths = collect_rows(universe, source_lookup, args.days_forward)
    upsert_market_events(conn, rows)
    stale_deleted_count = delete_stale_calendar_events(conn, processed_paths, [row.get("event_id") for row in rows])

    EVENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVENT_OUTPUT_DIR / f"{snapshot_date}_upcoming_event_calendar.md"
    write_summary(output_path, created_at, rows, stale_deleted_count, args.days_forward)
    entry = register_snapshot(
        conn,
        entity_type="upcoming_event_calendar_snapshot",
        entity_id=snapshot_date,
        status="compiled",
        source="build_upcoming_event_calendar.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload={
            "upcoming_event_count": len(rows),
            "stale_deleted_count": stale_deleted_count,
            "days_forward": args.days_forward,
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "build_upcoming_event_calendar.py",
        "success",
        "upcoming catalyst calendar extracted",
        {
            "entity_id": snapshot_date,
            "upcoming_event_count": len(rows),
            "stale_deleted_count": stale_deleted_count,
            "days_forward": args.days_forward,
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Upcoming event calendar extracted: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Upcoming event count: {len(rows)}")


if __name__ == "__main__":
    main()
