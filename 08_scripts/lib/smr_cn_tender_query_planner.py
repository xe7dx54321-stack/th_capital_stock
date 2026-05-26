#!/usr/bin/env python3
"""Phase 24 CN tender/procurement query planner.

The planner only creates search plans. It does not fetch pages, write evidence,
or widen the watchlist.
"""

from __future__ import annotations

from typing import Any


CN_TICKER_COMPANY_NAMES = {
    "300308.SZ": "中际旭创",
    "688041.SH": "海光信息",
    "002230.SZ": "科大讯飞",
}

BASE_QUERY_TERMS = [
    ("中标", "tender_award", "high", "tender_award"),
    ("采购", "procurement", "medium", "procurement_notice"),
    ("招标", "tender_notice", "medium", "tender_notice"),
    ("合同", "signed_contract", "high", "signed_contract"),
    ("框架协议", "framework_agreement", "medium", "framework_agreement"),
]

AI_INFRA_TERMS = ["算力", "智算", "AI服务器", "数据中心", "服务器", "芯片", "国产算力", "云计算", "大模型", "GPU服务器", "服务器采购"]


def normalize_ticker(ticker: str | None) -> str:
    return str(ticker or "").strip().upper()


def company_name_for_ticker(ticker: str, company_name: str | None = None) -> str | None:
    explicit = str(company_name or "").strip()
    if explicit:
        return explicit
    return CN_TICKER_COMPANY_NAMES.get(normalize_ticker(ticker))


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for row in rows:
        key = (row.get("ticker"), row.get("query"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def build_cn_tender_queries(
    ticker: str,
    company_name: str | None = None,
    thesis_type: str | None = None,
    keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    company = company_name_for_ticker(ticker, company_name)
    if not company:
        return [
            {
                "ticker": ticker,
                "company_name": None,
                "query": None,
                "query_type": "missing_company_name",
                "priority": "blocked",
                "expected_evidence_type": "missing_company_name",
                "reason": "company_name is required for CN tender/procurement search planning",
            }
        ]

    rows: list[dict[str, Any]] = []
    for term, query_type, priority, expected in BASE_QUERY_TERMS:
        rows.append(
            {
                "ticker": ticker,
                "company_name": company,
                "query": f"{company} {term}",
                "query_type": query_type,
                "priority": priority,
                "expected_evidence_type": expected,
            }
        )

    thesis = str(thesis_type or "").lower()
    terms = list(AI_INFRA_TERMS if ("ai" in thesis or "infra" in thesis or not thesis) else [])
    terms.extend(keywords or [])
    for term in terms:
        query_type = "tender_award" if "中标" in term else "ai_infrastructure_procurement"
        expected = "tender_award" if "中标" in term else "procurement_notice"
        priority = "high" if term in {"算力", "智算", "AI服务器", "数据中心", "服务器采购"} else "medium"
        rows.append(
            {
                "ticker": ticker,
                "company_name": company,
                "query": f"{company} {term}",
                "query_type": query_type,
                "priority": priority,
                "expected_evidence_type": expected,
            }
        )
        if term in {"算力", "智算", "AI服务器", "服务器采购"}:
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company,
                    "query": f"{company} 中标 {term}",
                    "query_type": "tender_award",
                    "priority": "high",
                    "expected_evidence_type": "tender_award",
                }
            )
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company,
                    "query": f"{company} 采购 {term}",
                    "query_type": "procurement",
                    "priority": "medium",
                    "expected_evidence_type": "procurement_notice",
                }
            )
    return _dedupe(rows)
