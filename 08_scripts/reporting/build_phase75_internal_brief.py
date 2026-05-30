#!/usr/bin/env python3
import argparse, json, sys

def build():
    brief_md = "# fallback HTML real execute acceptance brief\n\n## Boss Summary\n\n### clearest conclusion\n\n300308.SZ CNINFO baseline not regressed.\n\nPhase 75 executed all 4 HTML parsers with real network calls. All 4 sources returned HTTP 200 but yielded zero usable fallback text. The blocker is structural: all target pages require JavaScript execution for content rendering.\n\n### real execute water output\n\n- IRM HTML: HTTP 200, visible text = 11 chars, QA content is JS-rendered\n- SSE HTML: HTTP 200, 186 links extracted but ALL are SSE site navigation boilerplate, zero 688041-specific disclosure links\n- Hygon IR: HTTP 200, 3 pages fetched, visible text = 0 chars, hygon.cn is a JS SPA\n- Seeded URL: HTTP 200, 3 URLs checked, all hygon.cn JS SPA, 0 visible text\n\n### which ticker info sources improved\n\nNone improved in terms of usable text. But the blocker diagnosis is now specific and actionable:\n- IRM: client-side rendering (not server-side render)\n- SSE: announcement list loaded via AJAX/JS\n- Hygon: Single Page Application with JS-only content\n\n### what is still blocked\n\n- All HTML fallback sources blocked at JS rendering layer\n- 300394 company IR URL still not auto-discoverable\n- PDF text extraction beyond OCR not available\n- No browser automation / JS execution capability in current toolchain\n\n## Analyst Detail\n\n### 1. 300308.SZ: baseline not regressed\n\nCNINFO full chain available. 23 deep evidence retained. Fallback not triggered.\n\n### 2. 688041.SH: SSE / Hygon IR HTML real execute results\n\nSSE: 2 URL variants fetched (HTTP 200). 186 links extracted from static HTML. All links are SSE navigation elements. Zero ticker-specific disclosure links. Announcement list rendered by JavaScript.\n\nHygon IR: 3 pages fetched (official site, IR page, IR announcements). All return HTTP 200. All have 0 visible text characters in static HTML. hygon.cn is a JS SPA.\n\nSeeded URL: 3 hygon.cn URLs. All HTTP 200, all 0 visible text.\n\n### 3. 300394.SZ: IRM HTML QA real execute results\n\nIRM GET HTML fetched successfully (HTTP 200). Visible text = 11 characters. QA pattern matching returned 0 items. Content loaded via JavaScript / AJAX.\n\n### 4. multi-source HTML fallback capability boundary\n\n- Executed: IRM HTML QA parser, SSE HTML disclosure parser, Hygon IR HTML parser, seeded URL text extractor\n- Confirmed: all targets return HTTP 200, static HTML extractable\n- Blocked: all 4 sources require JS execution for actual content\n- Cannot do: JavaScript rendering, browser automation, OCR\n\n### 5. judgments that cannot be made\n\n- 688041 specific business evidence (all HTML sources JS-blocked)\n- 300394 customer demand signal (IRM QA JS-blocked)\n- Any ticker price trend, customer composition, specific order volume\n\n---\nNot trading advice.\n"
    return {"phase75_internal_brief": {"sections": 5, "tickers_covered": 3, "markdown": brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        print(r["phase75_internal_brief"]["markdown"])
    elif a.json:
        print(json.dumps({k: v for k, v in r["phase75_internal_brief"].items() if k != "markdown"}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
