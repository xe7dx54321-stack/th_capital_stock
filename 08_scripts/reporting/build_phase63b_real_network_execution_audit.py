#!/usr/bin/env python3
"""Phase 63b: Real Network Execution Audit Report."""
import argparse, json, sys, time
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_real_network_execution_audit import run_real_network_audit

def build(conn, ticker=None):
    return run_real_network_audit(ticker or '300308.SZ')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ')
    p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker); d=r['phase63b_real_network_execution_audit']

    if a.markdown:
        print(f"# Phase 63b 真实网络执行审计\n- Ticker: {r['ticker']}")
        print(f"- 网络可达(任一源): {d['network_available_for_any_source']}")
        print(f"- CNINFO: {d['cninfo_reachable']} | IRM: {d['irm_reachable']} | SZSE: {d['szse_reachable']}")
        print(f"- 成功: {d['sources_success']}/{d['sources_checked']} | 失败: {d['sources_failed']}")
        print(f"- 取得文本: {d['sources_with_text']} | Mock: {d['mock_used']} | Fixture: {d['fixture_used']}")
        print("\n## 网络源详情")
        for row in d['network_rows']:
            icon = 'OK' if row['network_success'] else 'FAIL'
            print(f"- [{icon}] {row['source_id']}: {row['failure_reason'] or 'success'} ({row['content_length']} bytes)")
        print("\n## PDF源详情")
        for row in d['pdf_rows']:
            print(f"- [{row['download_tested']}] {row['source_id']}: {row['failure_reason']}")
    else:
        print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
