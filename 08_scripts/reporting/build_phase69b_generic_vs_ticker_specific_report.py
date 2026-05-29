#!/usr/bin/env python3
"""Phase 69b generic vs ticker-specific report."""
import argparse, json, sys
def build():
    return {'generic_vs_ticker_specific_report': {
        'generic_capabilities': ['metadata_fetch_framework','pagination_query','high_value_pdf_selection','pdf_text_extraction','evidence_memory_schema','capability_matrix','source_trace_index','evidence_claim_linkage','claim_state_memory','brief_quality_lint'],
        'ticker_specific_requirements': ['cninfo_org_id','stock_param','plate','column','industry_template'],
        'industry_specific_requirements': ['business_variable_template','cannot_conclude_rules','claim_mapping'],
        'not_yet_generalized': ['automatic_org_id_discovery_for_all_tickers','industry_specific_evidence_extraction_for_all_sectors','real_pdf_download_text_extraction_for_non_baseline_tickers']
    }}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
