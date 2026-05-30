#!/usr/bin/env python3
from pathlib import Path
import sys
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase77_quality_config import get_reliability, get_business_relevance, get_evidence_strength

def score_pdfs(pdf_rows):
    results = []
    total = 0
    for row in pdf_rows:
        doc_type = row.get("document_type","unknown")
        rel = get_reliability(doc_type)
        biz = get_business_relevance(doc_type, row.get("text_preview",""))
        evs = get_evidence_strength(doc_type)
        total += rel
        results.append({
            "title": row.get("title","")[:120],
            "document_type": doc_type,
            "reliability_score": rel,
            "business_relevance_hint": biz,
            "allowed_evidence_strength": evs,
            "score_reason": [f"doc_type={doc_type}", f"reliability={rel}", f"business={biz}", f"strength={evs}"]
        })
    avg = round(total / max(len(results), 1), 2)
    return {"phase77_688041_source_reliability": {
        "ticker": "688041.SH", "pdfs_scored": len(results),
        "average_reliability_score": avg, "rows": results, "mock_used": False, "fixture_used": False
    }}
