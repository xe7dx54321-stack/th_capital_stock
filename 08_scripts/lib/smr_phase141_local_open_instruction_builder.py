def build_local_open_instruction():
    instruction = {
        "static_html_only": True,
        "external_js_allowed": False,
        "external_cdn_allowed": False,
        "local_server_enabled": False,
        "browser_automation_allowed": False,
        "open_method": "Double-click the generated HTML file in file explorer, or open with any browser via File > Open.",
        "output_path": "09_runbooks/generated/phase141_research_console.html",
        "output_path_ignored": True,
        "note": "This is a local-only static HTML file. No network calls, no CDN, no JS frameworks."
    }
    return {"phase141_local_open_instruction_builder": instruction}
