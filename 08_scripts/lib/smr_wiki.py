#!/usr/bin/env python3
"""Shared helpers for SMR Wiki source manifests and ingest drafts."""

import json
import re
from datetime import datetime

from smr_paths import normalize_project_path, project_path, relative_to_project

REVIEW_REASON_CODES = {
    "needs_human_judgement",
    "duplicate_source",
    "duplicate_thesis",
    "insufficient_evidence",
    "conflicts_with_latest_research",
    "outdated_conclusion",
    "format_incomplete",
    "source_not_reliable",
}

CATEGORY_PAGE_TYPE = {
    "sectors": "sector",
    "stocks": "stock",
    "theses": "thesis",
    "strategies": "strategy",
    "playbooks": "playbook",
    "risk_cases": "risk_case",
    "decisions": "decision",
    "timelines": "timeline",
}

SINGLETON_CATEGORIES = {
    "sectors",
    "stocks",
    "theses",
    "strategies",
    "playbooks",
}


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dumps_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def loads_json(value, fallback):
    if value in (None, ""):
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def ensure_source_manifest_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_manifest (
            source_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            title TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_rel_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            upstream_refs TEXT NOT NULL DEFAULT '[]',
            tags TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_source_manifest_rel_path
        ON source_manifest(source_rel_path);

        CREATE INDEX IF NOT EXISTS idx_source_manifest_type_entity
        ON source_manifest(source_type, entity_type, entity_id);
        """
    )


def ensure_ingest_draft_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS smr_wiki_ingest_draft (
            draft_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            draft_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            candidate_category TEXT NOT NULL,
            candidate_tags TEXT NOT NULL DEFAULT '[]',
            governance_status TEXT NOT NULL,
            approval_status TEXT NOT NULL,
            review_reason_code TEXT,
            review_reason TEXT,
            source_path TEXT NOT NULL,
            source_rel_path TEXT NOT NULL,
            draft_payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_smr_wiki_ingest_draft_source
        ON smr_wiki_ingest_draft(source_id);

        CREATE INDEX IF NOT EXISTS idx_smr_wiki_ingest_draft_status
        ON smr_wiki_ingest_draft(governance_status, approval_status);
        """
    )


def ensure_knowledge_index_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS smr_wiki_knowledge_index (
            knowledge_id TEXT PRIMARY KEY,
            page_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            title TEXT NOT NULL,
            page_path TEXT NOT NULL,
            page_rel_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            source_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_smr_wiki_knowledge_rel_path
        ON smr_wiki_knowledge_index(page_rel_path);

        CREATE INDEX IF NOT EXISTS idx_smr_wiki_knowledge_entity
        ON smr_wiki_knowledge_index(page_type, entity_type, entity_id, status);
        """
    )


def ensure_import_execution_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS smr_wiki_import_execution (
            execution_id TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            knowledge_id TEXT,
            target_rel_path TEXT,
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_smr_wiki_import_execution_draft
        ON smr_wiki_import_execution(draft_id, created_at);

        CREATE INDEX IF NOT EXISTS idx_smr_wiki_import_execution_source
        ON smr_wiki_import_execution(source_id, created_at);
        """
    )


