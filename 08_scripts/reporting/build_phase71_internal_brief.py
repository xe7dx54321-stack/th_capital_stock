#!/usr/bin/env python3
"""Phase 71 internal brief."""
import argparse, json, sys

def build():
    brief_md = """# 多源披露链路扩展简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持CNINFO完整证据链路，baseline未回退。多源fallback框架已建立，覆盖IRM互动易、SZSE/SSE交易所披露页、公司官网IR、已知URL catalog共5个替代源。688041.SH和300394.SZ的fallback路由已配置。

### 多源 fallback 的真实进展

- IRM互动易：300394.SZ市场支持，待执行网络查询
- 交易所披露：SZSE和SSE端点已配置，688041.SH可尝试SSE页面
- 公司官网IR：300394和688041均需手动填写IR页面URL
- 已知URL catalog：均需手动填写

### 哪些标的信息源改善

688041.SH不再只依赖CNINFO——SSE披露页面可作为替代元数据源。300394.SZ不再完全受阻——IRM互动易可提供问答文本，SZSE页面可提供公告元数据。

### 哪些地方仍然卡住

- 公司官网IR页面URL需要手动查找填写
- 已知URL catalog需要手动补充
- IRM和交易所页面的真实网络执行依赖稳定网络环境

## 研究员详情

### 1. 300308.SZ：CNINFO baseline 未回退

维持Phase 68的完整证据链路。23条深度证据，7个支撑判断，3个不能确认。fallback为可选补充，不改变主链路。

### 2. 688041.SH：CNINFO PDF 卡点与替代源

CNINFO metadata可用（60条），PDF下载受阻。多源fallback已配置：SSE披露页可提供替代元数据和PDF链接，公司官网IR页需手动填URL。

### 3. 300394.SZ：CNINFO identity blocker 与替代源

CNINFO org_id仍未找到（9个备选均失败）。多源fallback已配置：IRM互动易可获取问答文本（管理层表述），SZSE页面可获取公告元数据，公司官网IR和已知URL需手动补充。

### 4. 多源能力边界

- 已建立：source registry、fallback route engine、known URL catalog
- 可自动：IRM connector、exchange disclosure connector
- 需手动：company IR page URL、known catalog URL
- 不能做的事：全市场自动org_id发现、绕过验证码、OCR

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（所有源均未提取到可用文本）
- 300394.SZ的任何披露证据（所有源均未提取到可用文本）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
"""
    return {"phase71_internal_brief": {"sections": 5, "tickers_covered": 3, "markdown": brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown: print(r["phase71_internal_brief"]["markdown"])
    elif a.json: print(json.dumps({k:v for k,v in r["phase71_internal_brief"].items() if k!="markdown"}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__": main()
