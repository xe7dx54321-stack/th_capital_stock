#!/usr/bin/env python3
"""Build source-grounded investment evidence packs for portfolio actions."""

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, ensure_auto_handoff
from smr_external_research import external_research_snapshots
from smr_official_materials import summarize_official_materials
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_source_registry import source_is_usable, source_status

OUTPUT_ROOT = project_path("02_research", "investment_evidence_packs")
SCRIPT_NAME = "build_investment_evidence_pack.py"
INVESTMENT_ACTION_TYPES = {"swap_ready", "swap_watch", "holding_watch", "reduce_watch", "buy_ready", "sell_ready"}
HARD_EVIDENCE_VARIABLES = [
    {
        "id": "cloud_capex",
        "label": "云厂商 capex / AI 基建强度",
        "research_question": "客户侧 AI 基建投入是否仍在加速，且足以支撑光模块需求继续超预期？",
        "why_it_matters": "决定中际旭创需求持续性、订单可见度和估值能否承受高位波动。",
        "accepted_evidence": "云厂商财报、官方业绩会、capex 指引、AI 基建/数据中心建设进度、客户订单或容量承诺。",
        "required_analyst_work": [
            "区分资本开支总额、AI 相关增量、数据中心长周期资产和短周期服务器/网络设备投入。",
            "比较微软、谷歌、亚马逊、Meta 之间的共识与分歧，判断是否只是市场已知的一致预期。",
            "把客户侧 capex 变化映射到光模块订单节奏，不能直接等同于中际旭创收入。",
        ],
        "patterns": [
            r"\bcapex\b",
            r"capital expenditures?",
            r"capital investment",
            r"levels? of investment",
            r"investment over the next",
            r"data centers?",
            r"datacenters?",
            r"AI infrastructure",
            r"infrastructure investment",
            r"infrastructure spend",
            r"compute capacity",
            r"scale compute",
            r"capacity needs",
            r"revenue-ready",
            r"云.*资本开支",
            r"数据中心",
            r"AI 基建",
            r"算力",
        ],
        "priority_terms": ["capex", "capital expenditure", "data center", "infrastructure spend", "scale compute", "capacity needs", "revenue-ready"],
    },
    {
        "id": "orders_demand",
        "label": "订单 / 需求 / 交付可见度",
        "research_question": "800G/1.6T 光模块需求是否有订单、交付或客户排产层面的硬证据支持？",
        "why_it_matters": "决定收入兑现节奏、回踩后是否值得提高敞口，以及高景气是否会被证伪。",
        "accepted_evidence": "公司 IR、客户/供应链订单、backlog、产能利用率、交付瓶颈、客户容量承诺或可验证的出货数据。",
        "required_analyst_work": [
            "区分终端 AI 需求、云厂商容量需求和中际旭创实际订单/交付。",
            "检查需求强不强、节奏是否提前、是否存在客户集中或交付瓶颈。",
            "若只有券商叙述而缺少一手订单锚点，必须降级为待补证据。",
        ],
        "patterns": [
            r"\border(s|ed|ing)?\b",
            r"\bdemand\b",
            r"\bbacklog\b",
            r"revenue backlog",
            r"\bcommitment\b",
            r"revenue-ready",
            r"capacity",
            r"supply constrained",
            r"capacity constrained",
            r"commercial booking(s)?",
            r"enterprise adoption",
            r"AI labs",
            r"Trainium demand",
            r"订单",
            r"在手",
            r"需求",
            r"交付",
            r"客户",
        ],
        "priority_terms": ["backlog", "commitment", "demand", "revenue-ready", "capacity", "supply", "customer"],
    },
    {
        "id": "margin_efficiency",
        "label": "毛利率 / 良率 / 投入产出效率",
        "research_question": "产品结构、良率、价格和产能利用率是否支持中际旭创利润率继续优于市场预期？",
        "why_it_matters": "决定高收入增长能否转化为盈利弹性，也决定高估值下的下行保护。",
        "accepted_evidence": "公司披露的毛利率/费用率、产品结构、良率或产能利用率、同业利润率、客户 AI 业务 ROI 与计价方式。",
        "required_analyst_work": [
            "把客户侧 AI ROI 与供应商利润率拆开，不得混作同一结论。",
            "检查高端产品占比提升是否被价格压力、扩产折旧或良率爬坡抵消。",
            "对比同业或客户披露，识别利润率分歧在哪里。",
        ],
        "patterns": [
            r"gross margin",
            r"operating margin",
            r"\bmargin(s)?\b",
            r"\bROI\b",
            r"\bROIC\b",
            r"return on invested capital",
            r"efficien(cy|t)",
            r"utilization",
            r"yield",
            r"毛利",
            r"良率",
            r"费用率",
            r"投入产出",
        ],
        "priority_terms": ["gross margin", "operating margin", "roi", "roic", "yield", "efficiency", "utilization", "毛利"],
    },
    {
        "id": "competition",
        "label": "竞争格局 / 供应链份额",
        "research_question": "中际旭创在高速光模块供应链中的份额、技术代际和价格压力是否仍有优势？",
        "why_it_matters": "决定景气上行是否能落到公司份额和盈利上，也决定趋势交易的证伪点。",
        "accepted_evidence": "竞品产能/产品路线、客户双供信息、供应商份额变化、价格压力、技术路线或管理层竞争表述。",
        "required_analyst_work": [
            "把行业需求增长与公司份额增长分开验证。",
            "检查 800G/1.6T、硅光、CPO 等路线中哪些是确定订单，哪些只是叙事。",
            "识别竞争加剧、降价或客户自研对利润率的影响。",
        ],
        "patterns": [
            r"compet(ition|itive|itor)",
            r"market share",
            r"custom silicon",
            r"\bASIC\b",
            r"\bTrainium\b",
            r"\bTPU\b",
            r"supplier",
            r"supply chain",
            r"price pressure",
            r"竞争",
            r"份额",
            r"供应商",
            r"供应链",
            r"降价",
        ],
        "priority_terms": ["competitive", "competition", "market share", "custom silicon", "trainium", "supplier", "supply chain", "竞争", "份额"],
    },
    {
        "id": "alibaba_ai_progress",
        "label": "阿里 AI / 云业务进展与压力",
        "research_question": "阿里 AI/云业务的增长、资本开支和利润压力是否足以改变调出候选判断？",
        "why_it_matters": "决定调出阿里是机会成本优化，还是错杀一个同样具备 AI 云弹性的资产。",
        "accepted_evidence": "阿里财报/公告/IR 材料、云收入与利润率、AI 相关收入或投入、管理层对资本开支和竞争的表述。",
        "required_analyst_work": [
            "区分阿里云/AI 的基本面进展与电商、本地生活等其他业务压力。",
            "比较阿里 AI 叙事与中际旭创光模块弹性的确定性和赔率。",
            "若阿里云 AI 增长足够强，必须重新评估调出腿的机会成本。",
        ],
        "patterns": [
            r"Alibaba Cloud",
            r"Cloud Intelligence",
            r"AI Agent",
            r"agentic",
            r"AI-driven",
            r"AI product",
            r"AI.*cloud",
            r"\bcapex\b",
            r"cloud revenue",
            r"通义",
            r"大模型",
            r"AI 应用",
            r"云智能",
            r"客户管理",
        ],
        "priority_terms": ["cloud intelligence", "ai agent", "agentic", "ai-driven", "ai product", "cloud revenue", "阿里", "通义", "云智能"],
        "path_filters": ["09988", "baba", "alibaba"],
    },
]

SOURCE_KIND_LABELS = {
    "announcement": "官方公告/IR 记录",
    "cninfo_announcement": "巨潮公告/IR 记录",
    "sec_filing_document": "SEC 主文件",
    "sec_earnings_material": "SEC 业绩材料",
    "official_ir_material": "公司 IR 材料",
    "ir_material_pdf": "公司 IR PDF",
    "ir_landing_page": "公司 IR 入口",
    "public_transcript": "公开电话会文字稿",
    "research_pdf_text": "研报 PDF 文本",
    "research_article": "研报正文",
    "research_table_structured": "研报表格结构化",
    "research_structured": "研报结构化",
    "research_search": "研报搜索快照",
    "news_article": "新闻正文",
    "news_search": "新闻搜索快照",
    "stock_research": "内部研究卡",
    "recommendation_card": "推荐卡",
}

SOURCE_STRENGTH_BY_KIND = {
    "announcement": "hard",
    "cninfo_announcement": "hard",
    "sec_filing_document": "hard",
    "sec_earnings_material": "hard",
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

SOURCE_KIND_PRIORITY = {
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
    "news_search": 14,
}

SOURCE_KIND_REGISTRY_KEYS = {
    "announcement": "cninfo_announcement",
    "cninfo_announcement": "cninfo_announcement",
    "hkex_announcement": "hkex_announcement",
    "sec_filing_document": "sec_filing_document",
    "sec_earnings_material": "sec_earnings_material",
    "official_ir_material": "official_ir_material",
    "ir_material_pdf": "official_ir_material",
    "ir_landing_page": "official_ir_page_discovery",
    "public_transcript": "public_transcript_fool",
    "research_pdf_text": "eastmoney_report_pdf_text",
    "research_article": "eastmoney_report_article",
    "research_table_structured": "eastmoney_report_table_structured",
    "research_structured": "eastmoney_report_structured",
    "research_search": "eastmoney_report_search",
    "news_article": "eastmoney_news_article",
    "news_search": "eastmoney_news_search",
    "stock_research": "smr_internal_stock_research",
    "recommendation_card": "smr_internal_recommendation_card",
}

EXPANDED_SOURCE_KINDS = {
    "announcement",
    "cninfo_announcement",
    "sec_filing_document",
    "sec_earnings_material",
    "official_ir_material",
    "ir_material_pdf",
    "ir_landing_page",
    "public_transcript",
    "research_pdf_text",
    "research_article",
    "research_table_structured",
    "research_structured",
    "research_search",
    "news_article",
    "stock_research",
    "recommendation_card",
}


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def sanitize(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^0-9A-Za-z._-]+", "_", text)
    return text.strip("._") or "unknown"


def latest_registry_entries(conn: sqlite3.Connection, entity_type: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (entity_type, limit),
    ).fetchall()
    return [registry_row(row) for row in rows]


def registry_row(row: sqlite3.Row) -> dict[str, Any]:
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


def find_action_in_entry(entry: dict[str, Any], action_id: str | None) -> dict[str, Any] | None:
    actions = (entry.get("payload") or {}).get("actions") or []
    if action_id:
        for action in actions:
            if action.get("action_id") == action_id:
                return action
        return None
    for action in actions:
        if action.get("action_type") in INVESTMENT_ACTION_TYPES:
            return action
    return actions[0] if actions else None


def selected_actions(conn: sqlite3.Connection, action_id: str | None, limit: int) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    entries = latest_registry_entries(conn, "portfolio_action_memo_snapshot", limit=80)
    results: list[tuple[dict[str, Any], dict[str, Any]]] = []
    seen = set()
    if action_id:
        for entry in entries:
            action = find_action_in_entry(entry, action_id)
            if action:
                return [(entry, action)]
        return []

    for entry in entries:
        for action in (entry.get("payload") or {}).get("actions") or []:
            aid = action.get("action_id")
            if not aid or aid in seen:
                continue
            if action.get("action_type") not in INVESTMENT_ACTION_TYPES:
                continue
            seen.add(aid)
            results.append((entry, action))
            if len(results) >= limit:
                return results
    return results


def action_symbols(action: dict[str, Any]) -> list[dict[str, Any]]:
    symbols: list[dict[str, Any]] = []
    seen = set()
    for leg_name in ("add", "remove", "subject"):
        leg = action.get(leg_name) or {}
        ts_code = leg.get("ts_code")
        if not ts_code or ts_code in seen:
            continue
        seen.add(ts_code)
        symbols.append(
            {
                "leg": leg_name,
                "ts_code": ts_code,
                "name": leg.get("name") or ts_code,
                "sector": leg.get("sector"),
            }
        )
    return symbols


def compact_dict(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: data.get(key) for key in keys if data.get(key) not in (None, "", [], {})}


def compact_symbol_object(obj: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "ts_code",
        "symbol",
        "name",
        "market",
        "sector",
        "primary_pool",
        "objective_view",
        "priority",
        "priority_score",
        "latest_trade_date",
        "latest_close",
        "latest_pct_chg",
        "trend_strength",
        "rsi_14",
        "ma_20",
        "ma_60",
        "ma_120",
        "pe_ttm",
        "pb",
        "revenue_yoy",
        "net_profit_yoy",
        "rotation_in_score",
        "rotation_out_score",
        "quality_score",
        "signal_tags",
        "trend_label",
        "trend_summary",
        "valuation_label",
        "valuation_summary",
        "summary_line",
        "driver_lines",
        "risk_flags",
        "next_checks",
        "watchpoints",
    ]
    compact = compact_dict(obj, keys)
    for nested_key in ("trend_state", "valuation_pressure", "research_staleness"):
        nested = obj.get(nested_key)
        if isinstance(nested, dict):
            compact[nested_key] = compact_dict(nested, ["label", "summary", "score"])
    return compact


def find_symbol_objects(payload: Any, ts_code: str, limit: int = 8) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen = set()

    def visit(value: Any):
        if len(results) >= limit:
            return
        if isinstance(value, dict):
            if value.get("ts_code") == ts_code or value.get("symbol") == ts_code:
                compact = compact_symbol_object(value)
                key = json.dumps(compact, ensure_ascii=False, sort_keys=True)
                if compact and key not in seen:
                    seen.add(key)
                    results.append(compact)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return results


def source_manifest_items_for_symbol(conn: sqlite3.Connection, ts_code: str, limit: int = 60) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT source_type, title, source_rel_path, metadata_json, updated_at, created_at
        FROM source_manifest
        WHERE status='active'
          AND entity_id=?
          AND (
              source_type IN ('external_source_snapshot', 'stock_research', 'recommendation_card')
              OR json_extract(metadata_json, '$.source_kind') IN (
                  'announcement', 'cninfo_announcement', 'sec_filing_document', 'sec_earnings_material',
                  'official_ir_material', 'ir_material_pdf', 'public_transcript',
                  'research_pdf_text', 'research_article', 'research_table_structured', 'research_structured',
                  'research_search', 'news_article'
              )
          )
        ORDER BY datetime(updated_at) DESC, datetime(created_at) DESC, source_rel_path ASC
        LIMIT ?
        """,
        (ts_code, max(limit * 3, limit)),
    ).fetchall()
    items: list[dict[str, Any]] = []
    seen = set()
    for row in rows:
        source_rel_path = row["source_rel_path"]
        if not source_rel_path or source_rel_path in seen:
            continue
        seen.add(source_rel_path)
        metadata = load_json(row["metadata_json"], {})
        source_kind = metadata.get("source_kind") or row["source_type"]
        if source_kind not in EXPANDED_SOURCE_KINDS and row["source_type"] not in {"stock_research", "recommendation_card"}:
            continue
        source_key = source_registry_key(source_kind, row["source_type"], metadata.get("provider") or "")
        if not source_is_usable(source_key):
            continue
        item = {
            "source_type": row["source_type"],
            "source_kind": source_kind,
            "source_registry_key": source_key,
            "source_registry_status": source_status(source_key),
            "evidence_usable": True,
            "source_kind_label": source_kind_label(source_kind),
            "source_strength": source_strength(source_kind),
            "title": row["title"],
            "source_rel_path": source_rel_path,
            "published_at": metadata.get("published_at") or metadata.get("notice_date") or row["updated_at"],
            "updated_at": row["updated_at"],
            "provider": metadata.get("provider") or "",
            "info_code": metadata.get("info_code") or "",
        }
        items.append(item)
    items.sort(
        key=lambda item: (
            source_kind_rank(item.get("source_kind")),
            str(item.get("published_at") or item.get("updated_at") or ""),
            item.get("title") or "",
        )
    )
    return items[:limit]


def collect_symbol_context(conn: sqlite3.Connection, symbol: dict[str, Any]) -> dict[str, Any]:
    ts_code = symbol["ts_code"]
    external_items = external_research_snapshots(conn, ts_code, limit=12)
    official_material = summarize_official_materials(conn, ts_code, limit=6)
    public_transcript = latest_public_transcript_snapshot(conn, ts_code)
    source_index = source_manifest_items_for_symbol(conn, ts_code, limit=60)

    technical_context: dict[str, list[dict[str, Any]]] = {}
    for entity_type in (
        "strategy_watch_batch",
        "rotation_candidate_snapshot",
        "rotation_execution_plan_snapshot",
        "price_range_forecast_snapshot",
        "risk_monitor_snapshot",
        "trade_risk_decision_snapshot",
        "stock_objective_monitor_snapshot",
        "opportunity_radar_snapshot",
        "opportunity_lifecycle_snapshot",
        "paper_watch_performance_snapshot",
    ):
        entries = latest_registry_entries(conn, entity_type, limit=1)
        if not entries:
            continue
        objects = find_symbol_objects(entries[0].get("payload") or {}, ts_code, limit=6)
        if objects:
            technical_context[entity_type] = objects

    return {
        **symbol,
        "external_research_items": external_items,
        "official_material": official_material,
        "public_transcript": public_transcript,
        "source_index": source_index,
        "technical_context": technical_context,
    }


def latest_gap_fetch_snapshot(conn: sqlite3.Connection, action_id: str | None) -> dict[str, Any] | None:
    if not action_id:
        return None
    rows = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, snapshot_index, created_at
        FROM task_registry_entry
        WHERE entity_type='investment_evidence_gap_fetch_snapshot'
        ORDER BY snapshot_index DESC, id DESC
        LIMIT 80
        """
    ).fetchall()
    for row in rows:
        payload = load_json(row["payload_json"], {})
        if payload.get("action_id") != action_id:
            continue
        source_count = (
            payload.get("source_path_count")
            or len(payload.get("source_paths") or [])
            or len(((payload.get("fetch_outputs") or {}).get("outputs") or []))
        )
        if payload.get("mode") == "planned":
            continue
        if source_count <= 0 and not payload.get("failure_count"):
            continue
        return {
            "id": row["id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "status": row["status"],
            "source": row["source"],
            "relationships": load_json(row["relationships_json"], {}),
            "payload": payload,
            "snapshot_index": row["snapshot_index"],
            "created_at": row["created_at"],
        }
    return None


def source_paths_for_symbol(context: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for item in context.get("external_research_items") or []:
        if item.get("source_rel_path"):
            paths.append(item["source_rel_path"])
    official = context.get("official_material") or {}
    paths.extend([path for path in official.get("source_rel_paths") or [] if path])
    transcript = context.get("public_transcript") or {}
    if transcript.get("source_rel_path"):
        paths.append(transcript["source_rel_path"])
    for item in context.get("source_index") or []:
        if item.get("source_rel_path"):
            paths.append(item["source_rel_path"])
    return unique(paths)


def unique(values: list[str]) -> list[str]:
    results = []
    seen = set()
    for value in values:
        if not isinstance(value, str) or not value or value in seen:
            continue
        seen.add(value)
        results.append(value)
    return results


def text_preview(rel_path: str, max_chars: int = 2600) -> dict[str, Any]:
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return {"rel_path": rel_path, "exists": False, "preview": ""}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return {"rel_path": rel_path, "exists": True, "preview": f"(unreadable: {exc})"}
    text = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())
    if len(text) > max_chars:
        text = text[: max_chars - 3].rstrip() + "..."
    return {"rel_path": rel_path, "exists": True, "preview": text}


def source_text(rel_path: str, max_chars: int = 180_000) -> str:
    path = normalize_project_path(rel_path)
    if path is None or not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def source_title(text: str, rel_path: str) -> str:
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("title:"):
            return clean_source_title(stripped.split(":", 1)[1].strip().strip('"') or rel_path)
        if stripped.startswith("# "):
            return clean_source_title(stripped[2:].strip() or rel_path)
    return rel_path


def parse_source_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:120]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def source_kind_label(source_kind: str | None) -> str:
    return SOURCE_KIND_LABELS.get(str(source_kind or "").strip(), str(source_kind or "").strip() or "unknown")


def source_strength(source_kind: str | None) -> str:
    return SOURCE_STRENGTH_BY_KIND.get(str(source_kind or "").strip(), "unknown")


def source_kind_rank(source_kind: str | None) -> int:
    return SOURCE_KIND_PRIORITY.get(str(source_kind or "").strip(), 99)


def source_registry_key(source_kind: str | None, source_type: str | None = None, provider: str | None = None) -> str:
    kind = str(source_kind or "").strip()
    provider_text = str(provider or "").strip().lower()
    if kind == "public_transcript" and "seeking" in provider_text:
        return "public_transcript_seekingalpha"
    if kind in {"research_structured", "research_table_structured", "research_article", "research_pdf_text", "research_search"}:
        if "marketscreener" in provider_text:
            return "public_analyst_signal_marketscreener"
        if "marketbeat" in provider_text:
            return "public_analyst_signal_marketbeat"
    return SOURCE_KIND_REGISTRY_KEYS.get(kind) or SOURCE_KIND_REGISTRY_KEYS.get(str(source_type or "").strip()) or kind or "unknown"


def source_kind_is_usable(source_kind: str | None, source_type: str | None = None, provider: str | None = None) -> bool:
    key = source_registry_key(source_kind, source_type, provider)
    if key.startswith("smr_internal_"):
        return True
    return source_is_usable(key)


def source_metadata(rel_path: str, text: str | None = None) -> dict[str, Any]:
    raw_text = text if text is not None else source_text(rel_path, max_chars=24_000)
    frontmatter = parse_source_frontmatter(raw_text or "")
    source_kind = frontmatter.get("source_kind") or infer_source_kind_from_path(rel_path)
    provider = frontmatter.get("provider") or ""
    registry_key = source_registry_key(source_kind, provider=provider)
    published_at = (
        frontmatter.get("published_at")
        or frontmatter.get("notice_date")
        or frontmatter.get("fetched_at")
        or ""
    )
    return {
        "rel_path": rel_path,
        "title": clean_source_title(frontmatter.get("title") or source_title(raw_text or "", rel_path)),
        "source_kind": source_kind,
        "source_registry_key": registry_key,
        "source_registry_status": source_status(registry_key),
        "evidence_usable": source_kind_is_usable(source_kind, provider=provider),
        "source_kind_label": source_kind_label(source_kind),
        "source_strength": source_strength(source_kind),
        "entity_id": frontmatter.get("entity_id") or infer_entity_id_from_path(rel_path),
        "provider": provider,
        "published_at": published_at,
        "source_url": frontmatter.get("source_url") or "",
    }


def infer_entity_id_from_path(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if "stock" in parts:
        idx = parts.index("stock")
        if idx + 1 < len(parts):
            slug = parts[idx + 1]
            if "_" in slug:
                code, market = slug.rsplit("_", 1)
                if market.upper() in {"SZ", "SH", "BJ", "HK"}:
                    return f"{code}.{market.upper()}"
            return slug.upper()
    return ""


def infer_source_kind_from_path(rel_path: str) -> str:
    filename = Path(rel_path).name.lower()
    for source_kind in sorted(EXPANDED_SOURCE_KINDS, key=len, reverse=True):
        if source_kind.lower() in filename:
            return source_kind
    if "/02_research/stock/" in f"/{rel_path}":
        return "stock_research"
    if "/03_stock_pool/" in f"/{rel_path}":
        return "recommendation_card"
    return ""


def clean_source_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    for marker in (" / The Motley Fool", " | The Motley Fool", " Bars Arrow-Thin-Down"):
        if marker in title:
            title = title.split(marker, 1)[0].strip()
    if len(title) > 120:
        title = title[:117].rstrip() + "..."
    return title


def compact_snippet(text: str, max_chars: int = 720) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def is_noise_segment(text: str) -> bool:
    if not text:
        return True
    lower = text.lower()
    if lower.count("us-gaap:") >= 2 or lower.count("xbrl") >= 2 or lower.count("0001326801") >= 2:
        return True
    if lower.count("member ") >= 6 and lower.count("2026-") >= 3:
        return True
    if len(re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)) >= 5:
        return True
    if len(text) > 280:
        digit_ratio = sum(ch.isdigit() for ch in text) / max(len(text), 1)
        if digit_ratio > 0.36:
            return True
    return False


def source_segments(text: str) -> list[str]:
    segments: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(
            r"^(title|source_url|source_kind|entity_type|entity_id|source_domain|content_type|fetched_at|raw_rel_path|meta_rel_path|tags|provider|cik|company_name|form_type|accession_number):",
            line,
            re.IGNORECASE,
        ):
            continue
        if is_noise_segment(line):
            continue
        if len(line) <= 900:
            segments.append(line)
            continue
        chunks = re.split(r"(?<=[。！？.!?;；])\s+", line)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            if is_noise_segment(chunk):
                continue
            if len(chunk) <= 900:
                segments.append(chunk)
                continue
            for start in range(0, len(chunk), 700):
                window = chunk[start : start + 900]
                if not is_noise_segment(window):
                    segments.append(window)
    return segments


def variable_match_score(snippet: str, hits: list[str], variable: dict[str, Any]) -> int:
    lower = snippet.lower()
    score = len(hits)
    for term in variable.get("priority_terms") or []:
        if str(term).lower() in lower:
            score += 3
    if "?" in snippet and any(token in lower for token in ("capex", "investment", "demand", "margin", "competition")):
        score += 2
    if any(token in lower for token in ("operator:", "please proceed", "thank you for taking")):
        score -= 1
    return score


def extract_variable_snippets(rel_path: str, variable: dict[str, Any], max_snippets: int = 2) -> list[dict[str, Any]]:
    text = source_text(rel_path)
    if not text:
        return []
    metadata = source_metadata(rel_path, text)
    if not metadata.get("evidence_usable"):
        return []
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in variable.get("patterns") or []]
    if not patterns:
        return []
    segments = source_segments(text)
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for idx, segment in enumerate(segments):
        hits = [pattern.pattern for pattern in patterns if pattern.search(segment)]
        if not hits:
            continue
        context_segments = [item for item in segments[idx : min(len(segments), idx + 2)] if not is_noise_segment(item)]
        snippet = compact_snippet(" ".join(context_segments))
        if not snippet:
            continue
        candidates.append(
            (
                variable_match_score(snippet, hits, variable),
                idx,
                {
                    "rel_path": rel_path,
                    "title": metadata.get("title") or rel_path,
                    "entity_id": metadata.get("entity_id") or "",
                    "source_kind": metadata.get("source_kind") or "",
                    "source_registry_key": metadata.get("source_registry_key") or "",
                    "source_registry_status": metadata.get("source_registry_status") or "",
                    "source_kind_label": metadata.get("source_kind_label") or "",
                    "source_strength": metadata.get("source_strength") or "",
                    "provider": metadata.get("provider") or "",
                    "published_at": metadata.get("published_at") or "",
                    "matched_patterns": hits[:6],
                    "snippet": snippet,
                },
            )
        )

    snippets: list[dict[str, Any]] = []
    seen = set()
    for _score, _idx, candidate in sorted(candidates, key=lambda item: (-item[0], item[1])):
        key = re.sub(r"\W+", "", candidate["snippet"].lower())[:220]
        if not key or key in seen:
            continue
        seen.add(key)
        snippets.append(candidate)
        if len(snippets) >= max_snippets:
            break
    return snippets


def variable_material_status(snippets: list[dict[str, Any]]) -> str:
    if not snippets:
        return "材料层缺口"
    strength_counts = Counter(item.get("source_strength") or "unknown" for item in snippets)
    entity_count = len({item.get("entity_id") for item in snippets if item.get("entity_id")})
    hard_count = strength_counts.get("hard", 0)
    strong_count = strength_counts.get("strong_supporting", 0)
    if hard_count >= 3 and entity_count >= 2:
        return "材料层已具备交叉验证条件"
    if hard_count >= 1 and (hard_count + strong_count) >= 3:
        return "材料层部分具备，需 agent 深读判断"
    return "材料层偏弱，需继续补证"


def build_variable_evidence_card(variable: dict[str, Any], snippets: list[dict[str, Any]]) -> dict[str, Any]:
    source_kind_counts = Counter(item.get("source_kind") or "unknown" for item in snippets)
    strength_counts = Counter(item.get("source_strength") or "unknown" for item in snippets)
    entity_counts = Counter(item.get("entity_id") or "unknown" for item in snippets)
    return {
        "variable_id": variable.get("id"),
        "variable_label": variable.get("label"),
        "research_question": variable.get("research_question"),
        "why_it_matters": variable.get("why_it_matters"),
        "accepted_evidence": variable.get("accepted_evidence"),
        "material_status": variable_material_status(snippets),
        "source_kind_counts": dict(source_kind_counts),
        "source_strength_counts": dict(strength_counts),
        "entity_counts": dict(entity_counts),
        "required_analyst_work": variable.get("required_analyst_work") or [],
        "analyst_boundary": "材料层状态不是投资结论；agent 必须回到来源原文，比较共识/分歧后形成判断。",
    }


def build_hard_evidence_digest(source_paths: list[str]) -> list[dict[str, Any]]:
    readable_paths = [
        path
        for path in unique(source_paths)
        if isinstance(path, str) and path and not path.startswith("registry_") and normalize_project_path(path) is not None
    ]
    digest: list[dict[str, Any]] = []
    for variable in HARD_EVIDENCE_VARIABLES:
        snippets: list[dict[str, str]] = []
        matched_paths = set()
        for rel_path in readable_paths[:80]:
            path_filters = [str(item).lower() for item in variable.get("path_filters") or []]
            if path_filters and not any(token in rel_path.lower() for token in path_filters):
                continue
            path_snippets = extract_variable_snippets(rel_path, variable, max_snippets=2)
            if not path_snippets:
                continue
            matched_paths.add(rel_path)
            snippets.extend(path_snippets)
            if len(snippets) >= 10:
                break
        digest.append(
            {
                "id": variable["id"],
                "label": variable["label"],
                "research_question": variable.get("research_question"),
                "why_it_matters": variable.get("why_it_matters"),
                "accepted_evidence": variable.get("accepted_evidence"),
                "matched_source_count": len(matched_paths),
                "snippets": snippets[:10],
                "evidence_card": build_variable_evidence_card(variable, snippets[:10]),
            }
        )
    return digest


def format_money(value: Any) -> str:
    if value in (None, ""):
        return "-"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def md_cell(value: Any) -> str:
    if isinstance(value, list):
        text = "；".join(str(item) for item in value)
    else:
        text = str(value or "-")
    return text.replace("\n", " ").replace("|", " / ").strip()


def render_external_research_table(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Published | Org | Rating | Title | Target | Key Forecast Fields | Source |",
        "|---|---|---|---|---:|---|---|",
    ]
    if not items:
        lines.append("| - | - | - | 暂无可用外部研究样本 | - | - | - |")
        return lines
    for item in items:
        metric_bits = []
        for label, key in (
            ("Revenue", "revenue_billion"),
            ("NetProfit", "net_profit_billion"),
            ("EPS", "eps_yuan"),
            ("PE", "pe_multiple"),
        ):
            values = item.get(key) or {}
            if values:
                metric_bits.append(f"{label}: {json.dumps(values, ensure_ascii=False, sort_keys=True)}")
        lines.append(
            "| {published} | {org} | {rating} | {title} | {target} | {metrics} | `{source}` |".format(
                published=item.get("published_at") or "-",
                org=item.get("org_name") or "-",
                rating=item.get("rating_name") or "-",
                title=str(item.get("title") or "-").replace("|", "/"),
                target=item.get("target_price_yuan") or "-",
                metrics="; ".join(metric_bits) or "-",
                source=item.get("source_rel_path") or "-",
            )
        )
    return lines


