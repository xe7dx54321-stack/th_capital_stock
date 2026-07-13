from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from smr_app.adapters.evidence import EvidenceRequest, load_evidence
from smr_app.adapters.fundamentals import FundamentalsRequest, load_fundamentals
from smr_app.adapters.memory import create_memory_candidate
from smr_app.adapters.risk import RiskContextRequest, load_risk_context
from smr_app.adapters.valuation import ValuationRequest, load_valuation
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_configured_artifact_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
DEFAULT_ARTIFACT_ROOT = Path(_configured_artifact_roots[0]) if _configured_artifact_roots[0] else PROJECT_ROOT / "06_outputs" / "workflows"
A_SHARE_RE = re.compile(r"^\d{6}\.(?:SZ|SH|BJ)$")
H_SHARE_RE = re.compile(r"^\d{5}\.HK$")
US_SHARE_RE = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def parse_ticker(raw: Any) -> tuple[str, str]:
    ticker = str(raw or "").strip().upper()
    if A_SHARE_RE.fullmatch(ticker):
        return ticker, "A"
    if H_SHARE_RE.fullmatch(ticker):
        return ticker, "H"
    if US_SHARE_RE.fullmatch(ticker):
        return ticker, "US"
    raise ValueError("ticker must be an A-share code, a five-digit .HK code, or a US symbol")


def _connect_source(context: WorkflowContext, source_db_path: Path | None) -> sqlite3.Connection:
    if source_db_path is None or source_db_path.resolve() == context.db_path.resolve():
        return sqlite3.connect(context.db_path)
    uri = source_db_path.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _validate_input(context: WorkflowContext) -> StageResult:
    ticker, market = parse_ticker(context.input_data.get("ticker"))
    allow_network = context.input_data.get("allow_network", False)
    if not isinstance(allow_network, bool):
        raise ValueError("allow_network must be a boolean")
    if allow_network:
        raise ValueError("stock_deep_dive MVP only supports allow_network=false")
    context.state.update({"ticker": ticker, "market": market, "allow_network": False})
    return StageResult.completed("Ticker validated", {"ticker": ticker, "market": market})


def _freshness_summary(risk_data: dict[str, Any], market: str) -> dict[str, Any]:
    rows = [
        item
        for item in (risk_data.get("data_health") or {}).get("items", [])
        if item.get("data_type") == "daily_bar" and item.get("market") in {market, "global"}
    ]
    if not rows:
        return {
            "status": "unknown",
            "condition": "not_configured",
            "blocking_level": "warn",
            "reason": "No market-specific daily-bar health row was found.",
        }
    row = rows[0]
    metadata = row.get("metadata") or {}
    return {
        "status": row.get("freshness_status") or "unknown",
        "condition": metadata.get("condition") or row.get("freshness_status") or "unknown",
        "blocking_level": row.get("blocking_level") or "warn",
        "reason": row.get("staleness_reason") or "",
        "last_data_timestamp": row.get("last_data_timestamp"),
    }


def _load_context_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        ticker = context.state["ticker"]
        conn = _connect_source(context, source_db_path)
        try:
            evidence = load_evidence(conn, EvidenceRequest(ticker, limit=30, minimum_quality=0.0))
            fundamentals = load_fundamentals(conn, FundamentalsRequest(ticker))
            valuation = load_valuation(conn, ValuationRequest(ticker))
            risk = load_risk_context(conn, RiskContextRequest(ticker, limit=20))
        finally:
            conn.close()
        for name, result in {
            "evidence": evidence,
            "fundamentals": fundamentals,
            "valuation": valuation,
            "risk": risk,
        }.items():
            if result.status == "error":
                raise RuntimeError(result.error or f"{name} adapter failed")
        context.state.update(
            {
                "evidence": evidence.data,
                "fundamentals": fundamentals.data.get("snapshot") or {},
                "valuation": valuation.data.get("snapshot") or {},
                "risk": risk.data,
                "freshness": _freshness_summary(risk.data, context.state["market"]),
            }
        )
        return StageResult.completed(
            "Local research context loaded",
            {
                "evidence_count": evidence.data.get("count", 0),
                "fundamentals_status": fundamentals.status,
                "valuation_status": valuation.status,
                "freshness": context.state["freshness"],
            },
        )

    return handler


def _claim(claim_type: str, text: str, evidence_ids: list[str]) -> dict[str, Any] | None:
    ids = list(dict.fromkeys(value for value in evidence_ids if value))
    if not ids:
        return None
    normalized_text = " ".join(str(text or "").split())
    if len(normalized_text) > 800:
        normalized_text = normalized_text[:800].rstrip() + "…"
    return {"claim_type": claim_type, "text": normalized_text, "evidence_ids": ids[:8]}


def _risk_summary(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    counts_by_severity: dict[str, int] = {}
    counts_by_type: dict[str, int] = {}
    for alert in alerts:
        severity = str(alert.get("severity") or "unknown")
        alert_type = str(alert.get("alert_type") or "unknown")
        counts_by_severity[severity] = counts_by_severity.get(severity, 0) + 1
        counts_by_type[alert_type] = counts_by_type.get(alert_type, 0) + 1
    return {
        "count": len(alerts),
        "counts_by_severity": counts_by_severity,
        "counts_by_type": counts_by_type,
        "top_alerts": [
            {
                "alert_type": alert.get("alert_type"),
                "severity": alert.get("severity"),
                "message": " ".join(str(alert.get("message") or "").split())[:300],
            }
            for alert in alerts[:5]
        ],
    }


def _build_analysis(context: WorkflowContext) -> StageResult:
    ticker = context.state["ticker"]
    evidence_items = context.state["evidence"].get("items") or []
    fundamentals = context.state["fundamentals"]
    valuation = context.state["valuation"]
    usable_items = [item for item in evidence_items if item.get("usable_for_core_claim")]
    selected = usable_items or evidence_items
    selected_ids = [item.get("evidence_id") for item in selected if item.get("evidence_id")]
    fundamental_ids = [value for value in fundamentals.get("source_evidence_ids") or [] if value][:8]
    all_ids = list(dict.fromkeys([*selected_ids, *fundamental_ids]))[:12]

    claims: list[dict[str, Any]] = []
    if selected:
        item = selected[0]
        qualitative = _claim(
            "business_evidence",
            item.get("text_excerpt") or f"{ticker} 出现一项值得关注的官方信息更新。",
            [item.get("evidence_id")],
        )
        if qualitative:
            claims.append(qualitative)
    if fundamentals:
        revenue = fundamentals.get("revenue")
        cash_flow = fundamentals.get("operating_cash_flow")
        fundamental = _claim(
            "fundamentals",
            f"最新基本面快照显示：营业收入={revenue}，经营现金流={cash_flow}。",
            fundamental_ids,
        )
        if fundamental:
            claims.append(fundamental)
    if valuation and all_ids:
        valuation_claim = _claim(
            "valuation_context",
            f"最新估值信息显示：价格={valuation.get('current_price')}，市盈率={valuation.get('pe_ttm')}；该信息仅作背景，不构成目标价。",
            all_ids[:3],
        )
        if valuation_claim:
            claims.append(valuation_claim)

    conclusion_status = "supported" if claims and all(claim["evidence_ids"] for claim in claims) else "cannot_conclude"
    if conclusion_status == "supported":
        scenario_ids = all_ids[:5]
        scenarios = [
            {
                "scenario": "bull",
                "judgment": "乐观情景要求已引用的经营动能持续，并且现金转化能力改善。",
                "evidence_ids": scenario_ids,
            },
            {
                "scenario": "base",
                "judgment": "基准情景仅假设现有证据继续有效，不外推至披露期之外。",
                "evidence_ids": scenario_ids,
            },
            {
                "scenario": "bear",
                "judgment": "如果后续官方披露显示增长或现金流证据发生逆转，则进入谨慎情景。",
                "evidence_ids": scenario_ids,
            },
        ]
    else:
        scenarios = [
            {"scenario": name, "judgment": "当前证据不足，暂时无法判断。", "evidence_ids": []}
            for name in ("bull", "base", "bear")
        ]

    summary = {
        "ticker": ticker,
        "market": context.state["market"],
        "conclusion_status": conclusion_status,
        "evidence_count": len(evidence_items),
        "evidence_ids": all_ids,
        "claims": claims,
        "scenarios": scenarios,
        "freshness": context.state["freshness"],
        "risk": _risk_summary(context.state["risk"].get("alerts") or []),
    }
    context.state["summary"] = summary
    message = "Evidence-backed scenarios built" if conclusion_status == "supported" else "Insufficient evidence; cannot conclude"
    return StageResult.completed(message, summary)


def _render_markdown(summary: dict[str, Any]) -> str:
    conclusion_labels = {"supported": "证据支持", "cannot_conclude": "暂无法判断"}
    market_labels = {"A": "A 股", "H": "港股", "US": "美股"}
    freshness_labels = {
        "current": "当前有效", "fresh": "新鲜", "unknown": "待检测",
        "not_configured": "未配置", "stale": "已过期", "missing": "缺失",
        "market_closed": "市场休市", "source_not_due": "未到更新时间",
        "fetch_failed": "获取失败", "data_stale": "数据过期",
    }
    claim_labels = {
        "business_evidence": "业务证据",
        "fundamentals": "基本面",
        "valuation_context": "估值背景",
    }
    scenario_labels = {"bull": "乐观情景", "base": "基准情景", "bear": "谨慎情景"}
    freshness = summary["freshness"]
    lines = [
        f"# 个股深挖报告 — {summary['ticker']}",
        "",
        f"- 市场：{market_labels.get(summary['market'], summary['market'])}",
        f"- 结论状态：**{conclusion_labels.get(summary['conclusion_status'], summary['conclusion_status'])}**",
        f"- 证据数量：{summary['evidence_count']}",
        f"- 数据新鲜度：{freshness_labels.get(freshness.get('condition'), freshness.get('condition'))} / {freshness_labels.get(freshness.get('status'), freshness.get('status'))}",
        "",
        "## 有证据支撑的判断",
        "",
    ]
    if not summary["claims"]:
        lines.append("- 暂无法判断：当前没有核心观点具备足够的可追溯证据。")
    for claim in summary["claims"]:
        citations = ", ".join(f"[{evidence_id}]" for evidence_id in claim["evidence_ids"])
        label = claim_labels.get(claim["claim_type"], "研究判断")
        lines.append(f"- **{label}**：{claim['text']} {citations}")
    lines.extend(["", "## 三种情景", ""])
    for scenario in summary["scenarios"]:
        label = scenario_labels.get(scenario["scenario"], "研究情景")
        citations = ", ".join(f"[{evidence_id}]" for evidence_id in scenario["evidence_ids"])
        lines.append(f"### {label}")
        lines.append("")
        lines.append(f"{scenario['judgment']} {citations}".rstrip())
        lines.append("")
    lines.extend(
        [
            "## 风险与边界",
            "",
            "本报告仅用于本地研究辅助，不会执行交易，也不构成自动投资建议。",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_outputs_stage(artifact_root: Path):
    def handler(context: WorkflowContext) -> StageResult:
        summary = dict(context.state["summary"])
        run_dir = artifact_root.resolve() / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "stock_deep_dive.md"
        report_path.write_text(_render_markdown(summary), encoding="utf-8")

        conn = sqlite3.connect(context.db_path)
        try:
            artifact = ArtifactStore(conn, [artifact_root]).register_artifact(
                context.run_id,
                "stock_deep_dive_report",
                f"个股深挖报告 — {summary['ticker']}",
                report_path,
                "text/markdown",
                metadata={
                    "ticker": summary["ticker"],
                    "conclusion_status": summary["conclusion_status"],
                },
            )
            memory_id = None
            if summary["conclusion_status"] == "supported":
                candidate = create_memory_candidate(
                    conn,
                    entity_type="ticker",
                    entity_id=summary["ticker"],
                    memory_type="investment_thesis",
                    content={
                        "claims": summary["claims"],
                        "scenarios": summary["scenarios"],
                        "freshness": summary["freshness"],
                    },
                    evidence_links=[
                        {"evidence_id": evidence_id, "relation": "supports"}
                        for evidence_id in summary["evidence_ids"]
                    ],
                    confidence=0.7,
                    source_run_id=context.run_id,
                )
                memory_id = candidate["memory_id"]
        finally:
            conn.close()

        summary.update(
            {
                "artifact_ids": [artifact["artifact_id"]],
                "memory_candidate_id": memory_id,
            }
        )
        context.state["summary"] = summary
        return StageResult.completed(
            "Research report and governed candidate persisted",
            summary,
            artifacts=(artifact,),
        )

    return handler


def stock_deep_dive_definition(
    *,
    artifact_root: str | Path | None = None,
    source_db_path: str | Path | None = None,
) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    source = Path(source_db_path) if source_db_path is not None else None
    return WorkflowDefinition(
        workflow_id="stock_deep_dive",
        title="Stock deep dive",
        description="Build an evidence-backed local company research report.",
        input_schema={
            "type": "object",
            "required": ["ticker"],
            "properties": {
                "ticker": {"type": "string"},
                "allow_network": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate_input, "Validate ticker"),
            StageDefinition("load_context", _load_context_stage(source), "Load local context"),
            StageDefinition("build_analysis", _build_analysis, "Build cited scenarios"),
            StageDefinition("write_outputs", _write_outputs_stage(root), "Persist report and memory candidate"),
        ),
    )
