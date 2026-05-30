#!/usr/bin/env python3
"""Phase 72 internal brief."""
import argparse, json, sys
def build():
    brief_md = """# 多源 fallback 真实取数简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持CNINFO完整证据链路，baseline未回退。Phase 72建立了fallback真实取数框架：URL catalog填充helper、公司IR候选补丁、已知URL catalog补丁、IRM/交易所/公司IR/已知URL四个connector的真实执行硬化。

688041.SH已注册SSE公告页面作为fallback备选URL。300394.SZ的fallback路由已配置IRM和SZSE页面，但公司IR页仍需手动填写URL。

### 备用源真实出水情况

- IRM互动易：connector已就绪，待网络执行
- SSE公告页：688041已注册备选URL
- SZSE公告页：connector已就绪
- 公司IR页：688041 SSE备选可用，300394仍需手动
- 已知URL catalog：688041 SSE备选可用，300394仍需手动

### 哪些标的信息源改善

688041不再只依赖CNINFO PDF——SSE公告页面可直接提供metadata和公告文本。300394不再只依赖CNINFO org_id——IRM互动易可提供问答文本。

### 哪些地方仍然卡住

- 真实文本获取依赖稳定网络环境执行
- 300394公司IR页面URL需手动查找
- 300394已知URL catalog需手动填充

## 研究员详情

### 1. 300308.SZ：baseline 未回退

维持Phase 68完整证据链路。23条深度证据，7个支撑判断，3个不能确认。fallback可选补充。

### 2. 688041.SH：fallback 取数进展

SSE公告页面已注册为fallback备选URL。CNINFO metadata可用（60条），PDF下载受阻。SSE页面可提供替代metadata和公告文本。

### 3. 300394.SZ：fallback 取数进展

IRM互动易connector已就绪（SZ market supported）。SZSE页面connector已就绪。公司IR页面URL待手动查找。一旦拿到可用的IRM问答文本或SZSE页面文本，即可进入evidence extraction。

### 4. 多源 fallback 能力边界

- 已就绪：IRM connector、SZSE/SSE connector、company IR page discovery、known URL catalog
- 需网络执行：IRM真实QA文本获取、交易所页面文本获取
- 需手动：300394公司IR URL、300394已知URL catalog
- 不能做的事：自动全市场URL发现、绕过验证码、OCR

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（所有源均未提取到可用备选文本）
- 300394.SZ的任何披露证据（所有源均未提取到可用备选文本）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
"""
    return {"phase72_internal_brief": {"sections": 5, "tickers_covered": 3, "markdown": brief_md}}
def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown: print(r["phase72_internal_brief"]["markdown"])
    elif a.json: print(json.dumps({k:v for k,v in r["phase72_internal_brief"].items() if k!="markdown"}, ensure_ascii=False, indent=2))
    else: print(json.dumps(r, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
