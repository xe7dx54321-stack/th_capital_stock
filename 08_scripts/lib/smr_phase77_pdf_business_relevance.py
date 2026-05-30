#!/usr/bin/env python3
GENERIC_VARS = ["product_progress","R&D","revenue_growth","gross_margin","customer_demand","orders","capacity","localization","risk_signal","governance_context"]
VAR_KEYWORDS = {
    "product_progress": [u"产品", u"研发", "product", "cpu", "gpu", "dcu", u"处理器", u"芯片"],
    "R&D": [u"研发", u"开发", "r&d", u"研究", u"技术", u"专利"],
    "revenue_growth": [u"收入", u"营收", "revenue", u"增长", u"同比增长"],
    "gross_margin": [u"毛利", "gross margin", u"利润率"],
    "customer_demand": [u"客户", "customer", u"需求", "demand"],
    "orders": [u"订单", "order", u"合同"],
    "capacity": [u"产能", "capacity", u"产量"],
    "localization": [u"国产", u"自主", "localization", u"替代"],
    "risk_signal": [u"风险", "risk", u"不确定", u"波动"]
}

def score_business_relevance(pdf_rows):
    results = []
    biz_count = 0
    gov_count = 0
    for row in pdf_rows:
        title = (row.get("title","") or "").lower()
        text = (row.get("text_preview","") or "").lower()[:3000]
        combined = title + " " + text
        doc_type = row.get("document_type","unknown")
        if doc_type in ("legal_opinion","shareholder_meeting_resolution","governance_policy"):
            gov_count += 1
            results.append({
                "title": row.get("title","")[:120],
                "document_type": doc_type,
                "business_relevance": "low",
                "matched_variables": ["governance_context"],
                "allowed_for_deep_extraction": False
            })
            continue
        matched = []
        for var, kws in VAR_KEYWORDS.items():
            if var == "governance_context": continue
            if any(kw.lower() in combined for kw in kws):
                matched.append(var)
        if not matched:
            matched = ["governance_context"]
        biz = "medium" if doc_type == "supervision_report" else ("high" if len(matched) > 3 else "low")
        allowed = biz != "low"
        if allowed: biz_count += 1
        else: gov_count += 1
        results.append({
            "title": row.get("title","")[:120],
            "document_type": doc_type,
            "business_relevance": biz,
            "matched_variables": matched[:5],
            "allowed_for_deep_extraction": allowed
        })
    return {"phase77_688041_business_relevance": {
        "ticker": "688041.SH", "pdfs_checked": len(results),
        "business_relevant_pdfs": biz_count,
        "governance_or_legal_only_pdfs": gov_count,
        "rows": results, "mock_used": False, "fixture_used": False
    }}
