#!/usr/bin/env python3
"""Phase 70: 300394.SZ curated identity patch."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_phase70_cninfo_orgid_discovery import discover_org_id
    disc = discover_org_id()
    diag = disc.get("phase70_300394_orgid_discovery", disc)

    if not diag.get("verified_org_id_found"):
        return {"ticker":"300394.SZ","phase70_300394_curated_identity_patch":{
            "identity_patch_applied": False,
            "reason": "no_verified_org_id_to_patch",
            "org_id": None, "ticker_specific": True,
            "mock_used": False, "fixture_used": False}}

    # Write to curated identity map
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    org_id = diag["org_id"]
    code = "300394"
    CURATED_CNINFO_IDENTITIES["300394.SZ"] = {
        "security_code": code, "org_id": org_id,
        "stock_param": f"{code},{org_id}",
        "plate": "sz", "column": "szse",
        "identity_source": "phase70_verified",
        "verification_status": "metadata_query_verified",
        "ticker_specific": True
    }
    return {"ticker":"300394.SZ","phase70_300394_curated_identity_patch":{
        "identity_patch_applied": True,
        "org_id": org_id, "stock_param": f"{code},{org_id}",
        "plate": "sz", "column": "szse",
        "verification_status": "metadata_query_verified",
        "ticker_specific": True,
        "mock_used": False, "fixture_used": False}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        d = r["phase70_300394_curated_identity_patch"]
        status = "Applied" if d["identity_patch_applied"] else "Not applied"
        lines = [f"# 300394.SZ Curated Identity Patch: {status}", "",
                 f"- Applied: {d['identity_patch_applied']}",
                 f"- Org ID: {d.get('org_id','N/A')}"]
        print("\n".join(lines))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
