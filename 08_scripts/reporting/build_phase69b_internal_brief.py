#!/usr/bin/env python3
"""Phase 69b internal brief."""
import argparse, json, sys
def build():
    brief_md = '''# 多标的真实泛化简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持完整证据链路，baseline 未回退。688041.SH identity 已验证（org_id=9900048365），metadata 链路已配置，PDF下载和文本提取待网络环境完成。300394.SZ identity 查找已尝试，org_id 未在已知身份库中发现，需手动补充。

### 本轮验证后的标的分层

- 第一层：300308.SZ — 完整证据链路可用（23条evidence，7 supported claims）
- 第二层：688041.SH — 部分链路可用（identity pass, metadata待完成, PDF/文本待完成）
- 第三层：300394.SZ — 阻断（org_id未发现）

### 已经真实完成的部分

300308.SZ 全链路回归通过。688041.SH 的 curated identity 可用（plate=sh, column=sse）。300394.SZ 的 identity 查找框架就绪，备选 org_ids 可尝试。

### 仍然卡住的部分

- 688041.SH：PDF下载+文本提取需要网络环境完成
- 300394.SZ：CNINFO org_id 未在已知身份库中，需要手动查找

## 研究员详情

### 1. 300308.SZ：baseline 未回退

维持 Phase 68 的完整证据链路状态。23条深度证据，7个支撑判断，3个不能确认。

### 2. 688041.SH：真实链路状态

identity已配置（org_id=9900048365，科创板/上交所）。使用generic_hard_tech行业模板。metadata链路已通过curated identity验证，PDF和文本提取链路待网络环境完成。

### 3. 300394.SZ：identity 查找与链路状态

identity 查找已尝试。备选 org_ids从CNINFO尝试，但在当前环境中未验证成功。需手动补充org_id到已知身份库。

### 4. 泛化能力判断

- 已泛化：metadata framework、pagination、high-value selection、evidence memory schema、capability matrix
- 仍ticker-specific：CNINFO org_id、stock_param
- 仍industry-specific：business variable template、claim mapping
- 未泛化：自动org_id发现、全行业evidence extraction

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（PDF文本未提取）
- 300394.SZ的任何披露证据（identity缺失）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
'''
    return {'phase69b_internal_brief': {'sections': 5, 'tickers_covered': 3, 'markdown': brief_md}}
def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.markdown: print(r['phase69b_internal_brief']['markdown'])
    elif a.json: print(json.dumps({k:v for k,v in r['phase69b_internal_brief'].items() if k!='markdown'}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
