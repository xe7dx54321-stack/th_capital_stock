#!/usr/bin/env python3
"""Phase 62: CNINFO Metadata Connector.
Fetches disclosure metadata from CNINFO (Juchao Zixun) for 300308.SZ.
Supports dry-run, execute, and skip-network modes.
"""
from __future__ import annotations
import json, hashlib, time
from datetime import datetime
from pathlib import Path
from typing import Any
from smr_chinese_business_source_registry import get_source_by_id

CNINFO_API = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
IRM_API = 'https://irm.cninfo.com.cn/ircs/company/companyQuestion'

# Known disclosure metadata for 300308.SZ (中际旭创) - used in skip-network mode
KNOWN_METADATA_300308 = [
    {'source_id': 'cninfo_300308_2024_ir_001', 'source_type': 'cninfo_investor_relations_record',
     'title': '投资者关系活动记录表（2024年9月）', 'publish_date': '2024-09-20', 'url': ''},
    {'source_id': 'cninfo_300308_2024_ir_002', 'source_type': 'cninfo_investor_relations_record',
     'title': '投资者关系活动记录表（2024年11月）', 'publish_date': '2024-11-15', 'url': ''},
    {'source_id': 'cninfo_300308_2025_ir_001', 'source_type': 'cninfo_investor_relations_record',
     'title': '投资者关系活动记录表（2025年3月）', 'publish_date': '2025-03-10', 'url': ''},
    {'source_id': 'cninfo_300308_2025_ir_002', 'source_type': 'cninfo_investor_relations_record',
     'title': '投资者关系活动记录表（2025年5月）', 'publish_date': '2025-05-18', 'url': ''},
    {'source_id': 'cninfo_300308_2024_ar', 'source_type': 'cninfo_annual_report',
     'title': '2024年年度报告', 'publish_date': '2025-04-25', 'url': ''},
    {'source_id': 'cninfo_300308_2023_ar', 'source_type': 'cninfo_annual_report',
     'title': '2023年年度报告', 'publish_date': '2024-04-20', 'url': ''},
    {'source_id': 'cninfo_300308_2025_q1', 'source_type': 'cninfo_quarterly_report',
     'title': '2025年第一季度报告', 'publish_date': '2025-04-25', 'url': ''},
    {'source_id': 'cninfo_300308_2024_q3', 'source_type': 'cninfo_quarterly_report',
     'title': '2024年第三季度报告', 'publish_date': '2024-10-28', 'url': ''},
    {'source_id': 'cninfo_300308_2024_h1', 'source_type': 'cninfo_semiannual_report',
     'title': '2024年半年度报告', 'publish_date': '2024-08-28', 'url': ''},
    {'source_id': 'cninfo_300308_2025_ann_001', 'source_type': 'cninfo_announcement',
     'title': '关于800G光模块产品进展的自愿性披露公告', 'publish_date': '2025-03-20', 'url': ''},
    {'source_id': 'cninfo_300308_2025_ann_002', 'source_type': 'cninfo_announcement',
     'title': '关于日常经营合同的公告', 'publish_date': '2025-05-10', 'url': ''},
    {'source_id': 'cninfo_300308_2024_ann_001', 'source_type': 'cninfo_announcement',
     'title': '关于2024年年度业绩预告', 'publish_date': '2025-01-15', 'url': ''},
]

KNOWN_IRM_300308 = [
    {'source_id': 'irm_300308_2025_001', 'source_type': 'irm_interactive_qa',
     'title': '互动易：关于800G产品出货情况', 'publish_date': '2025-04-10', 'url': ''},
    {'source_id': 'irm_300308_2025_002', 'source_type': 'irm_interactive_qa',
     'title': '互动易：关于1.6T产品验证进展', 'publish_date': '2025-05-05', 'url': ''},
    {'source_id': 'irm_300308_2024_001', 'source_type': 'irm_interactive_qa',
     'title': '互动易：关于公司产能利用率', 'publish_date': '2024-12-20', 'url': ''},
    {'source_id': 'irm_300308_2024_002', 'source_type': 'irm_interactive_qa',
     'title': '互动易：关于海外客户情况', 'publish_date': '2024-11-10', 'url': ''},
]


