# Phase174 trade term validator debt recorder
def build_trade_term_debt_recorder():
    return {"phase174_trade_term_debt":{
        "debt_recorded":True,
        "known_issue":"trade_term_validator_uses_substring_matching",
        "false_positive_example":"additional_matched_as_add",
        "affected_candidates_in_phase170":["INTC","MU"],
        "mitigation_applied":"rationale_rewritten_from_additional_to_further",
        "root_cause":"TRADE_TERMS list includes short tokens like add,exit,hold that trigger substring false positives",
        "recommended_fix":"upgrade_validator_to_word_boundary_or_token_aware_matching",
        "debt_severity":"low",
        "debt_not_blocking":True,
        "cannot_conclude":["this_is_technical_debt_record_not_security_issue"],
        "mock_used":False,"fixture_used":False
    }}
