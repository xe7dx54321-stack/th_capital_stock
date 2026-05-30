#!/usr/bin/env python3
import json, heapq
from pathlib import Path
import sys
L = Path(__file__).resolve().parent
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES

HIGH_PRIORITY = ["annual_report", "semiannual_report", "quarterly_report",
    "investor_relations_record", "performance_briefing", "major_announcement"]
LOW_PRIORITY = [u"股权激励", u"独立董事", u"法律意见书", u"审计机构", u"章程", u"制度"]

def classify_category(title):
    t = title.lower()
    if any(w in t for w in [u"年度报告", "annual report"]): return "annual_report", 0
    if any(w in t for w in [u"半年度报告", "semiannual"]): return "semiannual_report", 1
    if any(w in t for w in [u"季度报告", "quarterly"]): return "quarterly_report", 2
    if any(w in t for w in [u"投资者关系", "investor relation", u"调研", u"路演"]): return "investor_relations_record", 3
    if any(w in t for w in [u"业绩说明会", "performance briefing"]): return "performance_briefing", 4
    if any(w in t for w in [u"募集", u"招股", u"上市公告", u"发行"]): return "major_announcement", 5
    for i, kw in enumerate(LOW_PRIORITY):
        if kw.lower() in t.lower():
            return "admin_low_priority", 90 + i
    return "other", 50

def build_inventory(ticker="688041.SH", metadata_rows=None, max_candidates=10):
    ident = CURATED_CNINFO_IDENTITIES.get(ticker, {})
    if not ident:
        return {"phase76_688041_pdf_inventory": {"ticker": ticker, "status": "identity_not_found", "pdf_candidates_selected": 0, "rows": [], "mock_used": False, "fixture_used": False}}
    if metadata_rows is None:
        metadata_rows = []
    candidates = []
    for row in metadata_rows:
        title = row.get("announcementTitle", row.get("title", ""))
        pdf_rel = row.get("adjunctUrl", row.get("pdfUrl", ""))
        if not pdf_rel: continue
        cat_rank = classify_category(title)
        full_url = "https://static.cninfo.com.cn/" + pdf_rel if not pdf_rel.startswith("http") else pdf_rel
        priority = "P0" if cat_rank[1] <= 2 else ("P1" if cat_rank[1] <= 5 else "P2_low")
        candidates.append((cat_rank[1], {
            "title": title[:120],
            "announcement_date": row.get("announceTime", row.get("publishDate", ""))[:10],
            "category": cat_rank[0],
            "pdf_url_normalized": full_url,
            "priority": priority,
            "download_allowed": True,
            "ocr_allowed": False,
            "raw_save_allowed": False,
            "source_type": "cninfo_pdf"
        }))
    candidates.sort(key=lambda x: x[0])
    selected = [c[1] for c in candidates[:max_candidates]]
    high = sum(1 for s in selected if s["priority"] in ("P0", "P1"))
    return {"phase76_688041_pdf_inventory": {
        "ticker": ticker,
        "metadata_sources_found": len(metadata_rows),
        "pdf_urls_found": len(candidates),
        "pdf_candidates_selected": len(selected),
        "high_priority_pdfs": high,
        "rows": selected,
        "mock_used": False, "fixture_used": False
    }}
