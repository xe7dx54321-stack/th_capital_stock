def build_phase142_domain_registry():
    domains = {
        'phase142_config': {'desc': 'Phase142 config', 'category': 'input'},
        'phase141_dashboard_loader': {'desc': 'Load Phase141 dashboard', 'category': 'input'},
        'phase138_thesis_loader': {'desc': 'Load Phase138 thesis library', 'category': 'input'},
        'phase137_deep_dive_loader': {'desc': 'Load Phase137 deep dive', 'category': 'input'},
        'phase134_console_loader': {'desc': 'Load Phase134 console', 'category': 'input'},
        'ticker_detail_data_model': {'desc': 'Detail page data model', 'category': 'core'},
        'ticker_detail_page_generator': {'desc': 'Generate detail HTML pages', 'category': 'output'},
        'thesis_timeline_builder': {'desc': 'Thesis timeline per ticker', 'category': 'output'},
        'evidence_chain_builder': {'desc': 'Evidence chain per ticker', 'category': 'output'},
        'deep_dive_history_builder': {'desc': 'Deep dive history', 'category': 'output'},
        'financial_valuation_snapshot_builder': {'desc': 'Financial snapshot', 'category': 'output'},
        'source_limitation_detail_builder': {'desc': 'Source limitations', 'category': 'output'},
        'gap_risk_detail_builder': {'desc': 'Gap/risk detail', 'category': 'output'},
        'owner_action_detail_builder': {'desc': 'Owner actions', 'category': 'output'},
        'ticker_artifact_link_builder': {'desc': 'Artifact links', 'category': 'output'},
        'ticker_detail_index_builder': {'desc': 'Detail index page', 'category': 'output'},
        'homepage_link_update_builder': {'desc': 'Update homepage links', 'category': 'output'},
        'detail_css_extension': {'desc': 'CSS for detail pages', 'category': 'output'},
        'detail_open_instruction': {'desc': 'Open instructions', 'category': 'output'},
        'detail_quality_gate': {'desc': 'Quality gate', 'category': 'safety'},
        'detail_cannot_conclude_guard': {'desc': 'Guard', 'category': 'safety'},
        'detail_backlog_update': {'desc': 'Backlog', 'category': 'output'},
    }
    return {
        'phase142_domain_registry': {
            'total': len(domains),
            'all_research_only': True,
            'domains': {k: {**v, 'research_only': True} for k, v in domains.items()},
            'mock_used': False,
            'fixture_used': False
        }
    }
