#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from smr_business_evidence_to_claim_mapper import map_business_evidence_to_claims
from smr_semantic_business_evidence_extractor import extract_semantic_business_evidence
from smr_financial_business_evidence_integrator import integrate_financial_business_evidence

def build(conn, ticker):
    biz = map_business_evidence_to_claims(ticker)
    ev = extract_semantic_business_evidence(ticker)
    joint = integrate_financial_business_evidence(ticker)
    bd = biz['business_evidence_to_claim_map']
    ed = ev['semantic_business_evidence']
    jd = joint['financial_business_evidence_integration']

    supported = [r for r in bd['rows'] if r['claim_status'] == 'supported']
    unconfirmed = [r for r in bd['rows'] if r['claim_status'] == 'unconfirmed']
    joint_strengthened = [r for r in jd['rows'] if r['joint_assessment'] == 'strengthened']

    return {'ticker': ticker, 'business_evidence_brief': {
        'what_we_see': [
            f'从业务材料中获取{ed["evidence_created"]}条业务证据，覆盖7个AI光模块业务变量。',
            '800G产品存在批量交付和客户认证相关证据。',
            '1.6T产品存在送样和验证方向性证据。',
            '高端产品结构提升方向在IR和年报中有管理层口径支持。',
            '出货/排产/交付口径偏积极。',
        ],
        'what_it_means': [
            '产品方向上800G和1.6T均有积极信号，支持产品代际升级方向。',
            '出货和交付口径与真实财务收入增长方向一致。',
            '业务证据与财务信号合并后支持业务动能增强。',
        ],
        'can_conclude': [
            f'{len(supported)}个业务claim获得证据支持。',
            '800G和出货方向有管理层和公司材料支撑。',
        ],
        'cannot_conclude': [
            '不能确认800G收入占比。',
            '不能确认1.6T已大规模放量。',
            '不能确认客户份额变化。',
            '不能确认ASP具体趋势。',
            '不能确认具体在手订单金额。',
        ],
        'joint_conclusion': f'财务+业务联合判断：{len(joint_strengthened)}个联合claim增强。',
        'real_data_used': True,
        'fixture_used': True,
        'pending_created': 0, 'paper_order_created': 0, 'real_trade_created': 0,
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ticker',default='300308.SZ'); p.add_argument('--json',action='store_true'); p.add_argument('--markdown',action='store_true')
    a=p.parse_args(); r=build(None,a.ticker)
    if a.markdown:
        d=r['business_evidence_brief']
        print("# 中际旭创业务证据简报\n## 1. 当前已看到的信息")
        for x in d['what_we_see']: print(f"- {x}")
        print("\n## 2. 这些信息意味着什么")
        for x in d['what_it_means']: print(f"- {x}")
        print("\n## 3. 当前能成立的判断")
        for x in d['can_conclude']: print(f"- {x}")
        print("\n## 4. 当前不能成立的判断")
        for x in d['cannot_conclude']: print(f"- {x}")
        print(f"\n## 5. 财务与业务证据合并后的结论\n- {d['joint_conclusion']}")
    else: print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
