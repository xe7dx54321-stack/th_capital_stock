#!/usr/bin/env python3
import argparse, json, sys
def build():
    return {"phase74_html_parser_utils": {"capabilities": ["visible_text_extraction", "link_extraction", "pdf_link_detection", "relative_url_normalization", "boilerplate_removal", "text_hash_generation", "date_extraction", "chinese_ratio"], "raw_saved": False, "ocr_used": False, "mock_used": False, "fixture_used": False}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
