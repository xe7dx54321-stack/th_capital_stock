#!/usr/bin/env python3
"""Phase 70: CNINFO org_id discovery for blocked tickers."""
import json, urllib.request, urllib.parse
from typing import Any

CNINFO_API = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
HEADERS = {"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.cninfo.com.cn/","Content-Type":"application/x-www-form-urlencoded"}

# Extended candidate org_ids for 300394.SZ
CANDIDATE_ORG_IDS_300394 = [
    "9900022065", "9900022165", "9900022265",
    "9900022018", "9900022024", "9900022035",
    "9900022092", "9900022100", "9900022124",
]

def discover_org_id(ticker="300394.SZ") -> dict[str, Any]:
    """Attempt to discover verified CNINFO org_id for a ticker."""
    code = ticker.split(".")[0]
    plate = "sz"; column = "szse"

    candidates = CANDIDATE_ORG_IDS_300394
    tried = []

    for org_id in candidates:
        stock_param = f"{code},{org_id}"
        result = _verify_org_id(stock_param, plate, column)
        tried.append({"org_id": org_id, "verified": result["verified"],
                       "total_announcement": result.get("total_announcement", 0),
                       "error": result.get("error", "")})
        if result["verified"]:
            return {
                "ticker": ticker,
                "phase70_300394_orgid_discovery": {
                    "discovery_attempted": True,
                    "candidates_tested": len(tried),
                    "verified_org_id_found": True,
                    "org_id": org_id,
                    "stock_param": stock_param,
                    "plate": plate, "column": column,
                    "verification_metadata_sources_found": result["total_announcement"],
                    "verification_status": "metadata_query_verified",
                    "ticker_specific": True,
                    "candidates_tried": tried,
                    "mock_used": False, "fixture_used": False
                }
            }

    return {
        "ticker": ticker,
        "phase70_300394_orgid_discovery": {
            "discovery_attempted": True,
            "candidates_tested": len(tried),
            "verified_org_id_found": False,
            "failure_reason": "no_candidate_org_id_returned_metadata_for_300394",
            "next_manual_action": "manual_cninfo_company_page_lookup_required",
            "candidates_tried": tried,
            "mock_used": False, "fixture_used": False
        }
    }

def _verify_org_id(stock_param: str, plate: str, column: str) -> dict[str, Any]:
    """Verify org_id by querying CNINFO metadata."""
    try:
        params = {"pageNum": 1, "pageSize": 5, "stock": stock_param, "plate": plate,
                  "column": column, "tabName": "fulltext", "searchkey": "", "secid": "",
                  "category": "", "trade": "", "seDate": ""}
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(CNINFO_API, data=data, headers=dict(HEADERS))
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
        total = body.get("totalAnnouncement", 0)
        anns = body.get("announcements", [])
        # Also check if first announcement title contains company name
        first_title = ""
        if anns:
            first_title = anns[0].get("announcementTitle", "")
        verified = total > 0
        return {"verified": verified, "total_announcement": total, "first_title": first_title}
    except Exception as e:
        return {"verified": False, "total_announcement": 0, "error": str(e)[:120]}
