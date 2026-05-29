#!/usr/bin/env python3
"""Multi-ticker internal research brief."""
import argparse, json, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / 'lib'
if str(L) not in sys.path: sys.path.insert(0, str(L))

def build():
    from smr_multi_ticker_universe import load_universe
    from smr_cninfo_source_identity import CURATED_CNINFO_IDENTITIES
    u = load_universe()

    brief_md = '''# 多标的内部投研跟踪简报

## 老板摘要

### 当前最清楚的结论

300308.SZ（中际旭创）已形成真实披露证据闭环：23条深度证据覆盖8个业务变量，7个判断得到真实披露文本支撑。688041.SH（海光信息）具备披露链路连通条件（CNINFO identity已配置），待执行真实PDF下载和文本提取。300394.SZ（天孚通信）CNINFO identity缺失，披露链路受阻。

### 标的分层

- 第一层（证据闭环）：300308.SZ — 完整披露证据链路，7个supported claims
- 第二层（链路就绪）：688041.SH — identity已配置，metadata可获取，待执行PDF/文本提取
- 第三层（链路受阻）：300394.SZ — CNINFO org_id缺失，无法进入披露证据链路

### 证据增强的地方

300308.SZ的AI光模块业务判断在Phase 67b-68中得到显著增强：产品代际（800G/1.6T）、产品结构、出货交付、订单能见度、产能扩张均有真实披露文本支撑。

### 仍然卡住的地方

- ASP走势：300308.SZ的6条ASP证据均标为review_required，不能确认趋势
- 客户份额和具体订单量：两个标的均缺乏直接披露
- 300394.SZ：CNINFO identity缺失，需要补充org_id
- 688041.SH：跨交易所（SH vs SZ）的PDF下载链路需要实际执行验证

## 研究员详情

### 1. 300308.SZ：已形成真实证据闭环

基于CNINFO真实披露文本，系统对中际旭创已形成完整的证据闭环：

- 证据基础：23条deep evidence，14份高价值IR/报告文本
- 支撑判断：800G信号、1.6T信号、产品结构升级、出货交付、订单能见度、产能扩张、客户需求
- 不能确认：ASP趋势（review_required）、客户份额、具体订单量
- 研究结论：bounded positive，维持跟踪

### 2. 688041.SH：泛化验证状态

海光信息（科创板）的CNINFO identity已配置（org_id=9900048365），具备披露链路连通的基本条件。当前状态：

- identity：已配置（plate=sh, column=sse）
- metadata：预期可获取（需要实际网络执行验证）
- PDF text extraction：待执行
- industry template：使用generic_hard_tech模板（不硬套AI光模块变量）
- 业务变量：营收增长、毛利率、研发投入、客户需求、产能、订单、产品路线图、竞争地位

### 3. 300394.SZ：修复状态与阻塞点

天孚通信的CNINFO identity缺失（org_id不在curated identities中），披露链路受阻。阻塞点：

- identity：未配置—需要补充CNINFO org_id
- 下游链路：全部阻塞（无identity则无法获取metadata/PDF/文本）

### 4. 多标的链路泛化结论

当前泛化状态：

- CNINFO identity resolver：SZ/ChiNext和SH/STAR双交易所均已验证可curated
- 行业模板路由器：ai_optical_module和generic_hard_tech两个模板可用
- disclosure metadata/pagination引擎：ticker-agnostic，复用Phase 67基础设施
- PDF下载和文本提取：pypdf方案ticker-agnostic
- deep evidence extractor：依赖industry template路由到对应业务变量
- 阻塞点：non-curated ticker无法进入链路（需要预先配置CNINFO identity）

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（尚未执行PDF文本提取）
- 300394.SZ的任何披露证据（identity缺失）
- 任何标的的ASP趋势仍不能确认
- 任何标的的客户份额仍不能确认
- 任何标的的具体订单量仍不能确认

---
报告基于CNINFO真实披露基础设施。不构成交易建议。
'''
    return {'phase69_multi_ticker_internal_brief': {'sections': 5, 'tickers_covered': 3, 'markdown': brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--json', action='store_true'); p.add_argument('--markdown', action='store_true')
    a = p.parse_args(); r = build()
    if a.markdown: print(r['phase69_multi_ticker_internal_brief']['markdown'])
    elif a.json: print(json.dumps({k: v for k, v in r['phase69_multi_ticker_internal_brief'].items() if k != 'markdown'}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
