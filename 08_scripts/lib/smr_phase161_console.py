def build_console_page_html():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Owner Decision Submission UI Feedback</title>
<link rel="stylesheet" href="phase161_submission_feedback.css">
</head>
<body>
<div class="console-container">
<header>
<h1>Owner Decision Submission UI Feedback Center</h1>
<p class="subtitle">Example Pack Integration | Sandbox Validation | Phase159 Submission Status</p>
</header>

<nav class="console-nav">
<a href="#example-library">Example Library</a>
<a href="#sandbox-results">Sandbox Results</a>
<a href="#safe-manifest">Safe Manifest</a>
<a href="#quarantine">Quarantine</a>
<a href="#phase159-status">Phase159 Status</a>
<a href="#workflow">Workflow</a>
<a href="#commands">Commands</a>
</nav>

<div id="example-library" class="section">
<h2>Example Library</h2>
<div id="example-library-content"></div>
</div>

<div id="sandbox-results" class="section">
<h2>Sandbox Validation Results</h2>
<div id="sandbox-results-content"></div>
</div>

<div id="safe-manifest" class="section">
<h2>Safe Manifest Explanation</h2>
<div id="safe-manifest-content"></div>
</div>

<div id="quarantine" class="section">
<h2>Quarantine Explanation</h2>
<div id="quarantine-content"></div>
</div>

<div id="phase159-status" class="section">
<h2>Phase159 Submission Status</h2>
<div id="phase159-status-content"></div>
</div>

<div id="workflow" class="section">
<h2>Real Input Workflow</h2>
<div id="workflow-content"></div>
</div>

<div id="commands" class="section">
<h2>Next Commands</h2>
<div id="commands-content"></div>
</div>

<footer>
<p class="footer-disclaimer">Research only. Not investment advice. All activations are preview-only. No real trades executed. No Watch/Core tier updates. Execution blocked.</p>
</footer>
</div>
</body>
</html>"""
    return {
        "phase161_console_page": {
            "page_html": html,
            "page_generated": True,
            "static_html": True,
            "external_js": False,
            "external_cdn": False,
            "local_server": False,
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_nav_integration():
    return {
        "phase161_nav_integration": {
            "integrated": True,
            "nav_items": [
                {"section": "example_library", "label": "Example Library", "href": "#example-library"},
                {"section": "sandbox_results", "label": "Sandbox Results", "href": "#sandbox-results"},
                {"section": "safe_manifest", "label": "Safe Manifest", "href": "#safe-manifest"},
                {"section": "quarantine", "label": "Quarantine", "href": "#quarantine"},
                {"section": "phase159_status", "label": "Phase159 Status", "href": "#phase159-status"},
                {"section": "workflow", "label": "Workflow", "href": "#workflow"},
                {"section": "commands", "label": "Commands", "href": "#commands"}
            ],
            "mock_used": False,
            "fixture_used": False
        }
    }

def build_css_extension():
    css = """
.console-container { max-width: 1200px; margin: 0 auto; padding: 20px; font-family: system-ui, sans-serif; }
header { text-align: center; margin-bottom: 30px; }
.subtitle { color: #666; font-size: 0.9em; }
.console-nav { display: flex; gap: 15px; justify-content: center; margin-bottom: 30px; flex-wrap: wrap; }
.console-nav a { color: #2563eb; text-decoration: none; padding: 5px 10px; border: 1px solid #2563eb; border-radius: 4px; }
.section { margin-bottom: 30px; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }
.example-card { padding: 15px; margin: 10px 0; border-radius: 6px; }
.example-card.valid { border-left: 4px solid #16a34a; background: #f0fdf4; }
.example-card.invalid { border-left: 4px solid #dc2626; background: #fef2f2; }
.safe-badge { color: #16a34a; font-weight: bold; }
.reject-badge { color: #dc2626; font-weight: bold; }
.danger-tag { color: #dc2626; font-weight: bold; }
.sandbox-table, .status-table { border-collapse: collapse; width: 100%; max-width: 500px; }
.sandbox-table td, .status-table td { padding: 8px; border: 1px solid #e5e7eb; }
td.safe { color: #16a34a; font-weight: bold; }
td.invalid, td.quarantine { color: #dc2626; font-weight: bold; }
td.zero { color: #2563eb; font-weight: bold; }
td.pass { color: #16a34a; }
td.pending { color: #d97706; }
.explanation-box { padding: 15px; background: #f8fafc; border-radius: 6px; }
.not-statement { color: #dc2626; font-weight: bold; font-style: italic; }
.preview-note { color: #2563eb; font-weight: bold; }
.workflow-steps li { margin: 10px 0; }
.command-box code { display: block; background: #1e293b; color: #e2e8f0; padding: 8px; margin: 5px 0; border-radius: 4px; }
.safety-note { color: #d97706; font-weight: bold; }
.status-message { padding: 10px; border-radius: 4px; }
.status-message.pending { background: #fef3c7; color: #92400e; }
.warning { color: #dc2626; font-weight: bold; background: #fef2f2; padding: 10px; border-radius: 4px; }
.footer-disclaimer { text-align: center; color: #666; font-size: 0.85em; padding: 20px; border-top: 1px solid #e5e7eb; }
"""
    return {
        "phase161_css_extension": {
            "css": css,
            "static_only": True,
            "no_external_fonts": True,
            "mock_used": False,
            "fixture_used": False
        }
    }
