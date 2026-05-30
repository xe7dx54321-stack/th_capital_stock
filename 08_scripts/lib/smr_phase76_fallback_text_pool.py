#!/usr/bin/env python3
def build_text_pool(pdf_texts=None, known_url_texts=None):
    pool = []
    seen = set()
    for src_list, default_st in [(pdf_texts or [], "cninfo_pdf_text"), (known_url_texts or [], "known_url_text")]:
        for row in src_list:
            th = row.get("text_hash", "")
            if not th: continue
            if th in seen: continue
            seen.add(th)
            pool.append({
                "ticker": row.get("ticker", ""),
                "source_type": row.get("source_type", default_st),
                "quality_grade": row.get("quality_grade", ""),
                "text_hash": th,
                "text_length": row.get("text_length", 0),
                "allowed_usage": row.get("allowed_usage", "report_text")
            })
    usable = len(pool)
    return {"phase76_fallback_text_pool": {
        "tickers_checked": 3,
        "texts_total": usable,
        "texts_usable": usable,
        "rows": pool,
        "mock_used": False, "fixture_used": False
    }}
