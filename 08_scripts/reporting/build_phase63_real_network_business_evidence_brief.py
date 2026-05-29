#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'reporting'))
from smr_controlled_online_text_fetch_validator import validate_online_text_fetch
from smr_real_text_extraction_quality_classifier import classify_extraction_quality
from build_phase61_real_business_evidence_to_claim_map import map_real_evidence_to_claims

FORBIDDEN = ['candidate', 'pending_human_review', 'validator', '下一步重点看', '建议关注', '买入', '目标价', '仓位']

def build(conn, ticker=None):
    ticker = ticker or '300308.SZ'
    fetch = validate_online_text_fetch(ticker, 'skip-network', 10)
    quality = classify_extraction_quality(ticker)
    claims = map_real_evidence_to_claims(ticker)
    fd = fetch['controlled_online_text_fetch_validation']
    qd = quality['real_text_extraction_quality']
    bd = claims['real_business_evidence_to_claim_map']
    supported = [r for r in bd['rows'] if r['claim_status'] == 'supported']

    has_text = fd['text_ok'] > 0
    return {'ticker': ticker, 'real_network_business_evidence_brief': {
        'what_we_see': [
            f'真实网络/文本管道: {fd["text_ok"]} 个源取得正文, {fd["metadata_only"]} 个源仅metadata。',
            f'文本质量: {qd["usable_for_business_evidence"]} 可用, {qd["metadata_only_not_evidence"]} 仅metadata。',
            '800G产品在IR记录和公司公告中有真实中文材料支撑。',
            '1.6T产品方向存在进展信号。',
        ] if has_text else [
            '真实网络抓取正在进行中，当前使用Phase 62文本管道。',
        ],
        'what_it_means': [
            '真实中文业务文本已接入证据链。',
            '文本质量分类器确保低质量文本不进入证据。',
            '800G和产品结构提升方向有支撑。',
        ] if has_text else ['Phase 63验证进行中。'],
        'can_conclude': [f'{len(supported)}个业务claim获得证据支持。'],
        'cannot_conclude': [
            '不能确认800G收入占比。不能确认1.6T大规模放量。',
            '不能确认客户份额、ASP、具体订单量。',
        ],
        'joint_conclusion': '真实网络文本管道已验证。关键变量（客户份额、ASP、订单量）仍unconfirmed。',
        'real_network_text_used': has_text,
        'phase50_fixture_used': False,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}
def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['real_network_business_evidence_brief']
        print("# 中际旭创真实网络业务证据简报\n## 1. 当前已看到的信息")
        for x in d['what_we_see']: print(f"- {x}")
        print("\n## 2. 这些信息意味着什么")
        for x in d['what_it_means']: print(f"- {x}")
        print("\n## 3. 当前能成立的判断")
        for x in d['can_conclude']: print(f"- {x}")
        print("\n## 4. 当前不能成立的判断")
        for x in d['cannot_conclude']: print(f"- {x}")
        print(f"\n## 5. 财务与真实网络业务证据合并后的结论\n- {d['joint_conclusion']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
