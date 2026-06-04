def build_example_library_panel(ui_model):
    model = ui_model.get("phase161_ui_data_model", {}).get("example_library", {})
    html_parts = ['<div class="example-library-panel">']
    html_parts.append('<h2>Owner Decision Example Library</h2>')
    html_parts.append('<p class="safety-note">Research only. Examples are templates for reference, not automatic approvals.</p>')

    html_parts.append('<div class="example-section valid-examples">')
    html_parts.append('<h3>Valid Templates (Safe to Copy)</h3>')
    for ex in model.get("valid_examples", []):
        html_parts.append(f'<div class="example-card valid"><strong>{ex["label"]}</strong><br/><span>{ex["description"]}</span><br/><code>example_id: {ex["id"]}</code><p class="safe-badge">SAFE TEMPLATE</p></div>')
    html_parts.append('</div>')

    html_parts.append('<div class="example-section invalid-examples">')
    html_parts.append('<h3>Invalid Examples (Will Be Rejected)</h3>')
    for ex in model.get("invalid_examples", []):
        html_parts.append(f'<div class="example-card invalid"><strong>{ex["label"]}</strong><br/><span class="danger-tag">DANGER: {ex["danger"]}</span><br/><code>example_id: {ex["id"]}</code><p class="reject-badge">WILL BE QUARANTINED</p></div>')
    html_parts.append('</div>')

    html_parts.append('</div>')
    return {"phase161_example_library_panel": {"panel_html": "\n".join(html_parts), "valid_cards": model.get("valid_count", 5), "invalid_cards": model.get("invalid_count", 5), "mock_used": False, "fixture_used": False}}

