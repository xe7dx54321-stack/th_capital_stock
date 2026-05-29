#!/usr/bin/env python3
"""Phase 63b: Real Network Source Execution Audit.
Honest audit of what actually works when executing real network fetches.
Records success/failure with reasons, no mock, no fixture.
"""
from __future__ import annotations
import json, time, hashlib, urllib.request, urllib.parse
from pathlib import Path
from typing import Any

NETWORK_AUDIT_SOURCES = [
    # CNINFO sources
    {'source_id': 'cninfo_metadata', 'source_type': 'cninfo_metadata',
     'description': 'CNINFO announcement metadata API',
     'url': 'http://www.cninfo.com.cn/new/hisAnnouncement/query',
     'method': 'POST', 'expected_content': 'json'},
    {'source_id': 'cninfo_disclosure_page', 'source_type': 'cninfo_web',
     'description': 'CNINFO main disclosure page',
     'url': 'http://www.cninfo.com.cn/new/disclosure',
     'method': 'GET', 'expected_content': 'html'},
    # IRM sources
    {'source_id': 'irm_company_questions', 'source_type': 'irm_interactive_qa',
     'description': 'IRM company questions API',
     'url': 'https://irm.cninfo.com.cn/ircs/company/companyQuestion',
     'method': 'GET', 'expected_content': 'json'},
    {'source_id': 'irm_main_page', 'source_type': 'irm_web',
     'description': 'IRM main index page',
     'url': 'https://irm.cninfo.com.cn/ircs/index',
     'method': 'GET', 'expected_content': 'html'},
    # SZSE sources
    {'source_id': 'szse_main', 'source_type': 'exchange_web',
     'description': 'SZSE main website',
     'url': 'http://www.szse.cn',
     'method': 'GET', 'expected_content': 'html'},
    # Company official site
    {'source_id': 'company_ir_page', 'source_type': 'company_official',
     'description': 'Company IR page (placeholder)',
     'url': '',
     'method': 'GET', 'expected_content': 'html'},
]

PDF_AUDIT_SOURCES = [
    {'source_id': 'pdf_cninfo_annual_report', 'source_type': 'cninfo_annual_report',
     'description': 'CNINFO annual report PDF download',
     'url_hint': 'from cninfo metadata adjunctUrl', 'download_tested': False},
    {'source_id': 'pdf_cninfo_quarterly_report', 'source_type': 'cninfo_quarterly_report',
     'description': 'CNINFO quarterly report PDF download',
     'url_hint': 'from cninfo metadata adjunctUrl', 'download_tested': False},
    {'source_id': 'pdf_cninfo_announcement', 'source_type': 'cninfo_announcement',
     'description': 'CNINFO announcement PDF download',
     'url_hint': 'from cninfo metadata adjunctUrl', 'download_tested': False},
]


def _test_single_endpoint(source: dict, timeout: int = 15) -> dict:
    """Test a single network endpoint and return honest results."""
    result = {
        'source_id': source['source_id'],
        'source_type': source['source_type'],
        'description': source['description'],
        'network_attempted': True,
        'network_success': False,
        'http_status': None,
        'content_type': None,
        'content_length': 0,
        'content_is_expected_format': False,
        'failure_reason': '',
        'download_success': False,
        'text_extracted': False,
    }

    if not source.get('url'):
        result['network_attempted'] = False
        result['failure_reason'] = 'no_url_provided'
        return result

    try:
        req = urllib.request.Request(source['url'], headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/json,application/xhtml+xml,*/*',
        })

        if source['method'] == 'POST':
            stock = '300308'
            data = urllib.parse.urlencode({
                'pageNum': 1, 'pageSize': 5,
                'column': 'szse', 'tabName': 'fulltext',
                'plate': 'sz', 'stock': stock,
                'searchkey': '', 'secid': '', 'category': '', 'trade': '', 'seDate': '',
            }).encode('utf-8')
            req = urllib.request.Request(source['url'], data=data, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            })

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result['network_success'] = True
            result['http_status'] = resp.status
            result['content_type'] = resp.headers.get('Content-Type', '')
            body = resp.read()
            result['content_length'] = len(body)
            result['download_success'] = len(body) > 100

            # Check format
            if source['expected_content'] == 'json':
                try:
                    json.loads(body.decode('utf-8'))
                    result['content_is_expected_format'] = True
                    result['text_extracted'] = True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result['content_is_expected_format'] = False
                    if b'<' in body[:10]:
                        result['failure_reason'] = 'got_html_not_json'
                    else:
                        result['failure_reason'] = 'not_valid_json'
            elif source['expected_content'] == 'html':
                result['content_is_expected_format'] = b'<' in body[:10]
                result['text_extracted'] = len(body) > 500
                if not result['content_is_expected_format']:
                    result['failure_reason'] = 'not_html'

    except urllib.error.HTTPError as e:
        result['failure_reason'] = f'http_error_{e.code}'
        result['http_status'] = e.code
    except urllib.error.URLError as e:
        result['failure_reason'] = 'network_unreachable'
        if 'timed out' in str(e.reason).lower():
            result['failure_reason'] = 'connection_timed_out'
    except Exception as e:
        result['failure_reason'] = f'error: {str(e)[:80]}'

    return result


def run_real_network_audit(ticker: str = '300308.SZ') -> dict:
    """Run full network audit on all defined sources."""
    results = []
    for source in NETWORK_AUDIT_SOURCES:
        r = _test_single_endpoint(source)
        results.append(r)
        time.sleep(0.3)  # Be polite

    success_count = sum(1 for r in results if r['network_success'])
    fail_count = sum(1 for r in results if r['network_attempted'] and not r['network_success'])
    text_count = sum(1 for r in results if r['text_extracted'])

    # PDF audit - depends on network results
    pdf_results = []
    cninfo_reachable = any(r['network_success'] and 'cninfo' in r['source_id'] for r in results)
    for ps in PDF_AUDIT_SOURCES:
        pdf_results.append({
            'source_id': ps['source_id'],
            'source_type': ps['source_type'],
            'description': ps['description'],
            'download_tested': False,
            'download_success': False,
            'pdf_parse_success': False,
            'text_extracted': False,
            'failure_reason': 'cninfo_metadata_not_reachable' if not cninfo_reachable else 'pdf_not_downloaded_yet',
            'ocr_used': False,
            'raw_pdf_saved': False,
        })

    return {
        'ticker': ticker,
        'phase63b_real_network_execution_audit': {
            'network_attempted': True,
            'network_available_for_any_source': success_count > 0,
            'sources_checked': len(results),
            'sources_success': success_count,
            'sources_failed': fail_count,
            'sources_with_text': text_count,
            'cninfo_reachable': cninfo_reachable,
            'irm_reachable': any(r['network_success'] and 'irm' in r['source_id'] for r in results),
            'szse_reachable': any(r['network_success'] and 'szse' in r['source_id'] for r in results),
            'raw_content_saved': False,
            'ocr_used': False,
            'mock_used': False,
            'fixture_used': False,
            'pending_created': 0,
            'note': 'Honest audit of real network source availability. No mock, no fixture.',
            'network_rows': results,
            'pdf_rows': pdf_results,
        }
    }
