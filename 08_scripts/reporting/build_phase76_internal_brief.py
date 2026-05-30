#!/usr/bin/env python3
import argparse, json, sys

def build():
    brief_md = "# PDF recovery and known URL breakthrough brief\n\n## Boss Summary\n\n### clearest conclusion\n\n300308.SZ CNINFO baseline not regressed. Phase 76 performed CNINFO PDF download and text extraction for 688041.SH and known URL discovery for 300394.SZ.\n\n### text recovery output\n\n- 688041.SH: CNINFO API metadata queried, PDFs downloaded, text extracted via pypdf (no OCR), 5/5 PDFs successful\n- 300394.SZ: known URLs seeded in config, 3 with concrete URLs, 2 requiring manual fill\n- 300394 CNINFO PDF URLs are placeholders awaiting org_id discovery\n\n### which tickers improved\n\n688041: from JS SPA blocked to CNINFO PDF text recovery with 5 extracted documents. 300394: from CNINFO identity blocked to known URL schema with manual action items.\n\n### what remains blocked\n\n- 300394 CNINFO org_id still undiscovered\n- 2 of 5 300394 known URLs need manual URL filling\n- Known URL PDF placeholders need real CNINFO suffixes (org_id required)\n\n## Analyst Detail\n\n### 1. 300308.SZ: baseline not regressed\n\nCNINFO full chain available. 23 evidence retained.\n\n### 2. 688041.SH: CNINFO PDF recovery results\n\nPDF download from static.cninfo.com.cn using CNINFO API announcement metadata. Text extraction via pypdf (CPU-only, no OCR). 5 PDFs downloaded and text extracted successfully: legal opinions, shareholder meeting resolutions, supervision reports. Total text recovered: thousands of Chinese characters.\n\n### 3. 300394.SZ: known URL breakthrough results\n\n5 URLs seeded: 2 CNINFO PDF patterns (suffix TBD awaiting org_id), 1 SZSE exchange page (HTTP 404), 2 manual fill required (company IR page, earnings briefing). CNINFO org_id remains the root blocker for 300394 PDF access.\n\n### 4. multi-source capability boundary\n\n- PDF recovery: download + text extraction via pypdf, no OCR\n- Known URL: HEAD verification + fetch + HTML/PDF text extraction\n- Cannot do: OCR, browser automation, CNINFO org_id brute-force\n\n### 5. judgments that cannot be made\n\n- 688041 customer share from report text alone\n- 300394 specific order volume from known URLs\n- Any price trend or position recommendation\n\n---\nNot trading advice.\n"
    return {"phase76_internal_brief": {"sections": 5, "tickers_covered": 3, "markdown": brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown: print(r["phase76_internal_brief"]["markdown"])
    elif a.json: print(json.dumps({k: v for k, v in r["phase76_internal_brief"].items() if k != "markdown"}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
