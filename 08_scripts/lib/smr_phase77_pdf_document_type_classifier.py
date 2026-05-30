#!/usr/bin/env python3
def classify_document(title="", text_preview=""):
    t = (title + " " + (text_preview or "")[:500]).lower()
    if any(w in t for w in [u"法律意见书", "legal opinion", u"律师事务所"]):
        return {"document_type": "legal_opinion", "confidence": "high", "reason": "legal_opinion_keywords"}
    if any(w in t for w in [u"股东会决议", u"股东大会议", u"shareholder resolution", u"股东会通知"]):
        return {"document_type": "shareholder_meeting_resolution", "confidence": "high", "reason": "shareholder_meeting_keywords"}
    if any(w in t for w in [u"年度报告", "annual report"]) and not any(w in t for w in [u"督导", u"保荐"]):
        return {"document_type": "annual_report", "confidence": "high", "reason": "annual_report_keywords"}
    if any(w in t for w in [u"半年度报告", "semiannual"]):
        return {"document_type": "semiannual_report", "confidence": "high", "reason": "semiannual_keywords"}
    if any(w in t for w in [u"季度报告", "quarterly"]):
        return {"document_type": "quarterly_report", "confidence": "high", "reason": "quarterly_keywords"}
    if any(w in t for w in [u"督导跟踪报告", u"持续督导跟踪"]):
        return {"document_type": "supervision_report", "confidence": "high", "reason": "supervision_tracking_keywords"}
    if any(w in t for w in [u"督导工作现场检查", u"现场检查报告"]):
        return {"document_type": "supervision_report", "confidence": "high", "reason": "supervision_inspection_keywords"}
    if any(w in t for w in [u"保荐总结报告", u"保荐总结报告书", "sponsorship summary"]):
        return {"document_type": "supervision_report", "confidence": "high", "reason": "sponsorship_summary_keywords"}
    if any(w in t for w in [u"督导", u"保荐"]):
        return {"document_type": "supervision_report", "confidence": "medium", "reason": "supervision_general_keywords"}
    if any(w in t for w in [u"业绩预告", "earnings preview"]):
        return {"document_type": "earnings_preview", "confidence": "high", "reason": "earnings_preview_keywords"}
    if any(w in t for w in [u"章程", u"制度", u"规则", "policy", "rule"]):
        return {"document_type": "governance_policy", "confidence": "medium", "reason": "governance_policy_keywords"}
    if any(w in t for w in [u"公告", u"通知", u"声明", "announcement"]):
        return {"document_type": "administrative_announcement", "confidence": "low", "reason": "generic_announcement_keywords"}
    return {"document_type": "unknown", "confidence": "low", "reason": "no_strong_signal"}

def classify_pdfs(pdf_rows):
    results = []
    type_counts = {}
    for row in pdf_rows:
        c = classify_document(row.get("title",""), row.get("text_preview",""))
        doc_type = c["document_type"]
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        results.append({
            "title": row.get("title","")[:120],
            "document_type": doc_type,
            "document_type_confidence": c["confidence"],
            "classification_reason": c["reason"],
            "allowed_usage": "business_context" if doc_type in ("annual_report","quarterly_report","supervision_report") else "governance_context_only",
            "not_allowed_usage": ["confirmed_evidence","strong_direct"] if doc_type in ("legal_opinion","shareholder_meeting_resolution") else []
        })
    return {"phase77_688041_pdf_document_type": {
        "ticker": "688041.SH", "pdfs_checked": len(results), "classified": len(results),
        "document_type_mix": type_counts, "rows": results, "mock_used": False, "fixture_used": False
    }}
