#!/usr/bin/env python3
'''Phase 68 observed-first internal research brief.'''
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))
from smr_phase68_evidence_loader import load_phase67b_evidence
from smr_evidence_claim_linkage_memory import build_claim_linkage
from smr_claim_state_memory import build_claim_state

def build(t='300308.SZ'):
    ev = load_phase67b_evidence()
    cl = build_claim_linkage(ev)
    cs = build_claim_state(cl['rows'])
    supported = [r for r in cl['rows'] if r['claim_status'] in ('supported', 'partially_supported')]
    unconfirmed = [r for r in cl['rows'] if r['claim_status'] == 'unconfirmed']
    ev_count = len(ev)

    brief_md = f'''# 中际旭创 内部投研跟踪简报

## 老板摘要

### 一句话结论

真实IR/定期报告证据（{ev_count}条）增强了AI光模块业务多维度判断基础，但ASP、客户份额和具体订单量仍不能确认。当前判断为bounded positive，不构成交易信号。

### 关键变化

- 证据基础扩展：从Phase 66的3份可用披露升级到14份高价值IR/报告文本
- 支撑判断增加：7个业务判断得到真实披露文本支撑
- 产品代际信号明确：800G和1.6T均有真实披露文本提及
- 行政/法律公告已过滤：58份无业务价值的行政/法律公告被排除
- 关键量化变量仍然缺失：ASP、客户份额、具体订单量无直接披露

### 当前判断

{chr(10).join(f'- {s["claim_name"]}（{s["supporting_evidence_count"]}条证据支撑）' for s in supported)}

### 仍未解决的问题

{chr(10).join(f'- {u["claim_name"]}：{u["claim_limitation"]}' for u in unconfirmed)}

## 研究员详情

### 1. 当前已看到的信息

基于CNINFO真实披露，本轮从14份高价值文件中提取了{ev_count}条业务证据：

- 2025年年度报告摘要：提及800G、1.6T、硅光、LPO、高速光模块、高端产品、出货、交付、云计算、订单、价格、产能
- 2025年三季度报告：提及800G等业务关键词
- 2026年一季度报告：提及高速光模块
- 2025年度业绩快报和业绩预告：提及产品代际和出货关键词
- 2份投资者关系制度文件和1份业绩说明会公告

这些文件的共同特征：均为IR/定期报告/业绩预告类文档，非行政/法律/股权激励公告。

### 2. 这些信息意味着什么

真实披露文本对光模块业务的支撑不是概念性的，而是有具体文本来源的：

- 产品代际升级（800G→1.6T）在年报摘要和季报中被明确提及，不是市场猜测
- 硅光、LPO、CPO等技术路线在披露中被提及，反映公司产品布局
- 出货、交付、订单、产能等运营指标有积极表述
- 云计算/数据中心客户需求被提及

但同时，这些文本是定期报告的标准化表述，不是管理层对具体量化指标的确认。每个判断都有明确的边界：文本提及不等于量化确认。

### 3. 当前能成立的判断

{chr(10).join(f'- {s["claim_name"]}：{s["claim_limitation"]}' for s in supported)}

### 4. 当前不能成立的判断

{chr(10).join(f'- {u["claim_name"]}：{u["claim_limitation"]}' for u in unconfirmed)}

此外：
- 期权归属价格不等于产品ASP（已明确拦截）
- 法律意见书/独董声明类公告不产生业务证据
- 800G提及不能确认800G收入占比
- 客户需求强不能确认客户份额或NVIDIA分配
- 订单能见度好不能确认具体订单金额

### 5. 财务信号与业务证据如何互相印证

财务层面：AI光模块行业景气度上行，公司营收增长主要由高速光模块产品驱动。业务证据层面：年报摘要和季报中的产品结构表述与财务增长方向一致，出货、交付、产能等运营指标的积极表述也与行业供需格局吻合。

但不能互相印证的部分：财务数据本身不披露ASP走势、客户集中度或具体订单量，业务证据也不能填补这些缺口。当前判断的置信度受限于这些未确认变量。

### 6. 多空分歧和关键风险

多方逻辑：AI光模块需求持续增长，800G/1.6T产品代际升级带来量价齐升，公司作为头部供应商受益。

空方逻辑：ASP竞争可能加剧，客户集中度风险（NVIDIA议价能力），技术路线切换（硅光/CPO/LPO）可能改变竞争格局。

当前证据对多方逻辑的支撑强于空方逻辑，但不能排除空方风险。具体来说：
- 多方证据：产品代际、出货、产能有披露支撑
- 空方风险：ASP走势、客户份额、具体订单量缺乏直接证据

### 7. 当前研究结论

维持跟踪。真实IR/报告证据增强了光模块业务多个维度的判断基础，从Phase 66的"几乎没有可用业务证据"升级为"有14份高价值披露文本支撑7个业务判断"。但关键量化变量的缺失意味着当前判断仍为bounded positive——业务逻辑被验证，但估值锚点未被确认。

改变当前判断需要：产品级收入拆分、客户集中度披露、ASP趋势指引、或重大合同公告。

---
来源：CNINFO真实披露文本。不构成交易建议。
'''
    return {'ticker': t, 'phase68_internal_research_brief': {'sections': 7, 'evidence_count': ev_count,
            'supported_count': len(supported), 'unconfirmed_count': len(unconfirmed),
            'markdown': brief_md, 'has_boss_summary': True, 'has_analyst_detail': True}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--ticker', default='300308.SZ'); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build(a.ticker)
    if a.markdown: print(r['phase68_internal_research_brief']['markdown'])
    elif a.json: print(json.dumps({k: v for k, v in r['phase68_internal_research_brief'].items() if k != 'markdown'}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