def ensure_review_queue_execution_table(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS smr_wiki_review_queue_execution (
            execution_id TEXT PRIMARY KEY,
            queue_mode TEXT NOT NULL,
            filters_json TEXT NOT NULL DEFAULT '{}',
            item_count INTEGER NOT NULL DEFAULT 0,
            counts_by_status_json TEXT NOT NULL DEFAULT '{}',
            export_rel_path TEXT,
            created_at TEXT NOT NULL
        );
        """
    )


def slugify(value):
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower())
    return text.strip("_") or "item"


def entity_slug(entity_id):
    return slugify(str(entity_id).replace(".", "_"))


def normalize_tags(tags, limit=12, max_length=40):
    result = []
    seen = set()
    for raw_tag in tags:
        if raw_tag in (None, ""):
            continue
        tag = re.sub(r"[^a-zA-Z0-9]+", "_", str(raw_tag).strip().lower()).strip("_")
        if not tag:
            continue
        tag = tag[:max_length]
        if tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
        if len(result) >= limit:
            break
    return result


def read_markdown(path_value):
    path = normalize_project_path(path_value)
    if path is None or not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def extract_frontmatter(text):
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    metadata = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return metadata
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return {}


def extract_title(text, fallback=""):
    metadata = extract_frontmatter(text)
    if metadata.get("title"):
        return metadata["title"]

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def extract_section_text(text, headings):
    lines = text.splitlines()
    wanted = {heading.strip().lower() for heading in headings}

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        heading_text = re.sub(r"^#+\s*", "", stripped).strip().lower()
        if heading_text not in wanted:
            continue

        collected = []
        for next_line in lines[index + 1:]:
            if next_line.strip().startswith("#"):
                break
            collected.append(next_line)
        cleaned = cleanup_summary("\n".join(collected))
        if cleaned:
            return cleaned
    return ""


def extract_first_paragraph(text):
    body_lines = []
    in_frontmatter = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" and not body_lines:
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            if body_lines:
                break
            continue
        body_lines.append(stripped.lstrip("- ").strip())

    return cleanup_summary(" ".join(body_lines))


def cleanup_summary(text, max_length=240):
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    cleaned = cleaned.strip("-").strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "…"


def markdown_timestamp(path_value):
    path = normalize_project_path(path_value)
    if path is None or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def normalized_source_path(path_value):
    path = normalize_project_path(path_value)
    if path is None:
        return None, None
    return str(path), relative_to_project(path)


def page_type_for_category(category):
    return CATEGORY_PAGE_TYPE.get(category, slugify(category))


def knowledge_id_for(category, entity_id, source_id=None):
    if category in SINGLETON_CATEGORIES:
        return f"{category}__{entity_slug(entity_id)}"
    return f"{category}__{slugify(source_id or entity_id)}"


def wiki_rel_path_for(category, entity_id, source_id=None):
    if category in SINGLETON_CATEGORIES:
        file_name = f"{entity_slug(entity_id)}.md"
    else:
        file_name = f"{slugify(source_id or entity_id)}.md"
    return str(project_path("11_smr_wiki", "wiki", category, file_name).relative_to(project_path()))


def wiki_abs_path_for(category, entity_id, source_id=None):
    rel_path = wiki_rel_path_for(category, entity_id, source_id=source_id)
    return project_path(*rel_path.split("/"))


def imported_source_exists(conn, source_id):
    row = conn.execute(
        """
        SELECT 1
        FROM smr_wiki_import_execution
        WHERE source_id=? AND status='imported'
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    return bool(row)


def active_knowledge_entry(conn, knowledge_id):
    row = conn.execute(
        """
        SELECT
            knowledge_id,
            page_type,
            entity_type,
            entity_id,
            title,
            page_path,
            page_rel_path,
            status,
            source_id,
            source_type,
            imported_at,
            updated_at,
            metadata_json
        FROM smr_wiki_knowledge_index
        WHERE knowledge_id=? AND status='active'
        LIMIT 1
        """,
        (knowledge_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "knowledge_id": row[0],
        "page_type": row[1],
        "entity_type": row[2],
        "entity_id": row[3],
        "title": row[4],
        "page_path": row[5],
        "page_rel_path": row[6],
        "status": row[7],
        "source_id": row[8],
        "source_type": row[9],
        "imported_at": row[10],
        "updated_at": row[11],
        "metadata_json": row[12],
    }


def generate_execution_id(prefix):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def validate_review_reason_code(reason_code):
    if reason_code in (None, ""):
        return None
    normalized = slugify(reason_code)
    if normalized not in REVIEW_REASON_CODES:
        raise ValueError(f"Invalid review reason code: {reason_code}")
    return normalized


def draft_registry_status(governance_status, approval_status, review_reason_code=None):
    if approval_status == "rejected":
        return "rejected"
    if approval_status == "reopened":
        return "reopened"
    if governance_status == "blocked" and review_reason_code:
        return review_reason_code
    if governance_status == "ready":
        return "ready"
    if governance_status:
        return governance_status
    return approval_status or "unknown"
