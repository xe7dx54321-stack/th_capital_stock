import os
def w(p,c): os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w',encoding='utf-8').write(c)

TEMPLATE = "import json,sys,os\nsys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','lib'))\nfrom {mod} import {fn}\ndef main():\n r={fn}()\n if '--json' in sys.argv: print(json.dumps(r,ensure_ascii=False,indent=2))\n else: print(json.dumps(r,ensure_ascii=False))\nif __name__=='__main__':main()\n"

reports = [
    ('build_phase121_config_report.py', 'smr_phase121_config', 'load_config'),
    ('build_phase121_domain_registry_report.py', 'smr_phase121_domain_registry', 'build_domain_registry'),
    ('build_phase121_target_universe.py', 'smr_phase121_target_universe', 'build_target_universe'),
    ('build_phase121_source_candidate_registry.py', 'smr_phase121_source_candidate_registry', 'build_source_candidate_registry'),
    ('build_phase121_official_filing_registry.py', 'smr_phase121_official_filing_registry', 'build_official_filing_registry'),
    ('build_phase121_market_quote_registry.py', 'smr_phase121_market_quote_registry', 'build_market_quote_registry'),
    ('build_phase121_news_event_registry.py', 'smr_phase121_news_event_registry', 'build_news_event_registry'),
    ('build_phase121_transcript_guidance_registry.py', 'smr_phase121_transcript_guidance_registry', 'build_transcript_guidance_registry'),
    ('build_phase121_source_access_policy.py', 'smr_phase121_source_access_policy', 'build_source_access_policy'),
    ('build_phase121_connector_skeleton.py', 'smr_phase121_connector_skeleton', 'build_connector_skeleton'),
    ('build_phase121_hk_external_adapter.py', 'smr_phase121_hk_external_adapter', 'build_hk_external_adapter'),
    ('build_phase121_us_external_adapter.py', 'smr_phase121_us_external_adapter', 'build_us_external_adapter'),
    ('build_phase121_source_coverage_matrix.py', 'smr_phase121_source_coverage_matrix', 'build_source_coverage_matrix'),
    ('build_phase121_external_evidence_normalization.py', 'smr_phase121_external_evidence_normalization', 'build_external_evidence_normalization'),
    ('build_phase121_cross_source_reliability.py', 'smr_phase121_cross_source_reliability', 'build_cross_source_reliability'),
    ('build_phase121_source_gap_register.py', 'smr_phase121_source_gap_register', 'build_source_gap_register'),
    ('build_phase121_integration_report.py', 'smr_phase121_integration_report', 'build_integration_report'),
    ('build_phase121_expansion_board.py', 'smr_phase121_expansion_board', 'build_expansion_board'),
    ('build_phase121_cannot_conclude_guard.py', 'smr_phase121_cannot_conclude_guard', 'run_cannot_conclude_guard'),
    ('build_phase121_backlog_update.py', 'smr_phase121_backlog_update', 'build_backlog_update'),
]

for name, mod, fn in reports:
    w(f'08_scripts/reporting/{name}', TEMPLATE.format(mod=mod, fn=fn))

print(f'{len(reports)} reporting files done')