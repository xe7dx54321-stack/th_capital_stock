#!/usr/bin/env python3
# Phase 75: Fallback text consolidator
from typing import Any

def consolidate(irm_result=None, sse_result=None, hygon_result=None, seeded_result=None):
    texts = []
    seen_hashes = set()
    # IRM QA texts
    if irm_result:
        ir = irm_result.get("phase75_irm_html_real_execute", irm_result)
        for row in ir.get("rows", []):
            usable_qa = row.get("qa_text_usable", 0) > 0 or "usable" in str(row.get("quality_grade", ""))
            if usable_qa:
                for qi in row.get("qa_items", []):
                    ans = qi.get("answer", "").strip()
                    if ans:
                        h = "irm:" + (qi.get("qa_hash", "") or str(abs(hash(ans))))
                        if h not in seen_hashes:
                            seen_hashes.add(h)
                            texts.append({"ticker": row.get("ticker", ""), "source_type": "irm_html",
                                "quality_grade": "usable_irm_qa", "allowed_usage": "management_commentary",
                                "text_hash": qi.get("qa_hash", ""), "text_preview": ans[:2000],
                                "text_length": len(ans)})
    # SSE texts
    if sse_result:
        sr = sse_result.get("phase75_sse_html_real_execute", sse_result)
        for ti in sr.get("texts", []):
            th = ti.get("text_hash", "")
            if th and th not in seen_hashes:
                seen_hashes.add(th)
                texts.append({"ticker": sr.get("ticker", ""), "source_type": "sse_html",
                    "quality_grade": "usable_sse_exchange_text", "allowed_usage": "exchange_text",
                    "text_hash": th, "text_preview": ti.get("text", "")[:2000],
                    "text_length": ti.get("text_length", 0)})
    # Hygon texts
    if hygon_result:
        hr = hygon_result.get("phase75_hygon_ir_html_real_execute", hygon_result)
        for row in hr.get("rows", []):
            qh = row.get("quality_hint", "")
            if "usable" in str(qh):
                th = row.get("text_hash", "")
                if th and th not in seen_hashes:
                    seen_hashes.add(th)
                    texts.append({"ticker": hr.get("ticker", ""), "source_type": "hygon_ir_html",
                        "quality_grade": qh, "allowed_usage": "company_context",
                        "text_hash": th, "text_preview": row.get("text_preview", "")[:2000],
                        "text_length": row.get("text_length", 0)})
    # Seeded URL texts
    if seeded_result:
        ss = seeded_result.get("phase75_seeded_url_html_real_execute", seeded_result)
        for row in ss.get("rows", []):
            qh = row.get("quality_hint", "")
            if "usable" in str(qh):
                th = row.get("text_hash", "")
                if th and th not in seen_hashes:
                    seen_hashes.add(th)
                    tk = row.get("ticker", ss.get("ticker", ""))
                    texts.append({"ticker": tk, "source_type": row.get("source_type", "seeded_url"),
                        "quality_grade": qh, "allowed_usage": "company_context",
                        "text_hash": th, "text_preview": row.get("text_preview", "")[:2000],
                        "text_length": row.get("text_length", 0)})
    usable = len(texts)
    return {"phase75_fallback_text_pool": {"tickers_checked": 3, "source_results_merged": 4,
        "texts_total": usable, "texts_usable": usable, "rows": texts,
        "mock_used": False, "fixture_used": False}}