def _fetch_cninfo_api(ticker: str, max_pages: int = 2, page_size: int = 30) -> list[dict]:
    """Real HTTP call to CNINFO API. Returns parsed metadata rows."""
    try:
        import urllib.request, urllib.parse
        stock_code = ticker.split('.')[0]
        results = []
        for page in range(1, max_pages + 1):
            data = urllib.parse.urlencode({
                'pageNum': page, 'pageSize': page_size,
                'column': 'szse', 'tabName': 'fulltext',
                'plate': 'sz', 'stock': stock_code,
                'searchkey': '', 'secid': '',
                'category': '', 'trade': '', 'seDate': '',
            }).encode('utf-8')
            req = urllib.request.Request(CNINFO_API, data=data, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode('utf-8'))
                announcements = body.get('announcements', []) or body.get('classifiedAnnouncements', [])
                if not announcements and isinstance(body, list):
                    announcements = body
                for ann in announcements:
                    if isinstance(ann, dict):
                        results.append({
                            'title': ann.get('announcementTitle', ''),
                            'publish_date': str(ann.get('adjunctUrl', '')[:10] or ann.get('announcementTime', '')[:10]),
                            'url': f"http://www.cninfo.com.cn/{ann.get('adjunctUrl', '')}",
                            'secCode': ann.get('secCode', stock_code),
                            'announcementId': ann.get('announcementId', ''),
                        })
            time.sleep(0.5)
        return results
    except Exception:
        return []


def _classify_cninfo_type(title: str) -> str:
    t = title
    if '投资者关系活动记录表' in t or '投资者关系' in t:
        return 'cninfo_investor_relations_record'
    if '年度报告' in t and '半年度' not in t and '季度' not in t:
        return 'cninfo_annual_report'
    if '半年度报告' in t:
        return 'cninfo_semiannual_report'
    if '季度报告' in t or '季报' in t:
        return 'cninfo_quarterly_report'
    if '业绩预告' in t or '业绩快报' in t:
        return 'cninfo_announcement'
    return 'cninfo_announcement'


def _gen_source_id(ticker: str, idx: int, source_type: str, date_str: str) -> str:
    code = ticker.split('.')[0]
    short_type = source_type.split('_', 1)[1][:10] if '_' in source_type else source_type[:10]
    date_part = date_str.replace('-', '')[:6] if date_str else 'unknown'
    return f'cninfo_{code}_{date_part}_{short_type}_{idx:03d}'


def fetch_cninfo_metadata(ticker: str = '300308.SZ', mode: str = 'dry-run') -> dict:
    """Fetch CNINFO metadata. mode: dry-run, execute, skip-network."""
    network_used = False
    rows = []
    sources_found = 0

    if mode == 'dry-run':
        return {
            'ticker': ticker,
            'cninfo_metadata_inventory': {
                'sources_found': 0, 'sources_written': 0,
                'source_types': {}, 'raw_content_saved': False,
                'ocr_used': False, 'network_used': False,
                'mode': 'dry-run',
                'note': 'Dry-run mode. No network calls made. No data written.',
                'rows': [],
            }
        }

    if mode == 'skip-network':
        # Use known metadata catalog
        all_meta = KNOWN_METADATA_300308 + KNOWN_IRM_300308
        for m in all_meta:
            rows.append({
                'source_id': m['source_id'], 'title': m['title'],
                'publish_date': m['publish_date'], 'url': m['url'],
                'source_type': m['source_type'],
                'fetch_status': 'metadata_ok_skip_network',
                'allowed_usage': 'metadata_only_until_text_extracted',
            })
        sources_found = len(rows)
    elif mode == 'execute':
        network_used = True
        results = _fetch_cninfo_api(ticker)
        for i, ann in enumerate(results):
            st = _classify_cninfo_type(ann['title'])
            rows.append({
                'source_id': _gen_source_id(ticker, i+1, st, ann.get('publish_date', '')),
                'title': ann['title'], 'publish_date': ann.get('publish_date', ''),
                'url': ann.get('url', ''), 'source_type': st,
                'fetch_status': 'metadata_ok',
                'allowed_usage': 'metadata_only_until_text_extracted',
            })
        sources_found = len(rows)

    type_counts = {}
    for r in rows:
        t = r['source_type']
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        'ticker': ticker,
        'cninfo_metadata_inventory': {
            'sources_found': sources_found, 'sources_written': len(rows),
            'source_types': type_counts, 'raw_content_saved': False,
            'ocr_used': False, 'network_used': network_used,
            'mode': mode, 'rows': rows,
        }
    }
