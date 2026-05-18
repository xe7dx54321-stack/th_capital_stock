#!/usr/bin/env python3
"""Shared helpers for SMR input-source registry and normalized market events."""

import hashlib
import re
from datetime import datetime, timedelta

from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_wiki import dumps_json, extract_frontmatter, loads_json, now_ts, read_markdown, slugify

SOURCE_REGISTRY_PATH = project_path("00_control", "source_registry.md")
RAW_EXTERNAL_DIR = project_path("11_smr_wiki", "raw", "external")
EVENT_OUTPUT_DIR = project_path("01_data", "events")


def ordered_unique(values):
    seen = set()
    rows = []
    for value in values or []:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        rows.append(item)
    return rows


def normalize_csv_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return ordered_unique(value.split(","))
    return ordered_unique(value)


def parse_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "enabled", "active"}


def parse_int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def parse_markdown_table(lines):
    table_lines = []
    in_table = False
    for raw_line in lines or []:
        stripped = raw_line.strip()
        if stripped.startswith("|"):
            table_lines.append(stripped)
            in_table = True
            continue
        if in_table:
            break

    if len(table_lines) < 2:
        return []

    headers = [part.strip() for part in table_lines[0].strip("|").split("|")]
    rows = []
    for raw_line in table_lines[2:]:
        if raw_line.startswith("|-"):
            continue
        parts = [part.strip() for part in raw_line.strip("|").split("|")]
        if len(parts) != len(headers):
            continue
        row = {header: part for header, part in zip(headers, parts)}
        if any(value for value in row.values()):
            rows.append(row)
    return rows


def section_lines(path_value):
    path = normalize_project_path(path_value)
    if path is None or not path.exists():
        return {}
    sections = {}
    current = None
    buffer = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = buffer
            current = line[3:].strip()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = buffer
    return sections


def parse_source_registry(path_value=SOURCE_REGISTRY_PATH):
    sections = section_lines(path_value)
    rows = []
    for row in parse_markdown_table(sections.get("Sources", [])):
        source_key = str(row.get("Source Key") or "").strip()
        if not source_key:
            continue
        rows.append(
            {
                "source_key": source_key,
                "name": str(row.get("Name") or "").strip(),
                "layer": str(row.get("Layer") or "").strip(),
                "provider": str(row.get("Provider") or "").strip(),
                "source_class": str(row.get("Source Class") or "").strip(),
                "entity_scope": normalize_csv_list(row.get("Entity Scope")),
                "markets": [item.upper() for item in normalize_csv_list(row.get("Markets"))],
                "cadence": str(row.get("Cadence") or "").strip(),
                "freshness_sla_hours": parse_int(row.get("Freshness SLA Hours"), default=0) or 0,
                "status": str(row.get("Status") or "").strip() or "planned",
                "enabled": parse_bool(row.get("Enabled")),
                "cost_level": str(row.get("Cost") or "").strip() or "unknown",
                "confidence_level": str(row.get("Confidence") or "").strip() or "unknown",
                "owner_profile_id": str(row.get("Owner Profile") or "").strip(),
                "notes": str(row.get("Notes") or "").strip(),
            }
        )
    return rows


def ensure_input_source_registry_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS input_source_registry (
            source_key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            layer TEXT NOT NULL,
            provider TEXT NOT NULL,
            source_class TEXT NOT NULL,
            entity_scope_json TEXT NOT NULL DEFAULT '[]',
            markets_json TEXT NOT NULL DEFAULT '[]',
            cadence TEXT NOT NULL,
            freshness_sla_hours INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            cost_level TEXT NOT NULL DEFAULT 'unknown',
            confidence_level TEXT NOT NULL DEFAULT 'unknown',
            owner_profile_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_input_source_registry_layer_status
        ON input_source_registry(layer, status, enabled);
        """
    )


def ensure_market_event_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS market_event (
            event_id TEXT PRIMARY KEY,
            source_key TEXT NOT NULL,
            source_id TEXT,
            event_family TEXT NOT NULL,
            event_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT,
            publish_time TEXT,
            market_effective_time TEXT,
            importance TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'active',
            source_path TEXT,
            source_rel_path TEXT,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_market_event_source_type
        ON market_event(source_id, event_type);

        CREATE INDEX IF NOT EXISTS idx_market_event_entity
        ON market_event(entity_type, entity_id, event_date DESC, event_type);

        CREATE INDEX IF NOT EXISTS idx_market_event_family_date
        ON market_event(event_family, event_date DESC, importance);
        """
    )
    try:
        conn.execute(
            """
            CREATE VIEW market_event_latest AS
            WITH ranked AS (
                SELECT
                    event_id,
                    source_key,
                    source_id,
                    event_family,
                    event_type,
                    entity_type,
                    entity_id,
                    title,
                    event_date,
                    publish_time,
                    market_effective_time,
                    importance,
                    status,
                    source_path,
                    source_rel_path,
                    payload_json,
                    created_at,
                    updated_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY entity_type, entity_id, event_type
                        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, updated_at DESC, event_id DESC
                    ) AS rn
                FROM market_event
            )
            SELECT
                event_id,
                source_key,
                source_id,
                event_family,
                event_type,
                entity_type,
                entity_id,
                title,
                event_date,
                publish_time,
                market_effective_time,
                importance,
                status,
                source_path,
                source_rel_path,
                payload_json,
                created_at,
                updated_at
            FROM ranked
            WHERE rn = 1
            """
        )
    except Exception as exc:
        if "already exists" not in str(exc):
            raise


def upsert_input_source_registry(conn, rows):
    ensure_input_source_registry_table(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            "SELECT created_at FROM input_source_registry WHERE source_key=?",
            (row["source_key"],),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        conn.execute(
            """
            INSERT INTO input_source_registry (
                source_key,
                name,
                layer,
                provider,
                source_class,
                entity_scope_json,
                markets_json,
                cadence,
                freshness_sla_hours,
                status,
                enabled,
                cost_level,
                confidence_level,
                owner_profile_id,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_key) DO UPDATE SET
                name=excluded.name,
                layer=excluded.layer,
                provider=excluded.provider,
                source_class=excluded.source_class,
                entity_scope_json=excluded.entity_scope_json,
                markets_json=excluded.markets_json,
                cadence=excluded.cadence,
                freshness_sla_hours=excluded.freshness_sla_hours,
                status=excluded.status,
                enabled=excluded.enabled,
                cost_level=excluded.cost_level,
                confidence_level=excluded.confidence_level,
                owner_profile_id=excluded.owner_profile_id,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (
                row["source_key"],
                row["name"],
                row["layer"],
                row["provider"],
                row["source_class"],
                dumps_json(row["entity_scope"]),
                dumps_json(row["markets"]),
                row["cadence"],
                row["freshness_sla_hours"],
                row["status"],
                1 if row["enabled"] else 0,
                row["cost_level"],
                row["confidence_level"],
                row["owner_profile_id"],
                row["notes"],
                created_at,
                timestamp,
            ),
        )


def normalize_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) >= 10:
        return text[:10]
    try:
        return datetime.fromisoformat(text).strftime("%Y-%m-%d")
    except ValueError:
        return None


def normalize_ts(value):
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 10:
        return f"{text} 00:00:00"
    return text


def heuristic_market_effective_time(publish_time):
    timestamp = normalize_ts(publish_time)
    if not timestamp:
        return None
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp
    if dt.hour >= 15:
        dt = dt + timedelta(days=1)
    return dt.strftime("%Y-%m-%d 09:00:00")


def classification_text(title, metadata, text):
    return " ".join(
        [
            str(title or ""),
            str(metadata.get("source_kind") or ""),
            str(metadata.get("provider") or ""),
            str(metadata.get("tags") or ""),
            str(metadata.get("公告分类") or ""),
            str(metadata.get("form_type") or ""),
            str(metadata.get("company_name") or ""),
            str(metadata.get("material_name") or ""),
            str(metadata.get("mean_consensus") or ""),
            text or "",
        ]
    ).lower()


def detect_source_key(metadata):
    provider = slugify(metadata.get("provider") or metadata.get("source_domain") or "")
    source_kind = slugify(metadata.get("source_kind") or "")
    if source_kind == "sec_submissions_json":
        return "sec_submissions_json"
    if source_kind == "sec_filing_document":
        return "sec_filing_document"
    if source_kind == "sec_earnings_material":
        return "sec_earnings_material"
    if source_kind == "ir_landing_page":
        return "official_ir_page_discovery"
    if source_kind in {"ir_material_page", "ir_material_pdf"}:
        return "official_ir_material"
    if source_kind == "announcement" and provider == "cninfo":
        return "cninfo_announcement"
    if source_kind == "announcement" and provider == "hkexnews":
        return "hkex_announcement"
    if source_kind == "news_search":
        return "eastmoney_news_search"
    if source_kind == "news_article":
        return "eastmoney_news_article"
    if source_kind == "research_article":
        return "eastmoney_report_article"
    if source_kind == "research_pdf_text":
        return "eastmoney_report_pdf_text"
    if source_kind == "research_structured":
        return "eastmoney_report_structured"
    if source_kind == "research_table_structured":
        return "eastmoney_report_table_structured"
    if source_kind == "public_analyst_signal" and provider == "marketscreener":
        return "public_analyst_signal_marketscreener"
    if source_kind == "public_transcript" and provider == "fool":
        return "public_transcript_fool"
    if source_kind == "research":
        return "eastmoney_report_search"
    return f"{provider}_{source_kind}".strip("_") or "unknown_source"


def classify_market_event(title, metadata, text):
    source_kind = slugify(metadata.get("source_kind") or "")
    content = classification_text(title, metadata, text)
    form_type = str(metadata.get("form_type") or "").strip().upper()
    if source_kind == "announcement":
        if "board meeting" in content or "董事会" in content:
            return "announcement", "board_meeting_notice", "high"
        if "annual results" in content or "年度业绩" in content or "年度报告" in content:
            return "announcement", "annual_results_announcement", "high"
        if "interim results" in content or "中期业绩" in content or "半年报" in content:
            return "announcement", "interim_results_announcement", "high"
        if "quarterly report" in content or "季度报告" in content or "一季度" in content or "三季度" in content:
            return "announcement", "quarterly_report", "high"
        if any(
            keyword in content
            for keyword in ("投资者关系活动记录", "投资者关系活动记录表", "投资者关系管理信息", "调研纪要", "调研活动", "机构调研")
        ):
            return "announcement", "investor_relations_activity", "high"
        if any(
            keyword in content
            for keyword in ("业绩说明会", "业绩会", "电话会议", "电话会", "conference call", "earnings call", "webcast")
        ):
            return "announcement", "earnings_call_material", "high"
        if "annual results announcement" in content or ("for the year ended" in content and "results" in content):
            return "announcement", "annual_results_announcement", "high"
        if "interim results announcement" in content or ("interim" in content and "results" in content):
            return "announcement", "interim_results_announcement", "high"
        if "quarterly results" in content or "quarter results" in content or ("quarter" in content and "results" in content):
            return "announcement", "earnings_release", "high"
        if "业绩预告" in content or "profit warning" in content or "earnings warning" in content:
            return "announcement", "earnings_preannouncement", "high"
        if "dividend" in content or "分红" in content or "派息" in content:
            return "announcement", "dividend_notice", "high"
        if "monthly return" in content or "月报表" in content:
            return "announcement", "monthly_return", "low"
        if "movements in securities" in content or "股本" in content or "股份变动" in content:
            return "announcement", "equity_movement", "medium"
        return "announcement", "announcement_general", "medium"
    if source_kind == "research_table_structured":
        return "research", "analyst_report_table", "medium"
    if source_kind in {"research_structured", "research_pdf_text"}:
        return "research", "analyst_report_structured", "medium"
    if source_kind in {"research", "research_article"}:
        return "research", "analyst_report", "medium"
    if source_kind == "public_analyst_signal":
        return "research", "analyst_signal_summary", "medium"
    if source_kind == "public_transcript":
        return "announcement", "earnings_call_material", "medium"
    if source_kind == "sec_filing_document":
        if form_type in {"10-K", "20-F"}:
            return "announcement", "annual_results_announcement", "high"
        if form_type in {"10-Q"}:
            return "announcement", "quarterly_report", "high"
        if form_type in {"8-K", "6-K"} and any(
            keyword in content for keyword in ("earnings", "results", "webcast", "conference call", "prepared remarks")
        ):
            return "announcement", "earnings_release", "high"
        return "announcement", "announcement_general", "medium"
    if source_kind == "sec_earnings_material":
        if any(keyword in content for keyword in ("transcript", "prepared remarks", "conference call", "webcast")):
            return "announcement", "earnings_call_material", "high"
        if any(keyword in content for keyword in ("presentation", "slides", "deck")):
            return "announcement", "investor_presentation", "medium"
        return "announcement", "earnings_release", "high"
    if source_kind in {"ir_material_page", "ir_material_pdf"}:
        if any(keyword in content for keyword in ("transcript", "prepared remarks", "conference call", "webcast")):
            return "announcement", "earnings_call_material", "high"
        if any(keyword in content for keyword in ("presentation", "slides", "deck")):
            return "announcement", "investor_presentation", "medium"
        if any(keyword in content for keyword in ("annual report", "interim report", "results", "financial report")):
            return "announcement", "announcement_general", "medium"
        return "announcement", "announcement_general", "low"
    if source_kind == "news_article":
        return "news", "news_article", "medium"
    if source_kind == "news_search":
        return "news", "news_digest_item", "low"
    return "news", "news_article", "low"


def is_summary_noise(stripped):
    if not stripped:
        return True
    if stripped.startswith(
        (
            "证券代码",
            "证券简称",
            "本地名称",
            "本地实体",
            "官方简称",
            "原始文件",
            "官方入口",
            "材料链接",
            "链接文字",
            "SEC代码",
            "公告标题",
            "公告日期",
            "公告类型",
            "披露板块",
            "source_url:",
            "generated_at:",
            "batch_date:",
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
            "createElement(",
            "Trace Id:",
            "polyfill",
            "function(",
            "'fetch' in window",
            "'assign' in Object",
            "Skip to main content",
            "All Microsoft Global",
            "heading-bg-color",
            "row-bg-color",
            "isModernBrowser",
            "scriptElement",
            "polyfillScriptElement",
            "parentNode",
            "if (",
            "var ",
            ".css",
            ".js",
        )
    ):
        return True
    if stripped in {");", "}", "};"}:
        return True
    if stripped.count("{") + stripped.count("}") >= 2:
        return True
    return False


def summarize_event_text(text, title=None):
    lines = []
    in_extracted = False
    for raw_line in str(text or "").splitlines():
        stripped = raw_line.strip()
        if stripped == "## Extracted Text":
            in_extracted = True
            continue
        if not in_extracted:
            continue
        if stripped.startswith("## "):
            break
        if is_summary_noise(stripped):
            continue
        lines.append(stripped)
        if len(lines) >= 3:
            break
    summary = " / ".join(lines[:3])
    if summary:
        compact = summary.replace(" / ", "").strip()
        if any(
            token in summary
            for token in (
                "window",
                "Object",
                "document",
                "propertyToken",
                "visitorJsHash",
                "expJsHash",
                '"exp":',
                '"target":',
            )
        ):
            return str(title or "").strip()
        if re.fullmatch(r"(?:[A-Za-z]\s*){3,}", compact):
            return str(title or "").strip()
        return summary
    return str(title or "").strip()


def stable_event_id(source_rel_path, event_type):
    digest = hashlib.sha1(f"{source_rel_path}|{event_type}".encode("utf-8")).hexdigest()[:20]
    return f"event_{digest}"


def load_source_manifest_lookup(conn):
    rows = conn.execute(
        """
        SELECT source_id, source_rel_path
        FROM source_manifest
        """
    ).fetchall()
    return {row[1]: row[0] for row in rows}


def event_rows_from_raw_external(source_lookup, days_back=None, limit=None, families=None):
    rows = []
    cutoff = None
    if days_back is not None:
        cutoff = datetime.now().date() - timedelta(days=days_back)
    for path in sorted(RAW_EXTERNAL_DIR.rglob("*.md"), reverse=True):
        text = read_markdown(path)
        metadata = extract_frontmatter(text)
        source_kind = slugify(metadata.get("source_kind") or "")
        if source_kind not in {
            "announcement",
            "news_article",
            "news_search",
            "research",
            "research_article",
            "research_pdf_text",
            "research_structured",
            "research_table_structured",
            "public_analyst_signal",
            "sec_filing_document",
            "sec_earnings_material",
            "ir_material_page",
            "ir_material_pdf",
        }:
            continue
        title = metadata.get("title") or path.stem
        event_family, event_type, importance = classify_market_event(title, metadata, text)
        if families and event_family not in families:
            continue
        event_date = normalize_date(
            metadata.get("event_date")
            or metadata.get("notice_date")
            or metadata.get("published_at")
            or metadata.get("fetched_at")
        )
        if cutoff and event_date:
            try:
                if datetime.strptime(event_date, "%Y-%m-%d").date() < cutoff:
                    continue
            except ValueError:
                pass
        source_path = str(path.resolve())
        source_rel_path = relative_to_project(path)
        publish_time = normalize_ts(metadata.get("published_at") or metadata.get("notice_date") or metadata.get("fetched_at"))
        rows.append(
            {
                "event_id": stable_event_id(source_rel_path, event_type),
                "source_key": detect_source_key(metadata),
                "source_id": source_lookup.get(source_rel_path),
                "event_family": event_family,
                "event_type": event_type,
                "entity_type": metadata.get("entity_type") or "external_source",
                "entity_id": metadata.get("entity_id") or path.stem,
                "title": title,
                "event_date": event_date,
                "publish_time": publish_time,
                "market_effective_time": heuristic_market_effective_time(publish_time),
                "importance": importance,
                "status": "active",
                "source_path": source_path,
                "source_rel_path": source_rel_path,
                "payload_json": dumps_json(
                    {
                        "provider": metadata.get("provider"),
                        "source_kind": metadata.get("source_kind"),
                        "source_url": metadata.get("source_url"),
                        "source_domain": metadata.get("source_domain"),
                        "content_type": metadata.get("content_type"),
                        "published_at": metadata.get("published_at"),
                        "notice_date": metadata.get("notice_date"),
                        "tags": normalize_csv_list(metadata.get("tags")),
                        "summary": summarize_event_text(text, title=title),
                    }
                ),
            }
        )
        if limit and len(rows) >= limit:
            break
    return rows


def upsert_market_events(conn, rows):
    ensure_market_event_table(conn)
    timestamp = now_ts()
    for row in rows:
        existing = conn.execute(
            "SELECT created_at FROM market_event WHERE event_id=?",
            (row["event_id"],),
        ).fetchone()
        created_at = existing[0] if existing else timestamp
        if row.get("source_id") and row.get("event_type"):
            existing_source_event = conn.execute(
                """
                SELECT event_id, created_at
                FROM market_event
                WHERE source_id=? AND event_type=?
                LIMIT 1
                """,
                (row["source_id"], row["event_type"]),
            ).fetchone()
            if existing_source_event and existing_source_event[0] != row["event_id"]:
                created_at = existing_source_event[1] or created_at
                conn.execute("DELETE FROM market_event WHERE event_id=?", (existing_source_event[0],))
        conn.execute(
            """
            INSERT INTO market_event (
                event_id,
                source_key,
                source_id,
                event_family,
                event_type,
                entity_type,
                entity_id,
                title,
                event_date,
                publish_time,
                market_effective_time,
                importance,
                status,
                source_path,
                source_rel_path,
                payload_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                source_key=excluded.source_key,
                source_id=excluded.source_id,
                event_family=excluded.event_family,
                event_type=excluded.event_type,
                entity_type=excluded.entity_type,
                entity_id=excluded.entity_id,
                title=excluded.title,
                event_date=excluded.event_date,
                publish_time=excluded.publish_time,
                market_effective_time=excluded.market_effective_time,
                importance=excluded.importance,
                status=excluded.status,
                source_path=excluded.source_path,
                source_rel_path=excluded.source_rel_path,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                row["event_id"],
                row["source_key"],
                row["source_id"],
                row["event_family"],
                row["event_type"],
                row["entity_type"],
                row["entity_id"],
                row["title"],
                row["event_date"],
                row["publish_time"],
                row["market_effective_time"],
                row["importance"],
                row["status"],
                row["source_path"],
                row["source_rel_path"],
                row["payload_json"],
                created_at,
                timestamp,
            ),
        )


def delete_stale_market_events(conn, rows):
    source_rel_paths = ordered_unique(row.get("source_rel_path") for row in rows if row.get("source_rel_path"))
    keep_event_ids = ordered_unique(row.get("event_id") for row in rows if row.get("event_id"))
    if not source_rel_paths or not keep_event_ids:
        return 0
    path_placeholders = ",".join("?" for _ in source_rel_paths)
    keep_placeholders = ",".join("?" for _ in keep_event_ids)
    params = tuple(source_rel_paths) + tuple(keep_event_ids)
    stale_count = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM market_event
        WHERE source_rel_path IN ({path_placeholders})
          AND event_id NOT IN ({keep_placeholders})
        """,
        params,
    ).fetchone()[0]
    if stale_count:
        conn.execute(
            f"""
            DELETE FROM market_event
            WHERE source_rel_path IN ({path_placeholders})
              AND event_id NOT IN ({keep_placeholders})
            """,
            params,
        )
    return stale_count


def count_by_key(rows, key):
    counts = {}
    for row in rows:
        value = row.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts
