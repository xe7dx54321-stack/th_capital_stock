from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from smr_app.acquisition.store import AcquisitionStore
from smr_app.research.analysis_v3 import extract_operating_metrics


FACT_TO_SNAPSHOT = {
    "revenue": "revenue",
    "net_profit_parent": "net_income",
    "operating_cash_flow": "operating_cash_flow",
    "eps": "eps_basic",
    "weighted_roe": "roe",
    "attributable_equity": "shareholders_equity",
    "gross_margin": "gross_margin",
}

ACQUIRED_DATA_TYPES = (
    "official_filings",
    "financial_statements",
    "daily_bars",
    "realtime_quote",
    "valuation_snapshot",
    "peer_comparison",
)


def _latest_verified_facts(store: AcquisitionStore, ticker: str) -> tuple[str | None, list[dict[str, Any]]]:
    facts = [
        item for item in store.list_facts(ticker, "financial_statements")
        if item.get("verification_status") == "verified" and item.get("as_of")
    ]
    latest = max((str(item["as_of"]) for item in facts), default=None)
    return latest, [item for item in facts if str(item.get("as_of")) == latest]


def _candidate_by_fact(candidates: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("metadata", {}).get("fact_id")): str(item["candidate_id"])
        for item in candidates
        if item.get("metadata", {}).get("fact_id") and item.get("candidate_id")
    }


def _financial_snapshot(
    store: AcquisitionStore,
    ticker: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any] | None:
    latest, facts = _latest_verified_facts(store, ticker)
    if not latest or not facts:
        return None
    by_field = {str(item["field_name"]): item for item in facts}
    all_facts = [
        item for item in store.list_facts(ticker, "financial_statements")
        if item.get("verification_status") == "verified"
    ]
    history: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in all_facts:
        history[str(item["field_name"])].append(item)
    for rows in history.values():
        rows.sort(key=lambda item: str(item.get("as_of") or ""), reverse=True)
    evidence_by_fact = _candidate_by_fact(candidates)
    snapshot: dict[str, Any] = {
        "ticker": ticker,
        "period": latest[:4],
        "created_at": latest,
        "confidence": 0.99,
        "source_quality": "official",
        "metadata": {"currency": "CNY", "materialized_from": "acquisition_store"},
        "field_details": {},
    }
    for fact_name, snapshot_name in FACT_TO_SNAPSHOT.items():
        fact = by_field.get(fact_name)
        if not fact:
            continue
        rows = history[fact_name]
        previous = next((row for row in rows if str(row.get("as_of") or "") < latest), None)
        evidence_id = evidence_by_fact.get(str(fact["fact_id"]))
        snapshot[snapshot_name] = fact["value"]
        snapshot["field_details"][snapshot_name] = {
            "period": latest[:4],
            "source_evidence_ids": [evidence_id] if evidence_id else [],
            "confidence": fact.get("confidence"),
            "allowed_usage": "research",
            "normalized_unit": fact.get("unit"),
            "previous_value": previous.get("value") if previous else None,
            "previous_period": str(previous.get("as_of") or "")[:4] if previous else None,
            "source_document_id": fact.get("source_document_id"),
        }
    if snapshot.get("gross_margin") is None:
        documents = store.list_documents(ticker, "financial_statements")
        annual_document = next(
            (
                item for item in documents
                if item.get("source_type") == "annual_report" and item.get("raw_text")
            ),
            None,
        )
        if annual_document:
            operating = extract_operating_metrics([{
                "chunk_id": annual_document.get("document_id"),
                "evidence_id": None,
                "chunk_section_type": "operating_results",
                "text": annual_document.get("raw_text"),
            }])
            gross_margin = operating.get("current_gross_margin")
            if gross_margin is not None:
                evidence_id = next(
                    (
                        str(item["candidate_id"])
                        for item in candidates
                        if item.get("candidate_id")
                        and str(annual_document.get("document_id")) in {
                            str(value) for value in item.get("source_document_ids") or []
                        }
                    ),
                    None,
                )
                snapshot["gross_margin"] = gross_margin
                snapshot["field_details"]["gross_margin"] = {
                    "period": latest[:4],
                    "source_evidence_ids": [evidence_id] if evidence_id else [],
                    "confidence": 0.99,
                    "allowed_usage": "research",
                    "normalized_unit": "ratio",
                    "previous_value": operating.get("previous_gross_margin"),
                    "previous_period": str(int(latest[:4]) - 1),
                    "source_document_id": annual_document.get("document_id"),
                    "materialization_method": "annual_main_business_product_table",
                }
    return snapshot


def _evidence_items(
    candidates: list[dict[str, Any]], documents: Mapping[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    output = []
    for candidate in candidates:
        if candidate.get("status") != "validated":
            continue
        document_ids = list(candidate.get("source_document_ids") or [])
        document = next((documents.get(str(value)) for value in document_ids if documents.get(str(value))), {})
        authority = str(candidate.get("authority_tier") or document.get("authority_tier") or "discovery")
        source_type = str(document.get("source_type") or "acquired_source")
        output.append({
            "evidence_id": candidate["candidate_id"],
            "source_key": document.get("source_id") or "cninfo_official",
            "source_type": source_type,
            "source_quality": authority,
            "source_status": "active",
            "published_at": candidate.get("occurred_at") or document.get("published_at"),
            "ingested_at": candidate.get("created_at"),
            "text_excerpt": candidate.get("text"),
            "url_or_doc_id": document.get("source_url") or document.get("document_id"),
            "quality_score": 0.98,
            "usable_for_core_claim": True,
            "metadata": {
                "ticker": candidate.get("entity_key"),
                "claim_category": candidate.get("claim_type"),
                "title": document.get("title"),
            },
        })
    return output


def _slice(text: str, marker: str, *, before: int = 800, after: int = 18_000) -> str | None:
    index = text.find(marker)
    if index < 0:
        return None
    return text[max(0, index - before): index + after].strip()


def _section_slice(
    text: str,
    markers: tuple[str, ...],
    *,
    anchors: tuple[str, ...] = (),
    stop_markers: tuple[str, ...] = (),
    before: int = 80,
    max_chars: int = 12_000,
) -> str | None:
    """Return the most content-rich occurrence of an annual-report section.

    PDF text normally contains both a table-of-contents occurrence and the real
    section.  Picking the first marker silently materializes the TOC plus an
    unrelated block.  Rank every occurrence by nearby section anchors and then
    cut at the next section marker so downstream synthesis receives a focused
    company-specific excerpt.
    """
    candidates: list[tuple[int, int]] = []
    for marker in markers:
        offset = 0
        while True:
            index = text.find(marker, offset)
            if index < 0:
                break
            preview = text[index:index + min(max_chars, 6_000)]
            anchor_score = sum(1 for anchor in anchors if anchor in preview)
            # The TOC normally has no nearby anchors.  Among equally rich matches,
            # prefer the earlier occurrence: later annual-report notes often repeat
            # the same heading and can otherwise displace the primary statement.
            candidates.append((anchor_score, index))
            offset = index + len(marker)
    if not candidates:
        return None
    best_score = max(score for score, _ in candidates)
    start = min(index for score, index in candidates if score == best_score)
    end = min(len(text), start + max_chars)
    for stop in stop_markers:
        stop_index = text.find(stop, start + 120)
        if 0 <= stop_index < end:
            end = stop_index
    return text[max(0, start - before):end].strip()


def _corpus_material(
    documents: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_for_document: dict[str, str] = {}
    for item in candidates:
        for document_id in item.get("source_document_ids") or []:
            candidate_for_document.setdefault(str(document_id), str(item["candidate_id"]))
    filings = []
    chunks = []
    seen_sources = set()
    for document in documents:
        if document.get("data_type") not in {"official_filings", "financial_statements"}:
            continue
        source_identity = document.get("source_id") or document.get("content_hash")
        if source_identity in seen_sources:
            continue
        seen_sources.add(source_identity)
        document_id = str(document["document_id"])
        evidence_id = candidate_for_document.get(document_id)
        filings.append({
            "filing_id": document_id,
            "ticker": document.get("entity_key"),
            "market": "A",
            "company_name": (document.get("raw_payload") or {}).get("security_name"),
            "filing_type": document.get("source_type"),
            "title": document.get("title"),
            "published_at": document.get("published_at"),
            "source_key": document.get("source_id"),
            "source_url": document.get("source_url"),
            "parse_status": "parsed",
        })
        text = str(document.get("raw_text") or "")
        sections = (
            {
                "markers": ("近三年主要会计数据和财务指标", "主要会计数据和财务指标"),
                "anchors": ("营业收入", "归属于上市公司股东的净利润", "经营活动产生的现金流量净额"),
                "stops": ("分季度主要财务数据", "境内外会计准则下会计数据差异"),
                "section_name": "主要会计数据和财务指标",
                "section_type": "financial_statement",
                "topics": ["financials", "growth"],
                "before": 120,
                "max_chars": 9_000,
            },
            {
                "markers": ("主要业务、主要产品或服务情况", "公司主要业务", "公司主营业务"),
                "anchors": ("光电子器件", "主要产品", "传输类产品", "接入和数据类产品"),
                "stops": ("主要经营模式",),
                "section_name": "主营业务与产品结构",
                "section_type": "business_products",
                "topics": ["business", "products", "industry"],
                "before": 80,
                "max_chars": 14_000,
            },
            {
                "markers": ("业绩变化主要源于", "经营情况讨论与分析"),
                "anchors": ("营业收入", "净利润", "传统电信", "数通", "战略投入"),
                "stops": ("技术突破驱动产品矩阵升级", "报告期内主要经营情况"),
                "section_name": "经营表现与业绩归因",
                "section_type": "performance_drivers",
                "topics": ["financials", "operations", "growth"],
                "before": 120,
                "max_chars": 8_000,
            },
            {
                "markers": ("技术突破驱动产品矩阵升级",),
                "anchors": ("研发投入", "400G", "800G", "1.6T", "批量交付"),
                "stops": ("业务结构持续优化",),
                "section_name": "研发投入与产品商业化进展",
                "section_type": "product_progress",
                "topics": ["products", "operations", "growth"],
                "before": 80,
                "max_chars": 9_000,
            },
            {
                "markers": ("主要经营模式",),
                "anchors": ("采购模式", "生产模式", "销售模式", "客户认证"),
                "stops": ("行业情况说明", "报告期内核心竞争力分析"),
                "section_name": "采购生产与销售模式",
                "section_type": "operating_model",
                "topics": ["business", "operations"],
                "before": 80,
                "max_chars": 10_000,
            },
            {
                "markers": ("五、报告期内主要经营情况", "报告期内主要经营情况"),
                "anchors": (
                    "主营业务分产品情况",
                    "毛利率",
                    "产销量情况分析表",
                    "主要销售客户",
                    "经营活动产生的现金流量净额",
                ),
                "stops": ("(三) 资产、负债情况分析", "（三）资产、负债情况分析"),
                "section_name": "经营结果与分产品数据",
                "section_type": "operating_results",
                "topics": ["operations", "financials", "growth"],
                "before": 80,
                "max_chars": 24_000,
            },
            {
                "markers": ("(三) 资产、负债情况分析", "（三）资产、负债情况分析"),
                "anchors": ("应收账款", "存货", "固定资产", "在建工程", "应付账款"),
                "stops": ("(四) 行业经营性信息分析", "（四）行业经营性信息分析"),
                "section_name": "资产负债与营运资本",
                "section_type": "balance_sheet_analysis",
                "topics": ["operations", "financials", "risks"],
                "before": 80,
                "max_chars": 14_000,
            },
            {
                "markers": ("报告期内核心竞争力分析", "核心竞争力分析"),
                "anchors": ("技术创新", "研发优势", "专利", "客户资源"),
                "stops": ("报告期内主要经营情况", "公司关于公司未来发展的讨论与分析"),
                "section_name": "核心竞争力",
                "section_type": "competitive_advantages",
                "topics": ["products", "operations", "growth"],
                "before": 80,
                "max_chars": 14_000,
            },
            {
                "markers": ("公司关于公司未来发展的讨论与分析", "未来发展的讨论与分析"),
                "anchors": ("行业格局", "发展趋势", "发展战略", "经营计划"),
                "stops": ("公司经营面临的风险因素",),
                "section_name": "行业趋势与发展规划",
                "section_type": "outlook",
                "topics": ["industry", "growth"],
                "before": 80,
                "max_chars": 14_000,
            },
            {
                "markers": ("公司经营面临的风险因素", "经营面临的风险因素", "四、风险因素"),
                "anchors": ("风险", "核心技术", "原材料", "应收账款", "存货"),
                "stops": ("其他披露事项", "报告期内主要经营情况"),
                "section_name": "公司经营风险",
                "section_type": "risk_factors",
                "topics": ["risks"],
                "before": 80,
                "max_chars": 14_000,
            },
        )
        added = 0
        for section in sections:
            excerpt = _section_slice(
                text,
                section["markers"],
                anchors=section["anchors"],
                stop_markers=section["stops"],
                before=section["before"],
                max_chars=section["max_chars"],
            )
            if not excerpt:
                continue
            chunks.append({
                "chunk_id": f"acquired:{document_id}:{section['section_type']}",
                "document_id": document_id,
                "document_type": "annual_report",
                "source_key": document.get("source_id"),
                "ticker": document.get("entity_key"),
                "market": "A",
                "section_name": section["section_name"],
                "chunk_index": added,
                "text": excerpt,
                "evidence_id": evidence_id,
                "chunk_section_type": section["section_type"],
                "research_topics": section["topics"],
                "retrieval_score": 1.0,
            })
            added += 1
        if not added and text:
            chunks.append({
                "chunk_id": f"acquired:{document_id}:full_text",
                "document_id": document_id,
                "document_type": "annual_report",
                "source_key": document.get("source_id"),
                "ticker": document.get("entity_key"),
                "market": "A",
                "section_name": "年度报告全文",
                "chunk_index": 0,
                "text": text[:24_000],
                "evidence_id": evidence_id,
                "chunk_section_type": "full_text",
                "research_topics": ["business", "financials", "risks"],
                "retrieval_score": 0.9,
            })
    return filings, chunks


def _latest_facts(store: AcquisitionStore, ticker: str, data_type: str) -> tuple[str | None, list[dict[str, Any]]]:
    facts = [
        item for item in store.list_facts(ticker, data_type)
        if item.get("verification_status") == "verified" and item.get("as_of")
    ]
    latest = max((str(item["as_of"]) for item in facts), default=None)
    return latest, [item for item in facts if str(item.get("as_of")) == latest]


def _candidate_ids(candidates: list[dict[str, Any]], data_type: str) -> list[str]:
    return list(dict.fromkeys(
        str(item["candidate_id"])
        for item in candidates
        if item.get("data_type") == data_type and item.get("status") == "validated" and item.get("candidate_id")
    ))


def _materialize_market(
    store: AcquisitionStore,
    ticker: str,
    candidates: list[dict[str, Any]],
    research_context: dict[str, Any],
    valuation: dict[str, Any],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    target = research_context.setdefault("instruments", {}).setdefault("target", {})
    daily_facts = [
        item for item in store.list_facts(ticker, "daily_bars")
        if item.get("verification_status") == "verified" and item.get("as_of")
    ]
    bars_by_date: dict[str, dict[str, Any]] = defaultdict(dict)
    for item in daily_facts:
        as_of = str(item["as_of"])
        bars_by_date[as_of][str(item["field_name"])] = item.get("value")
    bars = [
        {"trade_date": as_of, **values, "market": "A"}
        for as_of, values in sorted(bars_by_date.items(), reverse=True)
    ][:260]
    if bars:
        target["daily_bars"] = bars
        freshness.update({
            "status": "fresh",
            "condition": "official_completed_session_available",
            "blocking_level": "info",
            "reason": "已通过按需采集补齐最近已完成交易日行情。",
            "last_data_timestamp": bars[0]["trade_date"],
        })

    quote_as_of, quote_facts = _latest_facts(store, ticker, "realtime_quote")
    quote_by_field = {str(item["field_name"]): item.get("value") for item in quote_facts}
    if quote_as_of and quote_by_field:
        target["quote"] = {
            **quote_by_field,
            "quote_time": quote_by_field.get("quote_time") or quote_as_of,
            "source_evidence_ids": _candidate_ids(candidates, "realtime_quote")[:1],
        }

    valuation_as_of, valuation_facts = _latest_facts(store, ticker, "valuation_snapshot")
    valuation_by_field = {str(item["field_name"]): item.get("value") for item in valuation_facts}
    if valuation_as_of and valuation_by_field:
        verification_method = next(
            (
                str((item.get("metadata") or {}).get("verification_method"))
                for item in valuation_facts
                if (item.get("metadata") or {}).get("verification_method")
            ),
            "cross_source_validation",
        )
        snapshot = {
            "ticker": ticker,
            "generated_at": valuation_by_field.get("as_of") or valuation_as_of,
            "current_price": valuation_by_field.get("price"),
            "market_cap": valuation_by_field.get("market_cap"),
            "pe_ttm": valuation_by_field.get("pe_ttm"),
            "pb": valuation_by_field.get("pb_mrq"),
            "allowed_usage": "research",
            "valuation_confidence": 0.95,
            "source_quality": "cross_validated_reputable_secondary",
            "source_evidence_ids": _candidate_ids(candidates, "valuation_snapshot")[:1],
            "metadata": {
                "currency": "CNY",
                "materialized_from": "acquisition_store",
                "verification_method": verification_method,
            },
        }
        valuation.clear()
        valuation.update(snapshot)
        target["valuation"] = snapshot

    peer_as_of, peer_facts = _latest_facts(store, ticker, "peer_comparison")
    peer_by_field = {str(item["field_name"]): item.get("value") for item in peer_facts}
    peer_metrics = list(peer_by_field.get("comparable_metrics") or [])
    if peer_as_of and peer_metrics:
        peer_evidence = _candidate_ids(candidates, "peer_comparison")[:1]
        research_context.setdefault("graph", {})["peers"] = list(peer_by_field.get("peer_set") or [])
        research_context["graph"]["peer_selection_reason"] = peer_by_field.get("selection_reason")
        research_context["instruments"]["peers"] = [
            {
                "ticker": item.get("ticker"),
                "company_name": item.get("company_name"),
                "daily_bars": [{
                    "trade_date": str(item.get("as_of") or "")[:10],
                    "close": item.get("price"),
                    "market": "A",
                }],
                "valuation": {
                    "generated_at": item.get("as_of"),
                    "current_price": item.get("price"),
                    "market_cap": item.get("market_cap_cny"),
                    "pe_ttm": item.get("pe_ttm"),
                    "pb": item.get("pb_mrq"),
                    "valuation_flags": item.get("valuation_flags") or [],
                    "currency": item.get("currency"),
                    "source_evidence_ids": peer_evidence,
                    "allowed_usage": "research",
                },
                "selection_reason": item.get("selection_reason"),
                "fundamentals": None,
            }
            for item in peer_metrics
        ]
    return {
        "daily_bars_materialized": len(bars),
        "quote_materialized": bool(quote_as_of and quote_by_field),
        "valuation_materialized": bool(valuation_as_of and valuation_by_field),
        "peers_materialized": len(peer_metrics),
    }


def materialize_acquired_stock_data(
    store: AcquisitionStore,
    *,
    ticker: str,
    fundamentals: dict[str, Any],
    valuation: dict[str, Any],
    evidence: dict[str, Any],
    research_context: dict[str, Any],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    documents = [document for data_type in ACQUIRED_DATA_TYPES for document in store.list_documents(ticker, data_type)]
    documents_by_id = {str(item["document_id"]): item for item in documents}
    candidates = store.list_evidence_candidates(ticker)
    snapshot = _financial_snapshot(store, ticker, candidates)
    acquired_evidence = _evidence_items(candidates, documents_by_id)
    merged_evidence = {str(item.get("evidence_id")): item for item in (evidence.get("items") or []) if item.get("evidence_id")}
    for item in acquired_evidence:
        merged_evidence[str(item["evidence_id"])] = item
    evidence.update({"ticker": ticker, "count": len(merged_evidence), "items": list(merged_evidence.values())})
    if snapshot:
        fundamentals.clear()
        fundamentals.update(snapshot)
        research_context.setdefault("instruments", {}).setdefault("target", {})["fundamentals"] = snapshot
    filings, chunks = _corpus_material(documents, candidates)
    corpus = research_context.setdefault("corpus", {})
    research_context["acquired_evidence"] = acquired_evidence
    acquired_filing_ids = {str(item["filing_id"]) for item in filings}
    acquired_chunk_ids = {str(item["chunk_id"]) for item in chunks}
    # Verified write-through material is deliberately ranked before legacy rows so
    # deterministic parsers and report citations use the just-validated source.
    corpus["filings"] = [
        *filings,
        *(item for item in corpus.get("filings") or [] if str(item.get("filing_id")) not in acquired_filing_ids),
    ]
    corpus["chunks"] = [
        *chunks,
        *(item for item in corpus.get("chunks") or [] if str(item.get("chunk_id")) not in acquired_chunk_ids),
    ]
    if filings:
        identity = research_context.setdefault("identity", {})
        if identity.get("company_name") in {None, "", ticker} and filings[0].get("company_name"):
            identity["company_name"] = filings[0]["company_name"]
    if filings:
        health = research_context.setdefault("provider_status", {}).setdefault("official_filings", {})
        health.update({"status": "available", "acquisition_store_documents": len(filings)})
    market_result = _materialize_market(store, ticker, candidates, research_context, valuation, freshness)
    return {
        "financial_snapshot_materialized": bool(snapshot),
        "evidence_items_materialized": len(acquired_evidence),
        "filings_materialized": len(filings),
        "chunks_materialized": len(chunks),
        **market_result,
    }