def render_official_material_table(material: dict[str, Any]) -> list[str]:
    lines = [
        "| Date | Source | Event | Title | Summary | Path |",
        "|---|---|---|---|---|---|",
    ]
    items = material.get("items") or []
    if not items:
        lines.append("| - | - | - | 暂无可用官方一手材料 | - | - |")
        return lines
    for item in items:
        lines.append(
            "| {date} | {source} | {event} | {title} | {summary} | `{path}` |".format(
                date=item.get("publish_time") or "-",
                source=item.get("source_label") or item.get("source_key") or "-",
                event=item.get("event_label") or item.get("event_type") or "-",
                title=str(item.get("title") or "-").replace("|", "/"),
                summary=str(item.get("summary") or "-").replace("|", "/"),
                path=item.get("source_rel_path") or "-",
            )
        )
    return lines


def render_technical_context_table(context: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines = [
        "| Snapshot | Evidence |",
        "|---|---|",
    ]
    if not context:
        lines.append("| - | 暂无可用技术/组合上下文。 |")
        return lines
    for entity_type, objects in context.items():
        for obj in objects:
            lines.append(
                "| `{entity_type}` | `{payload}` |".format(
                    entity_type=entity_type,
                    payload=json.dumps(obj, ensure_ascii=False, sort_keys=True),
                )
            )
    return lines


def render_source_index_table(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 类型 | 强度 | 日期 | 标题 | 路径 |",
        "|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| - | - | - | 暂无补充材料索引 | - |")
        return lines
    for item in items[:50]:
        lines.append(
            "| {kind} | {strength} | {date} | {title} | `{path}` |".format(
                kind=md_cell(item.get("source_kind_label") or item.get("source_kind")),
                strength=md_cell(item.get("source_strength")),
                date=md_cell(str(item.get("published_at") or item.get("updated_at") or "")[:10]),
                title=md_cell(item.get("title")),
                path=md_cell(item.get("source_rel_path")),
            )
        )
    return lines


def render_gap_fetch_section(gap_fetch: dict[str, Any] | None) -> list[str]:
    if not gap_fetch:
        return [
            "## 3. Hard Evidence Supplement",
            "",
            "当前还没有接入硬证据补证执行结果。",
            "",
        ]
    payload = gap_fetch.get("payload") or {}
    outputs = (payload.get("fetch_outputs") or {}).get("outputs") or []
    failures = (payload.get("fetch_outputs") or {}).get("failures") or []
    lines = [
        "## 3. Hard Evidence Supplement",
        "",
        "这部分来自硬证据补证任务，属于原材料层。分析 agent 必须继续阅读、交叉比对和判断，不能把抓取成功当成结论。",
        "",
        f"- fetch_snapshot_entry_id: `{gap_fetch.get('id')}`",
        f"- status: `{gap_fetch.get('status')}`",
        f"- source_path_count: `{payload.get('source_path_count') or 0}`",
        f"- failure_count: `{payload.get('failure_count') or 0}`",
        f"- summary_rel_path: `{payload.get('summary_rel_path') or ''}`",
        "",
        "| Entity | Source | Date | Path |",
        "|---|---|---|---|",
    ]
    if not outputs:
        lines.append("| - | 暂无可用补证来源 | - | - |")
    for item in outputs[:40]:
        lines.append(
            "| {entity} | {title} | {date} | `{path}` |".format(
                entity=item.get("entity_id") or "-",
                title=str(item.get("title") or "-").replace("|", "/"),
                date=item.get("published_at") or "-",
                path=item.get("source_rel_path") or "-",
            )
        )
    if failures:
        lines.extend(["", "### Fetch Failures", "", "| Entity | Error |", "|---|---|"])
        for failure in failures[:20]:
            lines.append(
                "| {entity} | {error} |".format(
                    entity=failure.get("entity_id") or failure.get("target_key") or failure.get("sec_symbol") or "-",
                    error=str(failure.get("error") or failure).replace("|", "/"),
                )
            )
    lines.append("")
    return lines


def render_hard_evidence_digest_section(digest: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## 4. Hard Evidence Variable Digest",
        "",
        "这部分把原材料先按关键投研变量抽取成变量证据卡，目的是让分析 agent 优先围绕变量做交叉验证。摘录和材料层状态都不是结论；必须回到来源、比较共识/分歧并形成 SMR 自主判断。",
        "",
    ]
    if not digest:
        lines.extend(["当前还没有可用硬证据变量摘录。", ""])
        return lines
    for item in digest:
        card = item.get("evidence_card") or {}
        strength_counts = card.get("source_strength_counts") or {}
        kind_counts = card.get("source_kind_counts") or {}
        entity_counts = card.get("entity_counts") or {}
        lines.extend(
            [
                f"### {item.get('label') or item.get('id')}",
                "",
                f"- research_question: {item.get('research_question') or '-'}",
                f"- why_it_matters: {item.get('why_it_matters') or '-'}",
                f"- accepted_evidence: {item.get('accepted_evidence') or '-'}",
                f"- material_status: `{card.get('material_status') or '材料层缺口'}`",
                f"- matched_source_count: `{item.get('matched_source_count') or 0}`",
                f"- source_strength_counts: `{json.dumps(strength_counts, ensure_ascii=False, sort_keys=True)}`",
                f"- source_kind_counts: `{json.dumps(kind_counts, ensure_ascii=False, sort_keys=True)}`",
                f"- entity_counts: `{json.dumps(entity_counts, ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
        analyst_work = card.get("required_analyst_work") or []
        if analyst_work:
            lines.extend(["#### Required Analyst Work", ""])
            lines.extend([f"- {item_text}" for item_text in analyst_work])
            lines.append("")
        snippets = item.get("snippets") or []
        if not snippets:
            lines.extend(["- 暂未抽到直接匹配摘录，分析 agent 需要在补证任务中继续追材料。", ""])
            continue
        for idx, snippet in enumerate(snippets, start=1):
            lines.extend(
                [
                    f"#### Evidence Clip {idx}",
                    "",
                    f"- entity: `{snippet.get('entity_id') or ''}`",
                    f"- source_kind: `{snippet.get('source_kind') or ''}` / {snippet.get('source_kind_label') or ''}",
                    f"- source_strength: `{snippet.get('source_strength') or ''}`",
                    f"- published_at: `{snippet.get('published_at') or ''}`",
                    f"- source: `{snippet.get('rel_path') or ''}`",
                    f"- title: {str(snippet.get('title') or '-').replace('|', '/')}",
                    f"- matched_patterns: `{', '.join(snippet.get('matched_patterns') or [])}`",
                    "",
                    "```text",
                    snippet.get("snippet") or "",
                    "```",
                    "",
                ]
            )
    return lines


def render_pack_markdown(pack: dict[str, Any]) -> str:
    action = pack["action"]
    lines = [
        f"# Investment Evidence Pack: {action.get('title') or action.get('action_id')}",
        "",
        f"- generated_at: `{pack['generated_at']}`",
        f"- action_id: `{action.get('action_id')}`",
        f"- action_type: `{action.get('action_type')}`",
        f"- priority: `{action.get('priority')}`",
        f"- source_action_snapshot: `{pack['source_action_snapshot'].get('entity_id')}` / `{pack['source_action_snapshot'].get('created_at')}`",
        "",
        "## 1. Portfolio Action Context",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Title | {action.get('title') or '-'} |",
        f"| Summary | {action.get('summary') or '-'} |",
        f"| Trade Amount | {format_money(action.get('trade_amount'))} |",
        f"| Trade Amount Pct | {action.get('trade_amount_pct') if action.get('trade_amount_pct') is not None else '-'} |",
        f"| Gate Status | {action.get('gate_status') or '-'} |",
        "",
        "### Existing Rationale And Risk Flags",
        "",
        "这些是旧链路生成的素材，不是最终研究结论。分析 agent 必须复核、交叉验证并重写判断。",
        "",
        "#### Rationale",
        "",
    ]
    rationale = action.get("rationale") or []
    lines.extend([f"- {item}" for item in rationale] or ["- 暂无。"])
    lines.extend(["", "#### Risk Flags", ""])
    lines.extend([f"- {item}" for item in (action.get("risk_flags") or [])] or ["- 暂无。"])
    lines.extend(["", "#### Next Checks", ""])
    lines.extend([f"- {item}" for item in (action.get("next_checks") or [])] or ["- 暂无。"])

    lines.extend(
        [
            "",
            "## 2. Research Task For Analyst",
            "",
            "请基于下方材料完成真正的投研综合，而不是复述任一来源结论：",
            "",
            "1. 逐条提取外部研报、官方材料、电话会和技术证据的核心观点与假设。",
            "2. 找出多来源共识，并判断哪些信息可能已经被股价充分 price in。",
            "3. 找出关键分歧，说明分歧来自预测、利润率、需求、估值、风险还是节奏。",
            "4. 对分歧形成 SMR 自主判断，明确证据、反证、置信度和需要补充的材料。",
            "5. 输出可执行的组合含义：初始动作、加仓/减仓/退出条件、证伪触发器。",
            "",
        ]
    )

    lines.extend(render_gap_fetch_section(pack.get("gap_fetch")))
    lines.extend(render_hard_evidence_digest_section(pack.get("hard_evidence_digest") or []))

    for context in pack["symbols"]:
        lines.extend(
            [
                f"## 5. Symbol Material: {context.get('name')} / {context.get('ts_code')} / {context.get('leg')}",
                "",
                f"- sector: `{context.get('sector') or ''}`",
                f"- source_path_count: `{len(source_paths_for_symbol(context))}`",
                "",
                "### External Research Samples",
                "",
                *render_external_research_table(context.get("external_research_items") or []),
                "",
                "### Official First-Party Materials",
                "",
                *render_official_material_table(context.get("official_material") or {}),
                "",
                "### Public Transcript / Management Voice",
                "",
            ]
        )
        transcript = context.get("public_transcript") or {}
        if transcript:
            lines.extend(
                [
                    f"- provider: `{transcript.get('provider') or ''}`",
                    f"- published_at: `{transcript.get('published_at') or ''}`",
                    f"- quarter_label: `{transcript.get('quarter_label') or ''}`",
                    f"- speaker_count: `{transcript.get('speaker_count') or 0}`",
                    f"- source_rel_path: `{transcript.get('source_rel_path') or ''}`",
                    "",
                    transcript.get("summary") or "暂无摘要。",
                    "",
                ]
            )
        else:
            lines.extend(["- 暂无可用公开电话会文字稿。", ""])

        lines.extend(
            [
                "### Expanded Source Index",
                "",
                "这张表保留该标的已入库的高价值材料索引，帮助 agent 从多来源交叉阅读，而不是只看少数结构化摘要。",
                "",
                *render_source_index_table(context.get("source_index") or []),
                "",
                "### Technical / Portfolio / Risk Context",
                "",
                *render_technical_context_table(context.get("technical_context") or {}),
                "",
            ]
        )

    source_previews = pack.get("source_previews") or []
    lines.extend(
        [
            "## 6. Source Previews",
            "",
            "以下只提供有限预览，完整材料路径保留在 JSON 和源文件中。",
            "",
        ]
    )
    if not source_previews:
        lines.append("- 暂无可读源文件预览。")
    for item in source_previews:
        lines.extend(
            [
                f"### `{item.get('rel_path')}`",
                "",
                f"- exists: `{item.get('exists')}`",
                "",
            ]
        )
        if item.get("preview"):
            lines.extend(["```text", item["preview"], "```", ""])

    lines.extend(
        [
            "## 7. Required Analyst Output Contract",
            "",
            "- 研究结论必须分为：`结论`、`共识`、`分歧`、`SMR 判断`、`证据链`、`反方与证伪`、`组合含义`。",
            "- 如果材料不足，必须明确写成 `素材型假设` 或 `中等置信假设`，并列出补充研究任务。",
            "- 技术指标只能用于择时和风险控制，不能替代基本面逻辑。",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(conn: sqlite3.Connection, entry: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    symbols = [collect_symbol_context(conn, symbol) for symbol in action_symbols(action)]
    action_id = action.get("action_id")
    gap_fetch = latest_gap_fetch_snapshot(conn, action_id)
    gap_fetch_payload = (gap_fetch or {}).get("payload") or {}
    gap_fetch_source_paths = gap_fetch_payload.get("source_paths") or []
    source_paths = unique(
        [
            *(action.get("source_refs") or []),
            *((entry.get("relationships") or {}).values()),
            *gap_fetch_source_paths,
            *([gap_fetch_payload.get("summary_rel_path")] if gap_fetch_payload.get("summary_rel_path") else []),
            *[path for context in symbols for path in source_paths_for_symbol(context)],
        ]
    )
    hard_evidence_source_paths = unique(
        [
            *gap_fetch_source_paths,
            *[path for context in symbols for path in source_paths_for_symbol(context)],
            *source_paths,
        ]
    )
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "source_action_snapshot": {
            "registry_entry_id": entry.get("id"),
            "entity_id": entry.get("entity_id"),
            "created_at": entry.get("created_at"),
            "status": entry.get("status"),
            "source": entry.get("source"),
            "relationships": entry.get("relationships") or {},
        },
        "symbols": symbols,
        "gap_fetch": gap_fetch,
        "source_paths": source_paths,
        "hard_evidence_digest": build_hard_evidence_digest(hard_evidence_source_paths),
        "source_previews": [text_preview(path) for path in source_paths[:24]],
    }


def write_pack(pack: dict[str, Any], dry_run: bool) -> tuple[Path, Path, str, str]:
    snapshot_id = pack["source_action_snapshot"].get("entity_id") or datetime.now().strftime("%Y-%m-%d")
    action_id = pack["action"].get("action_id") or "unknown_action"
    out_dir = OUTPUT_ROOT / sanitize(str(snapshot_id))
    json_path = out_dir / f"{sanitize(action_id)}.json"
    md_path = out_dir / f"{sanitize(action_id)}.md"
    pack_md = render_pack_markdown(pack)
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(pack_md + "\n", encoding="utf-8")
    return json_path, md_path, relative_to_project(json_path), relative_to_project(md_path)


def register_pack_snapshot(
    conn: sqlite3.Connection,
    pack: dict[str, Any],
    json_rel_path: str,
    md_rel_path: str,
    dry_run: bool,
) -> dict[str, Any] | None:
    if dry_run:
        return None
    action = pack["action"]
    action_id = action.get("action_id") or "unknown_action"
    entity_id = f"{pack['source_action_snapshot'].get('entity_id')}__{action_id}"
    entry = register_snapshot(
        conn,
        entity_type="investment_evidence_pack_snapshot",
        entity_id=entity_id,
        status="generated",
        source=SCRIPT_NAME,
        relationships={
            "action_registry_entry_id": pack["source_action_snapshot"].get("registry_entry_id"),
            "action_entity_id": pack["source_action_snapshot"].get("entity_id"),
            "action_id": action_id,
            "pack_json_rel_path": json_rel_path,
            "pack_md_rel_path": md_rel_path,
        },
        payload={
            "action_id": action_id,
            "action_type": action.get("action_type"),
            "priority": action.get("priority"),
            "title": action.get("title"),
            "pack_json_rel_path": json_rel_path,
            "pack_md_rel_path": md_rel_path,
            "symbol_count": len(pack.get("symbols") or []),
            "symbols": [
                {
                    "leg": symbol.get("leg"),
                    "ts_code": symbol.get("ts_code"),
                    "name": symbol.get("name"),
                    "external_research_count": len(symbol.get("external_research_items") or []),
                    "official_material_count": (symbol.get("official_material") or {}).get("item_count") or 0,
                    "source_index_count": len(symbol.get("source_index") or []),
                    "has_public_transcript": bool(symbol.get("public_transcript")),
                }
                for symbol in pack.get("symbols") or []
            ],
            "source_path_count": len(pack.get("source_paths") or []),
            "hard_evidence_variable_count": len(pack.get("hard_evidence_digest") or []),
            "hard_evidence_snippet_count": sum(
                len(item.get("snippets") or []) for item in (pack.get("hard_evidence_digest") or [])
            ),
            "hard_evidence_card_status_counts": dict(
                Counter(
                    ((item.get("evidence_card") or {}).get("material_status") or "unknown")
                    for item in (pack.get("hard_evidence_digest") or [])
                )
            ),
            "gap_fetch_snapshot_entry_id": ((pack.get("gap_fetch") or {}).get("id")),
            "gap_fetch_source_path_count": (((pack.get("gap_fetch") or {}).get("payload") or {}).get("source_path_count") or 0),
            "requires_human_review": True,
        },
    )
    auto_handoff = ensure_auto_handoff(
        conn,
        entry,
        note="investment evidence pack ready for deep research synthesis",
        created_by=SCRIPT_NAME,
    )
    entry["auto_handoff"] = {
        "created": auto_handoff.get("created"),
        "reason": auto_handoff.get("reason"),
        "handoff_id": ((auto_handoff.get("handoff") or {}).get("handoff_id")),
        "to_profile_id": ((auto_handoff.get("handoff") or {}).get("to_profile_id")),
    }
    return entry


def main():
    parser = argparse.ArgumentParser(description="Build investment evidence packs from portfolio actions")
    parser.add_argument("--action-id", help="Specific portfolio action_id")
    parser.add_argument("--limit", type=int, default=3, help="Number of latest investment actions to package")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = connect_db()
    try:
        pairs = selected_actions(conn, args.action_id, max(args.limit, 1))
        if not pairs:
            raise SystemExit(f"No portfolio action found for action_id={args.action_id or '*'}")

        outputs = []
        for entry, action in pairs:
            pack = build_pack(conn, entry, action)
            json_path, md_path, json_rel_path, md_rel_path = write_pack(pack, args.dry_run)
            registry_entry = register_pack_snapshot(conn, pack, json_rel_path, md_rel_path, args.dry_run)
            outputs.append(
                {
                    "action_id": action.get("action_id"),
                    "json_rel_path": json_rel_path,
                    "md_rel_path": md_rel_path,
                    "registry_entry_id": (registry_entry or {}).get("id"),
                    "auto_handoff": (registry_entry or {}).get("auto_handoff"),
                }
            )
            if args.dry_run:
                print(render_pack_markdown(pack)[:5000])
                print("")
                continue
            print(f"Investment evidence pack: {md_path}")
            print(f"  action_id={action.get('action_id')}")
            print(f"  registry_entry_id={(registry_entry or {}).get('id') or ''}")
            auto_handoff = (registry_entry or {}).get("auto_handoff") or {}
            if auto_handoff:
                print(f"  auto_handoff={auto_handoff.get('reason')} {auto_handoff.get('handoff_id') or ''}")

        if not args.dry_run:
            conn.commit()
        log_run(
            SCRIPT_NAME,
            "success",
            "investment evidence packs built",
            {
                "dry_run": args.dry_run,
                "action_id": args.action_id,
                "output_count": len(outputs),
                "outputs": outputs,
            },
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
