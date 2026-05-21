#!/usr/bin/env python3
"""Execute source-fetch plans for investment hard-evidence gap tasks."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "run_investment_evidence_gap_fetch.py"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = project_path("02_research", "investment_evidence_gap_fetches")

CUSTOMER_CAPEX_OFFICIAL_TARGET_KEYS = [
    "microsoft_primary",
    "alphabet_primary",
    "amazon_primary",
    "meta_primary",
]
CUSTOMER_CAPEX_TRANSCRIPT_KEYS = ["msft_fool", "googl_fool", "amzn_fool", "meta_fool"]
COMPETITION_OFFICIAL_TARGET_KEYS = ["lumentum_primary", "marvell_primary", "broadcom_primary"]
COMPETITION_TRANSCRIPT_KEYS = ["mrvl_fool", "avgo_fool"]

LOCAL_SOURCE_KIND_PRIORITY = {
    "sec_earnings_material": 0,
    "sec_filing_document": 1,
    "announcement": 2,
    "cninfo_announcement": 2,
    "official_ir_material": 3,
    "ir_material_pdf": 4,
    "public_transcript": 5,
    "research_pdf_text": 6,
    "research_article": 7,
    "research_table_structured": 8,
    "research_structured": 9,
    "research_search": 10,
    "news_article": 11,
    "stock_research": 12,
    "recommendation_card": 13,
}

LOCAL_SOURCE_STRENGTH_BY_KIND = {
    "sec_earnings_material": "hard",
    "sec_filing_document": "hard",
    "announcement": "hard",
    "cninfo_announcement": "hard",
    "official_ir_material": "hard",
    "ir_material_pdf": "hard",
    "public_transcript": "strong_supporting",
    "research_pdf_text": "soft_supporting",
    "research_article": "soft_supporting",
    "research_table_structured": "soft_supporting",
    "research_structured": "soft_supporting",
    "research_search": "soft_supporting",
    "news_article": "soft_supporting",
    "stock_research": "internal_context",
    "recommendation_card": "internal_context",
}

LOCAL_VARIABLE_SOURCE_RULES = {
    "order_delivery_visibility": {
        "label": "订单/交付可见度",
        "entity_roles": ["add"],
        "source_kinds": [
            "announcement",
            "cninfo_announcement",
            "research_pdf_text",
            "research_article",
            "research_table_structured",
            "research_structured",
            "stock_research",
        ],
        "keywords": ["800G", "1.6T", "订单", "出货", "交付", "客户", "产能", "需求", "在手", "投资者关系"],
        "max_sources": 14,
    },
    "1_6t_timing_window": {
        "label": "1.6T 时间窗口",
        "entity_roles": ["add"],
        "source_kinds": [
            "announcement",
            "cninfo_announcement",
            "research_pdf_text",
            "research_article",
            "research_table_structured",
            "research_structured",
            "stock_research",
        ],
        "keywords": ["1.6T", "800G", "放量", "量产", "客户", "订单", "交付", "产品", "高端"],
        "max_sources": 12,
    },
    "gross_margin_elasticity": {
        "label": "毛利率/利润率弹性",
        "entity_roles": ["add"],
        "source_kinds": [
            "announcement",
            "cninfo_announcement",
            "research_pdf_text",
            "research_article",
            "research_table_structured",
            "research_structured",
            "stock_research",
        ],
        "keywords": ["毛利", "毛利率", "利润率", "净利率", "ROE", "ROIC", "良率", "ASP", "费用率", "产品结构", "高端产品"],
        "max_sources": 14,
    },
    "competitive_landscape": {
        "label": "竞争格局",
        "entity_roles": ["add", "peers"],
        "source_kinds": [
            "announcement",
            "cninfo_announcement",
            "sec_earnings_material",
            "sec_filing_document",
            "official_ir_material",
            "ir_material_pdf",
            "public_transcript",
            "research_pdf_text",
            "research_article",
            "research_structured",
            "news_article",
            "stock_research",
        ],
        "keywords": [
            "竞争",
            "份额",
            "降价",
            "价格",
            "供应商",
            "供应链",
            "800G",
            "1.6T",
            "Coherent",
            "Lumentum",
            "Marvell",
            "Broadcom",
            "competitive",
            "competition",
            "market share",
            "pricing",
            "supplier",
        ],
        "max_sources": 18,
    },
    "alibaba_fundamental_recheck": {
        "label": "阿里巴巴调出复核",
        "entity_roles": ["remove"],
        "source_kinds": [
            "sec_earnings_material",
            "sec_filing_document",
            "official_ir_material",
            "ir_material_pdf",
            "public_transcript",
            "announcement",
        ],
        "keywords": [
            "Alibaba Cloud",
            "Cloud Intelligence",
            "AI",
            "capex",
            "capital expenditure",
            "cloud revenue",
            "customer management",
            "Taobao",
            "Tmall",
            "云智能",
            "阿里云",
            "资本开支",
            "电商",
            "客户管理",
            "淘天",
        ],
        "max_sources": 16,
    },
    "google_capex_mapping": {
        "label": "GOOGL CapEx 映射",
        "entity_ids": ["GOOGL"],
        "source_kinds": ["sec_earnings_material", "sec_filing_document", "official_ir_material", "public_transcript"],
        "keywords": [
            "capex",
            "capital expenditures",
            "AI infrastructure",
            "data center",
            "datacenter",
            "Cloud",
            "GCP",
            "TPU",
            "compute",
        ],
        "max_sources": 12,
    },
    "customer_capex": {
        "label": "云厂商资本开支",
        "entity_ids": ["MSFT", "GOOGL", "AMZN", "META"],
        "source_kinds": ["sec_earnings_material", "sec_filing_document", "official_ir_material", "public_transcript"],
        "keywords": ["capex", "capital expenditures", "AI infrastructure", "data center", "datacenter", "compute", "capacity"],
        "max_sources": 16,
    },
    "cloud_capex": {
        "label": "云厂商资本开支",
        "entity_ids": ["MSFT", "GOOGL", "AMZN", "META"],
        "source_kinds": ["sec_earnings_material", "sec_filing_document", "official_ir_material", "public_transcript"],
        "keywords": ["capex", "capital expenditures", "AI infrastructure", "data center", "datacenter", "compute", "capacity"],
        "max_sources": 16,
    },
}

PEER_ENTITY_IDS = ["LITE", "MRVL", "AVGO", "COHR"]


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("_") or "unknown"


def date_from_entity(entity_id: str | None) -> str:
    text = str(entity_id or "")
    if "__" in text:
        prefix = text.split("__", 1)[0]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", prefix):
            return prefix
    return datetime.now().strftime("%Y-%m-%d")


def latest_task_entries(conn: sqlite3.Connection, action_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE entity_type='investment_evidence_gap_task_snapshot'
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (max(limit * 4, limit),),
    ).fetchall()
    entries = []
    seen_actions: set[str] = set()
    for row in rows:
        payload = load_json(row["payload_json"], {})
        candidate_action_id = payload.get("action_id")
        if not candidate_action_id:
            continue
        if not (payload.get("tasks") or []):
            continue
        if action_id and candidate_action_id != action_id:
            continue
        if candidate_action_id in seen_actions:
            continue
        seen_actions.add(candidate_action_id)
        entries.append(
            {
                "id": row["id"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "status": row["status"],
                "source": row["source"],
                "relationships": load_json(row["relationships_json"], {}),
                "payload": payload,
                "snapshot_index": row["snapshot_index"],
                "created_at": row["created_at"],
                "action_id": candidate_action_id,
            }
        )
        if len(entries) >= limit:
            break
    return entries


def command_for_step(step: dict[str, Any]) -> list[str]:
    if step.get("internal"):
        return step.get("command") or ["internal", str(step.get("step_id") or "local_step")]
    script = step.get("script")
    args = step.get("args") or []
    return [sys.executable, str(PROJECT_ROOT / script), *[str(item) for item in args]]


def action_entity_map(action_id: str | None) -> dict[str, list[str]]:
    text = str(action_id or "")
    parts = text.split("__")
    add_code = parts[1] if len(parts) >= 2 else ""
    remove_code = parts[2] if len(parts) >= 3 else ""
    result: dict[str, list[str]] = {
        "add": [add_code] if add_code else [],
        "remove": [remove_code] if remove_code else [],
        "peers": list(PEER_ENTITY_IDS),
    }
    return result


def entity_ids_for_rule(rule: dict[str, Any], action_id: str | None) -> list[str]:
    explicit = [str(item).strip() for item in (rule.get("entity_ids") or []) if str(item).strip()]
    if explicit:
        return explicit
    action_map = action_entity_map(action_id)
    results: list[str] = []
    seen: set[str] = set()
    for role in rule.get("entity_roles") or []:
        for entity_id in action_map.get(role) or []:
            if entity_id and entity_id not in seen:
                seen.add(entity_id)
                results.append(entity_id)
    return results


def build_local_source_queries(action_id: str | None, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for task in tasks:
        variable_id = str(task.get("variable_id") or "").strip()
        rule = LOCAL_VARIABLE_SOURCE_RULES.get(variable_id)
        if not rule:
            continue
        entity_ids = entity_ids_for_rule(rule, action_id)
        if not entity_ids:
            continue
        key = (variable_id, tuple(entity_ids))
        if key in seen:
            continue
        seen.add(key)
        queries.append(
            {
                "variable_id": variable_id,
                "variable_label": task.get("variable_label") or rule.get("label") or variable_id,
                "priority": task.get("priority") or "P1",
                "research_question": task.get("research_question") or "",
                "entity_ids": entity_ids,
                "source_kinds": rule.get("source_kinds") or [],
                "keywords": rule.get("keywords") or [],
                "max_sources": rule.get("max_sources") or 12,
            }
        )
    return queries


def build_fetch_plan(entry: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    tasks = (entry.get("payload") or {}).get("tasks") or []
    variable_ids = {task.get("variable_id") for task in tasks}
    local_source_queries = build_local_source_queries(entry.get("action_id"), tasks)
    steps: list[dict[str, Any]] = []

    if local_source_queries:
        steps.append(
            {
                "step_id": "resolve_local_variable_sources",
                "label": "解析本地已入库材料并映射到补证变量",
                "source_priority": "source_manifest",
                "internal": True,
                "command": ["internal", "source_manifest_variable_resolution"],
                "expected_entity_type": "local_variable_source_resolution",
            }
        )

    if {"customer_capex", "cloud_capex"} & variable_ids:
        sec_args: list[str] = []
        for target_key in CUSTOMER_CAPEX_OFFICIAL_TARGET_KEYS:
            sec_args.extend(["--target-key", target_key])
        sec_args.extend(
            [
                "--days-back",
                str(args.days_back),
                "--max-filings",
                str(args.max_filings),
                "--max-materials",
                str(args.max_materials),
                "--timeout",
                str(args.timeout),
            ]
        )
        steps.append(
            {
                "step_id": "customer_capex_sec_official",
                "label": "抓取云厂商 SEC 官方财报/业绩材料",
                "source_priority": "official_customer_filings",
                "script": "08_scripts/wiki/fetch_sec_official_materials.py",
                "args": sec_args,
                "expected_entity_type": "sec_official_fetch",
            }
        )

        transcript_args: list[str] = []
        for target_key in CUSTOMER_CAPEX_TRANSCRIPT_KEYS:
            transcript_args.extend(["--target-key", target_key])
        transcript_args.extend(["--max-pages", str(args.max_transcript_pages), "--timeout", str(args.timeout)])
        steps.append(
            {
                "step_id": "customer_capex_public_transcripts",
                "label": "抓取云厂商公开电话会文字稿",
                "source_priority": "earnings_call_transcripts",
                "script": "08_scripts/wiki/fetch_public_transcripts_fool.py",
                "args": transcript_args,
                "expected_entity_type": "public_transcript_fetch",
            }
        )

    if "google_capex_mapping" in variable_ids:
        steps.append(
            {
                "step_id": "google_capex_sec_official",
                "label": "抓取/刷新 Alphabet SEC 官方材料",
                "source_priority": "official_customer_filings",
                "script": "08_scripts/wiki/fetch_sec_official_materials.py",
                "args": [
                    "--target-key",
                    "alphabet_primary",
                    "--days-back",
                    str(args.days_back),
                    "--max-filings",
                    str(args.max_filings),
                    "--max-materials",
                    str(args.max_materials),
                    "--timeout",
                    str(args.timeout),
                ],
                "expected_entity_type": "sec_official_fetch",
            }
        )
        steps.append(
            {
                "step_id": "google_capex_public_transcript",
                "label": "抓取/刷新 Alphabet 公开电话会文字稿",
                "source_priority": "earnings_call_transcripts",
                "script": "08_scripts/wiki/fetch_public_transcripts_fool.py",
                "args": ["--target-key", "googl_fool", "--max-pages", str(args.max_transcript_pages), "--timeout", str(args.timeout)],
                "expected_entity_type": "public_transcript_fetch",
            }
        )

    if "alibaba_fundamental_recheck" in variable_ids:
        steps.extend(
            [
                {
                    "step_id": "alibaba_sec_official",
                    "label": "抓取/刷新阿里巴巴 SEC 业绩材料",
                    "source_priority": "official_company_filings",
                    "script": "08_scripts/wiki/fetch_sec_official_materials.py",
                    "args": [
                        "--target-key",
                        "alibaba_primary",
                        "--days-back",
                        str(args.days_back),
                        "--max-filings",
                        str(args.max_filings),
                        "--max-materials",
                        str(args.max_materials),
                        "--timeout",
                        str(args.timeout),
                    ],
                    "expected_entity_type": "sec_official_fetch",
                },
                {
                    "step_id": "alibaba_ir_primary",
                    "label": "抓取/刷新阿里巴巴官方 IR 材料",
                    "source_priority": "official_company_ir",
                    "script": "08_scripts/wiki/fetch_ir_primary_materials.py",
                    "args": ["--target-key", "alibaba_primary", "--max-links", str(args.max_ir_links), "--timeout", str(args.timeout)],
                    "expected_entity_type": "official_ir_fetch",
                },
                {
                    "step_id": "alibaba_public_transcript",
                    "label": "抓取/刷新阿里巴巴公开电话会文字稿",
                    "source_priority": "earnings_call_transcripts",
                    "script": "08_scripts/wiki/fetch_public_transcripts_fool.py",
                    "args": ["--target-key", "baba_fool", "--max-pages", str(args.max_transcript_pages), "--timeout", str(args.timeout)],
                    "expected_entity_type": "public_transcript_fetch",
                },
            ]
        )

    if "competitive_landscape" in variable_ids:
        official_args: list[str] = []
        for target_key in COMPETITION_OFFICIAL_TARGET_KEYS:
            official_args.extend(["--target-key", target_key])
        official_args.extend(["--max-links", str(args.max_ir_links), "--timeout", str(args.timeout)])
        steps.append(
            {
                "step_id": "competition_peer_ir_primary",
                "label": "抓取/刷新光通信链海外对标公司 IR 材料",
                "source_priority": "competitor_official_ir",
                "script": "08_scripts/wiki/fetch_ir_primary_materials.py",
                "args": official_args,
                "expected_entity_type": "official_ir_fetch",
            }
        )
        transcript_args: list[str] = []
        for target_key in COMPETITION_TRANSCRIPT_KEYS:
            transcript_args.extend(["--target-key", target_key])
        transcript_args.extend(["--max-pages", str(args.max_transcript_pages), "--timeout", str(args.timeout)])
        steps.append(
            {
                "step_id": "competition_peer_transcripts",
                "label": "抓取/刷新光通信链海外对标公司电话会文字稿",
                "source_priority": "competitor_transcripts",
                "script": "08_scripts/wiki/fetch_public_transcripts_fool.py",
                "args": transcript_args,
                "expected_entity_type": "public_transcript_fetch",
            }
        )

    steps.extend(
        [
            {
                "step_id": "build_source_manifest",
                "label": "更新统一 source_manifest",
                "script": "08_scripts/wiki/build_source_manifest.py",
                "args": [],
                "expected_entity_type": "source_manifest",
            },
            {
                "step_id": "normalize_market_events",
                "label": "把原始外部来源归一成 market_event",
                "script": "08_scripts/events/normalize_market_events.py",
                "args": ["--days-back", str(args.days_back), "--family", "announcement"],
                "expected_entity_type": "market_event_snapshot",
            },
        ]
    )
    if getattr(args, "local_only", False):
        local_safe_scripts = {
            "08_scripts/wiki/build_source_manifest.py",
            "08_scripts/events/normalize_market_events.py",
        }
        steps = [step for step in steps if step.get("internal") or step.get("script") in local_safe_scripts]
    return {
        "action_id": entry["action_id"],
        "source_task_entry_id": entry["id"],
        "source_task_entity_id": entry["entity_id"],
        "tasks": tasks,
        "local_source_queries": local_source_queries,
        "steps": steps,
        "step_count": len(steps),
        "plan_status": "ready" if steps else "empty",
    }


def run_command(step: dict[str, Any], execute: bool) -> dict[str, Any]:
    command = command_for_step(step)
    if step.get("internal"):
        return {
            "step_id": step.get("step_id"),
            "label": step.get("label"),
            "status": "success" if execute else "planned",
            "command": command,
            "returncode": 0 if execute else None,
            "stdout_tail": ["local source manifest resolution handled in-process"] if execute else [],
            "stderr_tail": [],
        }
    if not execute:
        return {
            "step_id": step.get("step_id"),
            "label": step.get("label"),
            "status": "planned",
            "command": command,
            "returncode": None,
            "stdout_tail": [],
            "stderr_tail": [],
        }
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True)
    stdout_lines = (completed.stdout or "").splitlines()
    stderr_lines = (completed.stderr or "").splitlines()
    return {
        "step_id": step.get("step_id"),
        "label": step.get("label"),
        "status": "success" if completed.returncode == 0 else "failed",
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": stdout_lines[-12:],
        "stderr_tail": stderr_lines[-12:],
    }


def latest_entry_by_type(conn: sqlite3.Connection, entity_type: str, created_after: str | None = None) -> dict[str, Any] | None:
    filters = ["entity_type=?"]
    params: list[Any] = [entity_type]
    if created_after:
        filters.append("datetime(created_at) >= datetime(?)")
        params.append(created_after)
    row = conn.execute(
        f"""
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE {' AND '.join(filters)}
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "status": row["status"],
        "source": row["source"],
        "relationships": load_json(row["relationships_json"], {}),
        "payload": load_json(row["payload_json"], {}),
        "snapshot_index": row["snapshot_index"],
        "created_at": row["created_at"],
    }


def normalize_text(text: str | None) -> str:
    return " ".join(str(text or "").split())


def source_kind_rank(source_kind: str | None) -> int:
    return LOCAL_SOURCE_KIND_PRIORITY.get(str(source_kind or "").strip(), 99)


def source_strength(source_kind: str | None) -> str:
    return LOCAL_SOURCE_STRENGTH_BY_KIND.get(str(source_kind or "").strip(), "unknown")


def read_rel_text(rel_path: str, max_chars: int = 120_000) -> str:
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    return text[:max_chars]


def first_keyword_snippet(text: str, keywords: list[str], max_chars: int = 360) -> tuple[list[str], str]:
    if not text:
        return [], ""
    normalized = normalize_text(text)
    lower = normalized.lower()
    matches = []
    first_pos = None
    for keyword in keywords:
        token = str(keyword or "").strip()
        if not token:
            continue
        pos = lower.find(token.lower())
        if pos < 0:
            continue
        matches.append(token)
        first_pos = pos if first_pos is None else min(first_pos, pos)
    if first_pos is None:
        return [], ""
    start = max(0, first_pos - 120)
    snippet = normalized[start : start + max_chars]
    return matches[:8], snippet.strip()


def local_manifest_rows(conn: sqlite3.Connection, entity_id: str, limit: int = 120) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT source_type, title, source_rel_path, metadata_json, updated_at, created_at
        FROM source_manifest
        WHERE status='active'
          AND entity_id=?
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_rel_path ASC
        LIMIT ?
        """,
        (entity_id, limit),
    ).fetchall()
    results = []
    for row in rows:
        metadata = load_json(row["metadata_json"], {})
        source_kind = metadata.get("source_kind") or row["source_type"]
        results.append(
            {
                "source_type": row["source_type"],
                "source_kind": source_kind,
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "published_at": metadata.get("published_at") or metadata.get("notice_date") or row["updated_at"],
                "updated_at": row["updated_at"],
                "provider": metadata.get("provider") or "",
                "metadata": metadata,
            }
        )
    return results


def collect_local_evidence_outputs(conn: sqlite3.Connection, plan: dict[str, Any]) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    by_variable: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for query in plan.get("local_source_queries") or []:
        variable_outputs: list[dict[str, Any]] = []
        allowed_kinds = set(query.get("source_kinds") or [])
        keywords = [str(item) for item in (query.get("keywords") or []) if str(item).strip()]
        max_sources = int(query.get("max_sources") or 12)
        for entity_id in query.get("entity_ids") or []:
            for row in local_manifest_rows(conn, entity_id):
                source_kind = row.get("source_kind")
                if allowed_kinds and source_kind not in allowed_kinds and row.get("source_type") not in allowed_kinds:
                    continue
                rel_path = row.get("source_rel_path")
                if not rel_path:
                    continue
                source_text = read_rel_text(rel_path, max_chars=120_000)
                matched_keywords, snippet = first_keyword_snippet(
                    "\n".join([row.get("title") or "", source_text]),
                    keywords,
                )
                title_match_count = sum(
                    1 for keyword in keywords if str(keyword).lower() in str(row.get("title") or "").lower()
                )
                score = (10 if matched_keywords else 0) + title_match_count * 4 - source_kind_rank(source_kind)
                if not matched_keywords and source_kind_rank(source_kind) > 4:
                    continue
                candidate = {
                    "source_family": "local_source_manifest",
                    "variable_id": query.get("variable_id"),
                    "variable_label": query.get("variable_label"),
                    "priority": query.get("priority"),
                    "entity_id": entity_id,
                    "title": row.get("title"),
                    "source_rel_path": rel_path,
                    "published_at": row.get("published_at"),
                    "source_kind": source_kind,
                    "source_strength": source_strength(source_kind),
                    "matched_keywords": matched_keywords,
                    "snippet": snippet,
                    "_score": score,
                }
                variable_outputs.append(candidate)
        variable_outputs.sort(
            key=lambda item: (
                -int(item.get("_score") or 0),
                source_kind_rank(item.get("source_kind")),
                str(item.get("published_at") or ""),
            )
        )
        selected = []
        variable_seen: set[str] = set()
        for item in variable_outputs:
            rel_path = item.get("source_rel_path")
            if not rel_path or rel_path in variable_seen:
                continue
            variable_seen.add(rel_path)
            cleaned = {key: value for key, value in item.items() if key != "_score"}
            selected.append(cleaned)
            if rel_path not in seen_paths:
                seen_paths.add(rel_path)
                outputs.append(cleaned)
            if len(selected) >= max_sources:
                break
        by_variable.append(
            {
                "variable_id": query.get("variable_id"),
                "variable_label": query.get("variable_label"),
                "priority": query.get("priority"),
                "entity_ids": query.get("entity_ids") or [],
                "candidate_count": len(variable_outputs),
                "selected_count": len(selected),
                "outputs": selected,
            }
        )
    return {
        "outputs": outputs,
        "by_variable": by_variable,
        "source_paths": [item.get("source_rel_path") for item in outputs if item.get("source_rel_path")],
        "source_path_count": len([item for item in outputs if item.get("source_rel_path")]),
    }


def collect_fetch_outputs(
    conn: sqlite3.Connection,
    created_after: str | None = None,
    local_outputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sec_entry = latest_entry_by_type(conn, "sec_official_fetch", created_after=created_after) or {}
    ir_entry = latest_entry_by_type(conn, "official_ir_fetch", created_after=created_after) or {}
    transcript_entry = latest_entry_by_type(conn, "public_transcript_fetch", created_after=created_after) or {}
    source_manifest_entry = latest_entry_by_type(conn, "source_manifest", created_after=created_after) or {}
    market_event_entry = latest_entry_by_type(conn, "market_event_snapshot", created_after=created_after) or {}
    entries = {
        "sec_official_fetch": sec_entry,
        "official_ir_fetch": ir_entry,
        "public_transcript_fetch": transcript_entry,
        "source_manifest": source_manifest_entry,
        "market_event_snapshot": market_event_entry,
    }
    outputs = list((local_outputs or {}).get("outputs") or [])
    failures = []
    for entry in (sec_entry, ir_entry, transcript_entry):
        payload = entry.get("payload") or {}
        for item in payload.get("outputs") or []:
            if item.get("markdown_rel_path"):
                outputs.append(
                    {
                        "source_family": entry.get("entity_type"),
                        "entity_id": item.get("entity_id"),
                        "title": item.get("title"),
                        "source_rel_path": item.get("markdown_rel_path"),
                        "published_at": item.get("published_at") or item.get("filing_date"),
                        "source_kind": item.get("material_reason") or item.get("provider"),
                    }
                )
        failures.extend(payload.get("failures") or [])
    source_paths = []
    seen = set()
    for item in outputs:
        rel_path = item.get("source_rel_path")
        if rel_path and rel_path not in seen:
            seen.add(rel_path)
            source_paths.append(rel_path)
    return {
        "entries": {
            key: {
                "id": (value or {}).get("id"),
                "entity_id": (value or {}).get("entity_id"),
                "status": (value or {}).get("status"),
                "created_at": (value or {}).get("created_at"),
            }
            for key, value in entries.items()
        },
        "outputs": outputs,
        "local_resolution": {
            "by_variable": (local_outputs or {}).get("by_variable") or [],
            "source_path_count": (local_outputs or {}).get("source_path_count") or 0,
        },
        "failures": failures,
        "source_paths": source_paths,
        "source_path_count": len(source_paths),
    }


def md_cell(value: Any) -> str:
    if isinstance(value, list):
        text = "；".join(str(item) for item in value)
    else:
        text = str(value or "-")
    return text.replace("\n", " ").replace("|", " / ").strip()


def render_summary_markdown(result: dict[str, Any]) -> str:
    plan = result.get("plan") or {}
    outputs = result.get("fetch_outputs") or {}
    lines = [
        f"# 硬证据补证执行结果：{result.get('action_id')}",
        "",
        f"- generated_at: `{result.get('generated_at')}`",
        f"- mode: `{result.get('mode')}`",
        f"- task_snapshot_entry_id: `{plan.get('source_task_entry_id')}`",
        f"- source_path_count: `{outputs.get('source_path_count') or 0}`",
        f"- failure_count: `{len(outputs.get('failures') or [])}`",
        "",
        "## 执行计划",
        "",
        "| Step | 状态 | 命令摘要 |",
        "|---|---|---|",
    ]
    by_step = {item.get("step_id"): item for item in result.get("command_results") or []}
    for step in plan.get("steps") or []:
        command_result = by_step.get(step.get("step_id")) or {}
        command = " ".join(command_result.get("command") or command_for_step(step))
        lines.append(
            "| {label} | {status} | `{command}` |".format(
                label=md_cell(step.get("label")),
                status=md_cell(command_result.get("status") or "planned"),
                command=md_cell(command[:220]),
            )
        )

    local_resolution = outputs.get("local_resolution") or {}
    by_variable = local_resolution.get("by_variable") or []
    if by_variable:
        lines.extend(
            [
                "",
                "## 变量补证来源映射",
                "",
                "这部分来自本地 source_manifest 已入库材料解析，目的是把报告里的变量缺口映射到可读原文。它仍属于材料层，不等于研究结论。",
                "",
            ]
        )
        for variable in by_variable:
            lines.extend(
                [
                    f"### {variable.get('variable_label') or variable.get('variable_id')}",
                    "",
                    f"- variable_id: `{variable.get('variable_id')}`",
                    f"- priority: `{variable.get('priority')}`",
                    f"- entity_ids: `{', '.join(variable.get('entity_ids') or [])}`",
                    f"- candidate_count: `{variable.get('candidate_count') or 0}`",
                    f"- selected_count: `{variable.get('selected_count') or 0}`",
                    "",
                    "| Entity | 强度 | 类型 | 日期 | 来源 | 关键词 | 摘录 |",
                    "|---|---|---|---|---|---|---|",
                ]
            )
            selected = variable.get("outputs") or []
            if not selected:
                lines.append("| - | - | - | - | 暂无可映射来源 | - | - |")
            for item in selected[:12]:
                lines.append(
                    "| {entity} | {strength} | {kind} | {date} | `{path}` | {keywords} | {snippet} |".format(
                        entity=md_cell(item.get("entity_id")),
                        strength=md_cell(item.get("source_strength")),
                        kind=md_cell(item.get("source_kind")),
                        date=md_cell(str(item.get("published_at") or "")[:10]),
                        path=md_cell(item.get("source_rel_path")),
                        keywords=md_cell(item.get("matched_keywords")),
                        snippet=md_cell(item.get("snippet")),
                    )
                )
            lines.append("")

    lines.extend(["", "## 新增/可用来源", "", "| Entity | 来源 | 日期 | 路径 |", "|---|---|---|---|"])
    source_outputs = outputs.get("outputs") or []
    if not source_outputs:
        lines.append("| - | 暂无新增来源 | - | - |")
    for item in source_outputs[:40]:
        rel_path = item.get("source_rel_path")
        path_text = f"`{rel_path}`" if rel_path else "-"
        lines.append(
            "| {entity} | {title} | {date} | {path} |".format(
                entity=md_cell(item.get("entity_id")),
                title=md_cell(item.get("title")),
                date=md_cell(item.get("published_at")),
                path=path_text,
            )
        )

    failures = outputs.get("failures") or []
    if failures:
        lines.extend(["", "## 抓取失败/待复核", "", "| Entity | Error |", "|---|---|"])
        for failure in failures[:20]:
            lines.append(
                "| {entity} | {error} |".format(
                    entity=md_cell(failure.get("entity_id") or failure.get("target_key") or failure.get("sec_symbol")),
                    error=md_cell(failure.get("error") or failure),
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def write_summary(result: dict[str, Any], entity_id: str) -> dict[str, str]:
    batch_date = date_from_entity(entity_id)
    out_dir = OUTPUT_ROOT / batch_date
    out_dir.mkdir(parents=True, exist_ok=True)
    mode_suffix = "" if result.get("mode") == "executed" else "__planned"
    path = out_dir / f"{safe_filename(result['action_id'])}{mode_suffix}.md"
    path.write_text(render_summary_markdown(result), encoding="utf-8")
    return {"summary_rel_path": relative_to_project(path)}


def process_entry(
    conn: sqlite3.Connection,
    entry: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    run_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plan = build_fetch_plan(entry, args)
    local_outputs = collect_local_evidence_outputs(conn, plan)
    command_results = []
    failed = False
    for step in plan.get("steps") or []:
        result = run_command(step, execute=args.execute)
        command_results.append(result)
        if result.get("returncode") not in (None, 0):
            failed = True
            if not args.continue_on_error:
                break
    if args.execute:
        fetch_outputs = collect_fetch_outputs(conn, created_after=run_started_at, local_outputs=local_outputs)
    else:
        fetch_outputs = {
            "entries": {},
            "outputs": local_outputs.get("outputs") or [],
            "local_resolution": {
                "by_variable": local_outputs.get("by_variable") or [],
                "source_path_count": local_outputs.get("source_path_count") or 0,
            },
            "failures": [],
            "source_paths": local_outputs.get("source_paths") or [],
            "source_path_count": local_outputs.get("source_path_count") or 0,
        }
    mode = "executed" if args.execute else "planned"
    status = "failed" if failed else ("fetched" if args.execute else "planned")
    result_payload = {
        "action_id": entry["action_id"],
        "mode": mode,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_started_at": run_started_at,
        "plan": plan,
        "command_results": command_results,
        "fetch_outputs": fetch_outputs,
        "source_paths": fetch_outputs.get("source_paths") or [],
        "source_path_count": fetch_outputs.get("source_path_count") or 0,
        "failure_count": len(fetch_outputs.get("failures") or []),
        "priority_counts": dict(Counter(task.get("priority") or "P1" for task in plan.get("tasks") or [])),
    }
    artifact_paths = write_summary(result_payload, entry["entity_id"])
    result_payload.update(artifact_paths)

    registry_entry = register_snapshot(
        conn,
        entity_type="investment_evidence_gap_fetch_snapshot",
        entity_id=entry["entity_id"],
        status=status,
        source=SCRIPT_NAME,
        relationships={
            "task_snapshot_entry_id": entry["id"],
            "action_id": entry["action_id"],
            "summary_rel_path": artifact_paths.get("summary_rel_path"),
            "source_paths": result_payload.get("source_paths") or [],
        },
        payload={
            **result_payload,
            "quality_boundary": "raw/source-layer fetch result; analyst must still read, compare, and judge evidence",
        },
    )
    return {
        "action_id": entry["action_id"],
        "new_entry_id": registry_entry["id"],
        "status": status,
        "mode": mode,
        "source_path_count": result_payload.get("source_path_count"),
        "failure_count": result_payload.get("failure_count"),
        "summary_rel_path": artifact_paths.get("summary_rel_path"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run investment hard-evidence source fetch plans")
    parser.add_argument("--action-id")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--execute", action="store_true", help="Actually run network/source fetch commands")
    parser.add_argument("--local-only", action="store_true", help="Only resolve local source_manifest evidence and local normalization steps")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--days-back", type=int, default=180)
    parser.add_argument("--max-filings", type=int, default=4)
    parser.add_argument("--max-materials", type=int, default=3)
    parser.add_argument("--max-ir-links", type=int, default=8)
    parser.add_argument("--max-transcript-pages", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    conn = connect_db()
    try:
        entries = latest_task_entries(conn, action_id=args.action_id, limit=max(args.limit, 1))
        if not entries:
            if args.allow_empty:
                print("[]")
                return
            raise SystemExit("No investment_evidence_gap_task_snapshot entries found")
        results = [process_entry(conn, entry, args) for entry in entries]
        conn.commit()
        log_run(
            SCRIPT_NAME,
            "success",
            "investment evidence gap fetch plans processed",
            {
                "action_id": args.action_id,
                "execute": args.execute,
                "result_count": len(results),
                "source_path_count": sum(result.get("source_path_count") or 0 for result in results),
                "results": results[:10],
            },
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