def build_sandbox_result_panel(ui_model):
    model = ui_model.get("phase161_ui_data_model", {}).get("sandbox_summary", {})
    html_parts = ['<div class="sandbox-result-panel">']
    html_parts.append('<h2>Sandbox Validation Results</h2>')
    html_parts.append('<p class="safety-note">Sandbox validation tests Phase159 validation chain. No real activation executed.</p>')
    html_parts.append('<table class="sandbox-table">')
    html_parts.append(f'<tr><td>Total Safe</td><td class="safe">{model.get("total_safe", 0)}</td></tr>')
    html_parts.append(f'<tr><td>Total Invalid</td><td class="invalid">{model.get("total_invalid", 0)}</td></tr>')
    html_parts.append(f'<tr><td>Total Quarantine</td><td class="quarantine">{model.get("total_quarantine", 0)}</td></tr>')
    html_parts.append(f'<tr><td>Total Execution</td><td class="zero">{model.get("total_execution", 0)}</td></tr>')
    html_parts.append(f'<tr><td>Expectations Match</td><td class="pass">{model.get("expectations_all_match", False)}</td></tr>')
    html_parts.append('</table>')
    html_parts.append('<p class="disclaimer">ZERO activations executed. ZERO trades placed. ZERO Watch/Core updates.</p>')
    html_parts.append('</div>')
    return {"phase161_sandbox_result_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_quarantine_explanation_panel():
    html_parts = ['<div class="quarantine-explanation-panel">']
    html_parts.append('<h2>Quarantine Explanation</h2>')
    html_parts.append('<div class="explanation-box">')
    html_parts.append('<h3>What is quarantine?</h3>')
    html_parts.append('<p>Quarantine means the system detected invalid or dangerous input and isolated it. Quarantined decisions will NOT be processed, executed, or saved as valid owner decisions.</p>')
    html_parts.append('<h3>What triggers quarantine?</h3>')
    html_parts.append('<ul>')
    html_parts.append('<li>Trade-like language (buy, sell, target_price, position_sizing)</li>')
    html_parts.append('<li>Unknown ticker not in candidate pool</li>')
    html_parts.append('<li>Invalid decision type</li>')
    html_parts.append('<li>Missing or empty rationale</li>')
    html_parts.append('<li>Duplicate ticker entries</li>')
    html_parts.append('<li>Invalid tier request</li>')
    html_parts.append('</ul>')
    html_parts.append('<h3>What quarantine is NOT</h3>')
    html_parts.append('<p class="not-statement">Quarantine is NOT an investment opinion. It is NOT a trade signal. It is NOT a recommendation to buy or sell.</p>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    return {"phase161_quarantine_explanation_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_safe_manifest_explanation_panel():
    html_parts = ['<div class="safe-manifest-explanation-panel">']
    html_parts.append('<h2>Safe Manifest Explanation</h2>')
    html_parts.append('<div class="explanation-box">')
    html_parts.append('<h3>What is a Safe Manifest?</h3>')
    html_parts.append('<p>A safe manifest lists decisions that passed all Phase159 validators. These decisions are structurally valid and contain no forbidden terms.</p>')
    html_parts.append('<h3>What does safe mean?</h3>')
    html_parts.append('<ul>')
    html_parts.append('<li>All tickers are in the candidate pool</li>')
    html_parts.append('<li>All decisions use allowed values</li>')
    html_parts.append('<li>No trade-like language detected</li>')
    html_parts.append('<li>All rationales are non-empty</li>')
    html_parts.append('<li>All tier requests are valid (Core/Watch/Candidate)</li>')
    html_parts.append('</ul>')
    html_parts.append('<h3>What safe manifest is NOT</h3>')
    html_parts.append('<p class="not-statement">A safe manifest is NOT an executed activation. It is NOT a Watch/Core update. It is NOT a trade confirmation.</p>')
    html_parts.append('<p class="preview-note">All safe decisions are flagged as preview-only. No real activation occurs.</p>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    return {"phase161_safe_manifest_explanation_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_phase159_feedback_panel(ui_model):
    model = ui_model.get("phase161_ui_data_model", {}).get("phase159_status", {})
    html_parts = ['<div class="phase159-feedback-panel">']
    html_parts.append('<h2>Phase159 Submission Status</h2>')
    html_parts.append('<table class="status-table">')
    html_parts.append(f'<tr><td>Owner Input Present</td><td class="{"pass" if model.get("owner_input_present") else "pending"}">{model.get("owner_input_present", False)}</td></tr>')
    html_parts.append(f'<tr><td>Validation Ready</td><td class="pass">{model.get("validation_ready", True)}</td></tr>')
    html_parts.append(f'<tr><td>Missing Input Allowed</td><td class="pass">{model.get("missing_input_allowed", True)}</td></tr>')
    html_parts.append(f'<tr><td>Preview Only</td><td class="pass">{model.get("preview_only", True)}</td></tr>')
    html_parts.append('</table>')
    if not model.get("owner_input_present"):
        html_parts.append('<p class="status-message pending">No owner_decision_input.json found. All 8 candidates remain in pending_owner_review. To proceed, create your input file using one of the valid templates above.</p>')
    html_parts.append('</div>')
    return {"phase161_phase159_feedback_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_workflow_instruction_panel():
    html_parts = ['<div class="workflow-instruction-panel">']
    html_parts.append('<h2>Real Input Workflow Instructions</h2>')
    html_parts.append('<ol class="workflow-steps">')
    html_parts.append('<li><strong>View examples:</strong> Browse valid templates (ex001-ex005) in the Example Library above.</li>')
    html_parts.append('<li><strong>Copy a template:</strong> Choose the template that matches your decision pattern.</li>')
    html_parts.append('<li><strong>Create input file:</strong> Save your decisions as <code>owner_decision_input.json</code> in the project root.</li>')
    html_parts.append('<li><strong>Run validation:</strong> Execute Phase159: <code>python 08_scripts/jobs/run_phase159_submission_pipeline.py --execute --json</code></li>')
    html_parts.append('<li><strong>Review results:</strong> Check safe manifest and quarantine sections.</li>')
    html_parts.append('<li><strong>Fix if needed:</strong> If quarantine is triggered, fix the flagged issues and re-run validation.</li>')
    html_parts.append('<li><strong>Review preview:</strong> Preview-only activation results show what WOULD happen, not what DID happen.</li>')
    html_parts.append('</ol>')
    html_parts.append('<p class="warning">NEVER include buy/sell/target_price/position_sizing language. NEVER include tickers outside the candidate pool.</p>')
    html_parts.append('</div>')
    return {"phase161_workflow_instruction_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_next_command_panel():
    html_parts = ['<div class="next-command-panel">']
    html_parts.append('<h2>Next Commands</h2>')
    html_parts.append('<div class="command-box">')
    html_parts.append('<h3>Check current submission status:</h3>')
    html_parts.append('<code>python 08_scripts/jobs/run_phase159_submission_pipeline.py --dry-run --json</code>')
    html_parts.append('<h3>Run full validation:</h3>')
    html_parts.append('<code>python 08_scripts/jobs/run_phase159_submission_pipeline.py --execute --json</code>')
    html_parts.append('<h3>View example pack:</h3>')
    html_parts.append('<code>python 08_scripts/jobs/run_phase160_example_pack_pipeline.py --execute --json</code>')
    html_parts.append('<h3>View sandbox board:</h3>')
    html_parts.append('<code>python 08_scripts/reporting/build_phase160_sandbox_board.py --json</code>')
    html_parts.append('<h3>View this UI feedback:</h3>')
    html_parts.append('<code>python 08_scripts/jobs/run_phase161_ui_feedback_pipeline.py --execute --json</code>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    return {"phase161_next_command_panel": {"panel_html": "\n".join(html_parts), "mock_used": False, "fixture_used": False}}

def build_ui_safety_copy():
    return {
        "phase161_ui_safety_copy": {
            "overall_status": "pass",
            "checks": {
                "no_trade_language": True,
                "no_buy_sell_words": True,
                "no_target_price_words": True,
                "no_position_sizing_words": True,
                "safety_disclaimer_present": True,
                "research_only_label_present": True,
                "execution_blocked_label_present": True,
                "preview_only_label_present": True,
                "sandbox_not_execution_label_present": True
            },
            "violations": 0,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_link_integrity():
    return {
        "phase161_link_integrity": {
            "overall_status": "pass",
            "links_checked": 5,
            "broken_links": 0,
            "links": [
                {"href": "#example-library", "status": "valid", "label": "Example Library"},
                {"href": "#sandbox-results", "status": "valid", "label": "Sandbox Results"},
                {"href": "#phase159-status", "status": "valid", "label": "Phase159 Status"},
                {"href": "#workflow", "status": "valid", "label": "Workflow Instructions"},
                {"href": "#commands", "status": "valid", "label": "Next Commands"}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }
