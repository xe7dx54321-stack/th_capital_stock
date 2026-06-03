def build_static_html_layout():
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TH Capital Research Console v1</title>
<style>/* CSS injected */</style>
</head>
<body>
<header class="console-header">
<h1>TH Capital Research Console</h1>
<div class="status-bar" id="system-status"></div>
</header>
<nav class="nav-bar" id="navigation"></nav>
<main class="console-main">
<section id="ticker-cards"></section>
<section id="thesis-library"></section>
<section id="evidence-sources"></section>
<section id="daily-delivery"></section>
<section id="owner-actions"></section>
<section id="gap-risk"></section>
<section id="feedback-template"></section>
<section id="artifact-links"></section>
</main>
<footer class="console-footer">
<p>Research-only console. No trade recommendations, target prices, or position sizing.</p>
</footer>
</body>
</html>'''
    return {"phase141_static_html_layout_builder": {"layout": html, "ready": True, "mock_used": False, "fixture_used": False}}
