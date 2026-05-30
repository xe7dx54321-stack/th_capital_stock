#!/usr/bin/env python3
"""Phase 70 internal brief."""
import argparse, json, sys

def build():
    brief_md = """# 多标的披露链路修复简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持完整证据链路，baseline 未回退。688041.SH PDF下载和文本提取链路已进行诊断和硬化，metadata链路已验证可用。300394.SZ CNINFO身份查找已扩展尝试更多备选号码，但尚未找到可验证的org_id。

### 本轮修复后的标的分层

- 第一层：300308.SZ — 完整证据链路可用（23条evidence，7 supported claims）
- 第二层：688041.SH — 部分链路可用（identity pass, metadata可用, PDF/文本硬化中）
- 第三层：300394.SZ — 阻断（扩展org_id查找后仍未找到可验证的org_id）

### 已经修复的部分

688041.SH PDF URL诊断已建立，metadata fetch已验证通过（60条来源），PDF download hardening已就绪。

### 仍然卡住的部分

- 688041.SH：PDF下载的实际执行需要稳定网络环境
- 300394.SZ：扩展的9个备选org_id均未通过CNINFO metadata验证

## 研究员详情

### 1. 300308.SZ：baseline 未回退

维持 Phase 68 的完整证据链路状态。23条深度证据，7个支撑判断，3个不能确认。

### 2. 688041.SH：PDF/text 修复进展

identity已配置（org_id=9900048365，科创板/上交所）。metadata fetch已验证通过，60条元数据记录，其中约55条含PDF链接。PDF URL诊断确认URL格式正常，均为static.cninfo.com.cn。PDF下载硬化代码已就绪，待网络环境执行。

### 3. 300394.SZ：identity 修复进展

扩展了org_id查找范围，从3个备选增加到9个备选。所有备选org_id均通过CNINFO metadata query尝试验证，但均未返回有效数据。需要手动从CNINFO公司页面提取org_id。

### 4. 泛化能力边界

- 已确认通用：metadata framework、pagination、PDF URL extraction、evidence memory schema、capability matrix
- 依赖ticker-specific：CNINFO org_id（每个标的唯一）
- 依赖网络环境：PDF download、text extraction
- 未解决：自动org_id发现、全行业evidence extraction

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（PDF文本尚未提取）
- 300394.SZ的任何披露证据（identity缺失）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
"""
    return {"phase70_internal_brief":{"sections":5,"tickers_covered":3,"markdown":brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown: print(r["phase70_internal_brief"]["markdown"])
    elif a.json: print(json.dumps({k:v for k,v in r["phase70_internal_brief"].items() if k!="markdown"}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
