#!/usr/bin/env python3
"""Phase 70 research packet."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    c394 = CURATED_CNINFO_IDENTITIES.get("300394.SZ", {})
    id300394_found = bool(c394.get("org_id") and c394.get("verification_status") == "metadata_query_verified")

    tickers = [
        {"ticker":"300308.SZ","research_status":"full_evidence_backed_tracking",
         "key_supported_claims":["800G_signal_supported","1_6T_signal_supported","product_mix_partially_supported","shipment_delivery_supported","order_visibility_partially_supported","capacity_expansion_supported"],
         "key_unconfirmed_claims":["asp_trend_unconfirmed","customer_share_unconfirmed","specific_order_volume_unconfirmed"]},
        {"ticker":"688041.SH","research_status":"metadata_available_pdf_pending_hardening",
         "key_supported_claims":[],"key_unconfirmed_claims":[],
         "partial_reason":"pdf_download_text_extraction_pending_network_hardening"},
    ]
    if id300394_found:
        tickers.append({"ticker":"300394.SZ","research_status":"identity_repaired_metadata_available_pdf_pending",
                        "key_supported_claims":[],"key_unconfirmed_claims":[],
                        "partial_reason":"identity_repaired_pdf_pending"})
    else:
        tickers.append({"ticker":"300394.SZ","research_status":"blocked_identity_missing",
                        "blocker":"verified_cninfo_org_id_not_found_after_extended_discovery"})

    return {"phase70_research_packet":{"tickers":tickers,"pending_created":0,"paper_order_created":0,"real_trade_created":0}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        pkt = r["phase70_research_packet"]
        lines = ["# Phase 70 Research Packet"]
        for t in pkt["tickers"]:
            lines.append(f"\n## {t['ticker']}: {t['research_status']}")
            if t.get("key_supported_claims"): lines.append(f"- Supported: {', '.join(t['key_supported_claims'])}")
            if t.get("key_unconfirmed_claims"): lines.append(f"- Unconfirmed: {', '.join(t['key_unconfirmed_claims'])}")
            if t.get("blocker"): lines.append(f"- Blocker: {t['blocker']}")
            if t.get("partial_reason"): lines.append(f"- Reason: {t['partial_reason']}")
        print("\n".join(lines))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
