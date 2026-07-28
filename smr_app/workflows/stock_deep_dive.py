from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from smr_app.acquisition.contracts import AcquisitionMode, AcquisitionProvider, AcquisitionResult
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.providers import (
    default_research_providers,
)
from smr_app.acquisition.store import AcquisitionStore
from smr_app.adapters.evidence import EvidenceRequest, load_evidence
from smr_app.adapters.fundamentals import FundamentalsRequest, load_fundamentals
from smr_app.adapters.memory import create_memory_candidate
from smr_app.adapters.risk import RiskContextRequest, load_risk_context
from smr_app.adapters.research_context_v3 import (
    assemble_stock_research_context,
    collect_stock_industry_graph,
    collect_stock_instruments,
    collect_stock_memory,
    collect_stock_news_events,
    collect_stock_official_corpus,
    provider_status,
    resolve_stock_research_identity,
)
from smr_app.adapters.valuation import ValuationRequest, load_valuation
from smr_app.research.analysis_v3 import (
    assemble_stock_analysis_v3,
    build_business_industry_analysis,
    build_catalyst_risk_analysis,
    build_financial_analysis,
    build_market_peer_analysis,
)
from smr_app.research.acquisition_materializer_v3 import materialize_acquired_stock_data
from smr_app.research.claim_compiler import compile_stock_claims
from smr_app.research.data_requirements_v3 import (
    build_stock_data_requirement_manifest,
    evaluate_cached_requirements,
    requirement_from_manifest_item,
    validate_acquisition_results,
)
from smr_app.research.normalization import normalize_research_data
from smr_app.research.quality_gate import evaluate_stock_research_quality
from smr_app.research.report_v3 import (
    compile_stock_research_report_v3,
    evaluate_v3_report_eligibility,
    validate_stock_research_report_v3,
)
from smr_app.research.report_compiler import compile_stock_research_report, validate_stock_research_report
from smr_app.research.research_plan_v3 import build_stock_research_plan
from smr_app.research.stock_packet import build_stock_research_packet
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
    allow_network = context.input_data.get("allow_network")
    if allow_network is not None and not isinstance(allow_network, bool):
        raise ValueError("allow_network must be a boolean")
    raw_mode = context.input_data.get("acquisition_mode")
    if raw_mode is not None:
        try:
            mode = AcquisitionMode(str(raw_mode))
        except ValueError as exc:
            raise ValueError("acquisition_mode must be cache_only, refresh_if_stale, or force_refresh") from exc
    elif allow_network is False:
        mode = AcquisitionMode.CACHE_ONLY
    else:
        mode = AcquisitionMode.REFRESH_IF_STALE
    context.state.update({
        "ticker": ticker,
        "market": market,
        "allow_network": mode is not AcquisitionMode.CACHE_ONLY,
        "acquisition_mode": mode.value,
    })
    return StageResult.completed(
        "Ticker and acquisition mode validated",
        {"ticker": ticker, "market": market, "acquisition_mode": mode.value},
    )


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


def _build_research_plan_v3_stage(context: WorkflowContext) -> StageResult:
    plan = build_stock_research_plan(context.state["ticker"], context.state["market"])
    context.state["research_plan_v3"] = plan
    return StageResult.completed(
        "V3 research plan built",
        {"section_count": len(plan["sections"]), "question_count": len(plan["questions"])},
    )


def _build_data_requirements_stage(context: WorkflowContext) -> StageResult:
    manifest = build_stock_data_requirement_manifest(
        context.state["ticker"],
        context.state["market"],
        context.state["research_plan_v3"],
    )
    context.state["data_requirement_manifest_v3"] = manifest
    return StageResult.completed(
        "Research data requirement manifest built",
        {
            "requirement_count": len(manifest["requirements"]),
            "critical_requirements": sum(1 for item in manifest["requirements"] if item["critical"]),
            "acquisition_mode": context.state["acquisition_mode"],
        },
    )


def _with_source_connections(context: WorkflowContext, source_db_path: Path | None):
    return _connect_source(context, source_db_path), sqlite3.connect(context.db_path)


def _check_provider_health_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        source_conn, control_conn = _with_source_connections(context, source_db_path)
        try:
            health = provider_status(source_conn, control_conn)
        finally:
            control_conn.close()
            source_conn.close()
        context.state["provider_health_v3"] = health
        return StageResult.completed(
            "Research data providers checked",
            {"provider_status": health},
        )
    return handler


def _retrieve_official_filings_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        conn = _connect_source(context, source_db_path)
        try:
            identity = resolve_stock_research_identity(
                conn, ticker=context.state["ticker"], market=context.state["market"]
            )
            corpus = collect_stock_official_corpus(conn, ticker=context.state["ticker"])
        finally:
            conn.close()
        context.state["research_identity_v3"] = identity
        context.state["official_corpus_v3"] = corpus
        return StageResult.completed("Official filings and research corpus retrieved", {
            "filing_count": len(corpus["filings"]),
            "chunk_count": len(corpus["chunks"]),
            "broker_report_count": len(corpus["broker_reports"]),
        })
    return handler


def _retrieve_memory_stage(context: WorkflowContext) -> StageResult:
    conn = sqlite3.connect(context.db_path)
    try:
        memories = collect_stock_memory(conn, ticker=context.state["ticker"])
    finally:
        conn.close()
    context.state["research_memories_v3"] = memories
    return StageResult.completed("Historical research memory retrieved", {"memory_count": len(memories)})


def _retrieve_news_events_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        conn = _connect_source(context, source_db_path)
        try:
            result = collect_stock_news_events(conn, ticker=context.state["ticker"])
        finally:
            conn.close()
        context.state["news_events_v3"] = result
        return StageResult.completed("News, catalysts and risk events retrieved", {
            "news_count": len(result["news"]), "event_count": len(result["events"]),
        })
    return handler


def _retrieve_industry_graph_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        conn = _connect_source(context, source_db_path)
        try:
            graph = collect_stock_industry_graph(conn, identity=context.state["research_identity_v3"])
        finally:
            conn.close()
        context.state["industry_graph_v3"] = graph
        return StageResult.completed("Industry graph and peer universe selected", {
            "peer_count": len(graph.get("peers") or []),
            "benchmark_count": len(graph.get("us_benchmarks") or []),
        })
    return handler


def _retrieve_instruments_stage(source_db_path: Path | None):
    def handler(context: WorkflowContext) -> StageResult:
        conn = _connect_source(context, source_db_path)
        try:
            instruments = collect_stock_instruments(
                conn, ticker=context.state["ticker"], graph=context.state["industry_graph_v3"]
            )
        finally:
            conn.close()
        context.state["research_instruments_v3"] = instruments
        return StageResult.completed("Target and peer instruments retrieved", {
            "target_bar_count": len(instruments["target"].get("daily_bars") or []),
            "peer_count": len(instruments["peers"]),
        })
    return handler


def _assemble_research_context_stage(context: WorkflowContext) -> StageResult:
    research_context = assemble_stock_research_context(
        provider_health=context.state["provider_health_v3"],
        identity=context.state["research_identity_v3"],
        official_corpus=context.state["official_corpus_v3"],
        memories=context.state["research_memories_v3"],
        news_events=context.state["news_events_v3"],
        graph=context.state["industry_graph_v3"],
        instruments=context.state["research_instruments_v3"],
    )
    context.state["research_context_v3"] = research_context
    corpus = research_context["corpus"]
    return StageResult.completed("Research context assembled", {
        "document_count": len(corpus["filings"]),
        "research_chunk_count": len(corpus["chunks"]),
        "context_item_count": len(corpus["news"]) + len(corpus["events"]) + len(corpus["memories"]),
    })


def _evaluate_cached_requirements_stage(context: WorkflowContext) -> StageResult:
    evaluation = evaluate_cached_requirements(
        context.state["data_requirement_manifest_v3"],
        AcquisitionStore(context.db_path),
        context.state["research_context_v3"],
        {
            "fundamentals": context.state.get("fundamentals") or {},
            "valuation": context.state.get("valuation") or {},
            "evidence": context.state.get("evidence") or {},
            "risk": context.state.get("risk") or {},
        },
    )
    context.state["cache_evaluation_v3"] = evaluation
    return StageResult.completed(
        "Local research cache evaluated",
        {
            "fresh_requirements": evaluation["fresh_requirements"],
            "usable_requirements": evaluation["usable_requirements"],
            "refresh_required": evaluation["refresh_required"],
        },
    )


def _acquisition_result_payload(result: AcquisitionResult) -> dict[str, Any]:
    return {
        "request_id": result.request_id,
        "status": result.status,
        "provider_id": result.provider_id,
        "persisted_documents": result.persisted_documents,
        "persisted_facts": result.persisted_facts,
        "persisted_evidence_candidates": result.persisted_evidence_candidates,
        "dataset_state": asdict(result.dataset_state) if result.dataset_state else None,
        "errors": [dict(item) for item in result.errors],
    }


def _acquire_missing_requirements_stage(providers: tuple[AcquisitionProvider, ...]):
    def handler(context: WorkflowContext) -> StageResult:
        kernel = AcquisitionKernel(AcquisitionStore(context.db_path), providers)
        mode = AcquisitionMode(context.state["acquisition_mode"])
        results: dict[str, dict[str, Any]] = {}
        attempts = 0
        for item in context.state["cache_evaluation_v3"]["items"]:
            if not item["refresh_needed"]:
                continue
            attempts += 1
            result = kernel.acquire(
                requirement_from_manifest_item(item),
                mode=mode,
                workflow_run_id=context.run_id,
            )
            results[str(item["requirement_id"])] = _acquisition_result_payload(result)
        context.state["acquisition_results_v3"] = results
        return StageResult.completed(
            "Missing or stale research datasets processed",
            {
                "mode": mode.value,
                "attempted_requirements": attempts,
                "acquired_requirements": sum(
                    1 for result in results.values() if result["status"] in {"acquired", "cache_hit"}
                ),
                "failed_requirements": sum(
                    1 for result in results.values() if result["status"] in {"failed", "cache_miss"}
                ),
            },
        )
    return handler


def _validate_acquired_data_stage(context: WorkflowContext) -> StageResult:
    validation = validate_acquisition_results(
        context.state["cache_evaluation_v3"],
        context.state.get("acquisition_results_v3") or {},
    )
    context.state["acquisition_validation_v3"] = validation
    return StageResult.completed(
        "Acquired research datasets validated",
        {
            "status": validation["status"],
            "total_requirements": validation["total_requirements"],
            "usable_requirements": validation["usable_requirements"],
            "unresolved_requirements": validation["unresolved_requirements"],
            "critical_unusable": validation["critical_unusable"],
        },
    )


def _materialize_acquired_data_stage(context: WorkflowContext) -> StageResult:
    result = materialize_acquired_stock_data(
        AcquisitionStore(context.db_path),
        ticker=context.state["ticker"],
        fundamentals=context.state["fundamentals"],
        valuation=context.state["valuation"],
        evidence=context.state["evidence"],
        research_context=context.state["research_context_v3"],
        freshness=context.state["freshness"],
    )
    context.state["acquisition_materialization_v3"] = result
    return StageResult.completed("Verified acquired data materialized into the V3 research context", result)


def _normalize_research_data_stage(context: WorkflowContext) -> StageResult:
    normalized = normalize_research_data(
        market=context.state["market"],
        fundamentals=context.state.get("fundamentals"),
        valuation=context.state.get("valuation"),
        evidence=context.state.get("evidence"),
        risk=context.state.get("risk"),
        freshness=context.state.get("freshness"),
    )
    context.state["normalized_research_data"] = normalized
    return StageResult.completed(
        "Research data normalized and inconsistent fields quarantined",
        {
            "fundamentals_status": normalized["fundamentals"]["status"],
            "valuation_status": normalized["valuation"]["status"],
            "evidence_status": normalized["evidence"]["status"],
            "quarantined_fields": [
                *normalized["fundamentals"].get("quarantined_fields", []),
                *normalized["valuation"].get("quarantined_fields", []),
            ],
        },
    )


def _build_research_packet_stage(context: WorkflowContext) -> StageResult:
    packet = build_stock_research_packet(
        ticker=context.state["ticker"],
        market=context.state["market"],
        normalized=context.state["normalized_research_data"],
    )
    packet["workflow_version"] = "3.0"
    packet["research_v3"] = {
        "provider_status": context.state["research_context_v3"]["provider_status"],
        "plan": context.state["research_plan_v3"],
        "context": context.state["research_context_v3"],
        "analysis": {},
        "report_quality": {},
        "acquisition": {
            "mode": context.state["acquisition_mode"],
            "manifest": context.state["data_requirement_manifest_v3"],
            "cache_evaluation": context.state["cache_evaluation_v3"],
            "results": context.state.get("acquisition_results_v3") or {},
            "validation": context.state["acquisition_validation_v3"],
        },
    }
    context.state["research_packet"] = packet
    return StageResult.completed(
        "Research Packet v2 built",
        {
            "schema_version": packet["schema_version"],
            "readiness": packet["quality"]["readiness"],
            "blockers": packet["quality"]["blockers"],
            "usable_evidence_count": len(packet["quality"]["usable_evidence_ids"]),
            "quarantined_field_count": len(packet["quality"]["quarantined_fields"]),
        },
    )


def _analyze_market_peers_stage(context: WorkflowContext) -> StageResult:
    result = build_market_peer_analysis(context.state["research_context_v3"])
    context.state["market_peers_analysis_v3"] = result
    return StageResult.completed("Market, valuation and peer analysis completed", {
        "market_as_of": result["market"].get("as_of"), "peer_count": len(result["peers"]),
    })


def _analyze_financials_stage(context: WorkflowContext) -> StageResult:
    result = build_financial_analysis(
        context.state["research_context_v3"], context.state["market_peers_analysis_v3"]["market"]
    )
    context.state["financial_analysis_v3"] = result
    return StageResult.completed("Financial trends and cash-flow analysis completed", {
        "annual_financials": result["annual_financials"]["status"],
        "operating_metrics": result["operating_metrics"]["status"],
        "insight_count": len(result["insights"]),
    })


def _analyze_business_industry_stage(context: WorkflowContext) -> StageResult:
    result = build_business_industry_analysis(context.state["research_context_v3"])
    context.state["business_industry_analysis_v3"] = result
    return StageResult.completed("Business, industry and competitiveness analysis completed", {
        "topic_count": len(result["topic_counts"]), "evidence_count": len(result["evidence_ids"]),
    })


def _analyze_catalysts_risks_stage(context: WorkflowContext) -> StageResult:
    result = build_catalyst_risk_analysis(context.state["research_context_v3"])
    context.state["catalyst_risk_analysis_v3"] = result
    return StageResult.completed("Catalysts, risks and falsification inputs analyzed", {
        "news_count": result["news_count"], "event_count": result["event_count"],
        "risk_source_count": result["risk_source_count"],
    })


def _assemble_analysis_v3_stage(context: WorkflowContext) -> StageResult:
    packet = context.state["research_packet"]
    analysis = assemble_stock_analysis_v3(
        context.state["research_context_v3"],
        context.state["research_plan_v3"],
        market_peers=context.state["market_peers_analysis_v3"],
        financials=context.state["financial_analysis_v3"],
        business_industry=context.state["business_industry_analysis_v3"],
        catalysts_risks=context.state["catalyst_risk_analysis_v3"],
    )
    packet["research_v3"]["analysis"] = analysis
    context.state["analysis_v3"] = analysis
    return StageResult.completed(
        "V3 chapter analyses assembled",
        {
            "annual_financials": analysis["annual_financials"]["status"],
            "operating_metrics": analysis["operating_metrics"]["status"],
            "coverage": analysis["coverage"]["score"],
            "insight_count": len(analysis["insights"]),
            "peer_count": len(analysis["peers"]),
        },
    )


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
                "alert_id": alert.get("alert_id"),
                "alert_type": alert.get("alert_type"),
                "severity": alert.get("severity"),
                "evidence_status": "cited" if alert.get("evidence_ids") else "context_only",
            }
            for alert in alerts[:5]
        ],
    }


def _compile_claims_stage(context: WorkflowContext) -> StageResult:
    packet = context.state["research_packet"]
    compiled = compile_stock_claims(packet)
    packet["claims"] = compiled["claims"]
    packet["scenarios"] = compiled["scenarios"]
    packet["research_questions"] = compiled["research_questions"]
    context.state["compiled_research"] = compiled
    return StageResult.completed(
        "Deterministic claims and scenarios compiled",
        {
            "claim_count": len(compiled["claims"]),
            "scenario_count": len(compiled["scenarios"]),
            "research_question_count": len(compiled["research_questions"]),
            "conclusion_status": compiled["conclusion_status"],
        },
    )


def _quality_gate_stage(context: WorkflowContext) -> StageResult:
    packet = context.state["research_packet"]
    gate = evaluate_stock_research_quality(packet)
    packet["claims"] = gate["approved_claims"]
    packet["scenarios"] = gate["approved_scenarios"]
    packet["quality"]["report_gate"] = {
        key: value
        for key, value in gate.items()
        if key not in {"approved_claims", "approved_scenarios", "rejected_claims", "rejected_scenarios"}
    }
    packet["quality"]["rejected_claims"] = gate["rejected_claims"]
    packet["quality"]["rejected_scenarios"] = gate["rejected_scenarios"]
    evidence_ids = list(dict.fromkeys(
        evidence_id
        for claim in gate["approved_claims"]
        for evidence_id in claim.get("evidence_ids") or []
    ))
    compiled = context.state["compiled_research"]
    conclusion_status = (
        "supported"
        if compiled["conclusion_status"] == "supported" and gate["report_status"] == "research_ready"
        else "cannot_conclude"
    )
    summary = {
        "ticker": context.state["ticker"],
        "market": context.state["market"],
        "conclusion_status": conclusion_status,
        "evidence_count": len(packet["datasets"]["evidence"].get("items") or []),
        "evidence_ids": evidence_ids,
        "claims": gate["approved_claims"],
        "scenarios": gate["approved_scenarios"],
        "research_questions": packet.get("research_questions") or [],
        "freshness": context.state["freshness"],
        "risk": _risk_summary(packet["datasets"]["risk"].get("alerts") or []),
        "research_readiness": gate["report_status"],
        "data_quality": packet["quality"],
        "evidence_gaps": packet["evidence_gaps"],
        "quality_gate": gate,
    }
    context.state["quality_gate"] = gate
    context.state["summary"] = summary
    return StageResult.completed(
        "Research quality gate evaluated",
        {
            "report_status": gate["report_status"],
            "approved_claim_count": len(gate["approved_claims"]),
            "rejected_claim_count": len(gate["rejected_claims"]),
            "citation_coverage": gate["citation_coverage"],
        },
    )


def _draft_report_stage(context: WorkflowContext) -> StageResult:
    packet = context.state["research_packet"]
    corpus = packet.get("research_v3", {}).get("context", {}).get("corpus", {})
    has_v3_corpus = bool(corpus.get("chunks") or corpus.get("broker_reports"))
    is_v3 = packet.get("workflow_version") == "3.0"
    if is_v3 and has_v3_corpus:
        eligibility = evaluate_v3_report_eligibility(packet)
        packet["research_v3"]["report_quality"]["eligibility"] = eligibility
        if not eligibility["eligible"]:
            raise RuntimeError(
                "deep research evidence floor not met; no report generated: "
                + ", ".join(eligibility["missing"])
            )
    elif is_v3 and context.state["quality_gate"]["report_status"] != "research_ready":
        raise RuntimeError(
            "deep research evidence floor not met; no report generated: "
            "no eligible official research evidence"
        )
    if is_v3 and has_v3_corpus:
        report = compile_stock_research_report_v3(packet)
        compiler = "v3"
    else:
        report = compile_stock_research_report(packet, context.state["quality_gate"])
        compiler = "governed_fallback"
    context.state["governed_report_draft"] = report
    context.state["has_v3_corpus"] = has_v3_corpus
    return StageResult.completed("Governed research draft generated", {
        "compiler": compiler, "characters": len(report),
    })


def _validate_report_stage(context: WorkflowContext) -> StageResult:
    packet = context.state["research_packet"]
    report = context.state["governed_report_draft"]
    if packet.get("workflow_version") == "3.0" and context.state["has_v3_corpus"]:
        report_validation = validate_stock_research_report_v3(report, packet)
    else:
        report_validation = validate_stock_research_report(report, packet, context.state["quality_gate"])
    if report_validation["status"] != "passed":
        raise RuntimeError(f"stock research report failed final validation: {report_validation['errors']}")
    packet["quality"]["report_validation"] = report_validation
    packet["research_v3"]["report_quality"]["governed_draft"] = report_validation
    context.state["governed_report_validation"] = report_validation
    return StageResult.completed("Governed draft structure, facts and citations validated", {
        "status": report_validation["status"],
        "characters": report_validation.get("characters", len(report)),
        "section_count": report_validation.get("section_count"),
    })


def _persist_outputs_stage(artifact_root: Path):
    def handler(context: WorkflowContext) -> StageResult:
        summary = dict(context.state["summary"])
        run_dir = artifact_root.resolve() / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "stock_deep_dive.md"
        packet = context.state["research_packet"]
        has_v3_corpus = context.state["has_v3_corpus"]
        report = context.state["governed_report_draft"]
        report_validation = context.state["governed_report_validation"]
        report_path.write_text(report, encoding="utf-8")
        packet_path = run_dir / "research_packet.json"
        packet_path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        audit_path = run_dir / "research_audit.json"
        audit = {
            "workflow_version": "3.0",
            "ticker": summary["ticker"],
            "provider_status": packet["research_v3"]["provider_status"],
            "plan": packet["research_v3"]["plan"],
            "coverage": packet["research_v3"]["analysis"]["coverage"],
            "governed_quality_gate": packet["quality"].get("report_gate"),
            "report_validation": report_validation,
        }
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

        conn = sqlite3.connect(context.db_path)
        try:
            store = ArtifactStore(conn, [artifact_root])
            artifact = store.register_artifact(
                context.run_id,
                "stock_deep_dive_report",
                f"个股深度研究 V3 — {summary['ticker']}",
                report_path,
                "text/markdown",
                metadata={
                    "ticker": summary["ticker"],
                    "conclusion_status": summary["conclusion_status"],
                },
            )
            packet_artifact = store.register_artifact(
                context.run_id,
                "stock_research_packet_v2",
                f"Research Packet V3 — {summary['ticker']}",
                packet_path,
                "application/json",
                metadata={
                    "ticker": summary["ticker"],
                    "schema_version": context.state["research_packet"]["schema_version"],
                    "readiness": summary["research_readiness"],
                },
            )
            audit_artifact = None
            if has_v3_corpus:
                audit_artifact = store.register_artifact(
                    context.run_id,
                    "stock_deep_dive_audit",
                    f"研究过程与质量审计 — {summary['ticker']}",
                    audit_path,
                    "application/json",
                    metadata={
                        "ticker": summary["ticker"],
                        "workflow_version": "3.0",
                        "coverage": packet["research_v3"]["analysis"]["coverage"]["score"],
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

        registered_artifacts = [artifact, packet_artifact, *([audit_artifact] if audit_artifact else [])]
        summary.update(
            {
                "artifact_ids": [item["artifact_id"] for item in registered_artifacts],
                "memory_candidate_id": memory_id,
                "workflow_version": "3.0",
                "research_coverage": packet["research_v3"]["analysis"]["coverage"]["score"],
            }
        )
        context.state["summary"] = summary
        return StageResult.completed(
            "Research report and governed candidate persisted",
            summary,
            artifacts=tuple(registered_artifacts),
        )

    return handler


def stock_deep_dive_definition(
    *,
    artifact_root: str | Path | None = None,
    source_db_path: str | Path | None = None,
    acquisition_providers: Iterable[AcquisitionProvider] | None = None,
) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    configured_source = source_db_path or os.environ.get("SMR_SOURCE_DB_PATH")
    source = Path(configured_source) if configured_source else None
    providers = (
        tuple(acquisition_providers)
        if acquisition_providers is not None
        else default_research_providers()
    )
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
                "acquisition_mode": {
                    "type": "string",
                    "enum": ["cache_only", "refresh_if_stale", "force_refresh"],
                    "default": "refresh_if_stale",
                },
            },
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate_input, "Validate ticker"),
            StageDefinition("build_research_plan", _build_research_plan_v3_stage, "Build V3 research plan"),
            StageDefinition("build_data_requirements", _build_data_requirements_stage, "Build data requirement manifest"),
            StageDefinition("check_provider_health", _check_provider_health_stage(source), "Check data provider health"),
            StageDefinition("load_structured_data", _load_context_stage(source), "Load structured financial and risk data"),
            StageDefinition("retrieve_official_filings", _retrieve_official_filings_stage(source), "Retrieve official filings and research corpus"),
            StageDefinition("retrieve_memory", _retrieve_memory_stage, "Retrieve historical research memory"),
            StageDefinition("retrieve_news_events", _retrieve_news_events_stage(source), "Retrieve news, catalysts and risk events"),
            StageDefinition("retrieve_industry_graph", _retrieve_industry_graph_stage(source), "Load industry graph and peer universe"),
            StageDefinition("retrieve_instruments", _retrieve_instruments_stage(source), "Retrieve target and peer instruments"),
            StageDefinition("assemble_research_context", _assemble_research_context_stage, "Assemble research context"),
            StageDefinition("evaluate_cached_requirements", _evaluate_cached_requirements_stage, "Evaluate local research cache"),
            StageDefinition("acquire_missing_requirements", _acquire_missing_requirements_stage(providers), "Acquire missing research data"),
            StageDefinition("validate_acquired_data", _validate_acquired_data_stage, "Validate acquired research data"),
            StageDefinition("materialize_acquired_data", _materialize_acquired_data_stage, "Materialize verified acquired data"),
            StageDefinition("normalize_research_data", _normalize_research_data_stage, "Normalize and quarantine research data"),
            StageDefinition("build_research_packet", _build_research_packet_stage, "Build Research Packet v2"),
            StageDefinition("analyze_market_peers", _analyze_market_peers_stage, "Analyze market, valuation and peers"),
            StageDefinition("analyze_financials", _analyze_financials_stage, "Analyze financial trends and cash flow"),
            StageDefinition("analyze_business_industry", _analyze_business_industry_stage, "Analyze business, industry and competitiveness"),
            StageDefinition("analyze_catalysts_risks", _analyze_catalysts_risks_stage, "Analyze catalysts, risks and falsification conditions"),
            StageDefinition("assemble_analysis", _assemble_analysis_v3_stage, "Assemble chapter analyses"),
            StageDefinition("compile_claims", _compile_claims_stage, "Compile deterministic cited claims"),
            StageDefinition("quality_gate", _quality_gate_stage, "Enforce research report quality"),
            StageDefinition("draft_report", _draft_report_stage, "Generate governed research draft"),
            StageDefinition("validate_report", _validate_report_stage, "Validate report structure, facts and citations"),
            StageDefinition("persist_outputs", _persist_outputs_stage(root), "Persist report, packet, audit and memory candidate"),
        ),
    )
