import os

def check_link_integrity(base_dir="09_runbooks/generated"):
    pages = {
        "phase141_research_console.html": ["ticker-cards", "thesis-library", "evidence-sources", "daily-delivery"],
        "phase142_ticker_details/index.html": ["Research Console", "detail-page"],
    }
    tickers = ["NVDA", "AVGO", "688041-SH", "300308-SZ", "002230-SZ", "09988-HK", "00700-HK", "300394-SZ"]
    for t in tickers:
        pages[f"phase142_ticker_details/{t}.html"] = ["Research Console", "detail-page", "thesis-timeline", "evidence-chain"]

    results = []
    all_ok = True
    for rel_path, required_sections in pages.items():
        full_path = os.path.join(base_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            missing = [s for s in required_sections if s not in content]
            status = "pass" if not missing else "fail"
            if missing:
                all_ok = False
            results.append({"path": rel_path, "exists": True, "status": status, "missing_sections": missing})
        else:
            results.append({"path": rel_path, "exists": False, "status": "fail", "missing_sections": ["FILE_NOT_FOUND"]})
            all_ok = False

    return {
        "phase143_link_integrity_check": {
            "overall_status": "pass" if all_ok else "fail",
            "files_checked": len(results),
            "files_pass": sum(1 for r in results if r["status"] == "pass"),
            "files_fail": sum(1 for r in results if r["status"] == "fail"),
            "results": results,
            "mock_used": False,
            "fixture_used": False
        }
    }
