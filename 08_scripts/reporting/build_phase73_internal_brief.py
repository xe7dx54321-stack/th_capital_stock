#!/usr/bin/env python3
import argparse,json,sys
def build():
 brief_md="""# fallback 源修复与真实取数简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持CNINFO完整证据链路，baseline未回退。Phase 73 对 Phase 72 诊断出的 IRM HTTP 405 / SSE HTTP 404 / SZSE HTTP 500 做了端点和参数维度修复诊断。688041已被填入 Hygon 官网和 IR 页面备选URL，300394因公开IR URL不可得仍留手动。

### 本轮修复后的出水情况

- IRM互动易：8个端点变量已就绪，待网络执行验证
- SSE公告页：8个端点变量已就绪，含 HTML 页面和 API 变量
- SZSE公告页：8个端点变量诊断已就绪
- 公司IR页：688041 已填入 Hygon 官网备选URL
- 已知URL：688041 已填入 Hygon IR 页面备选URL

### 哪些标的信息源改善

688041不再只是 SSE HTTP 404，而是有8种端点格式尝试。300394不再只是 IRM HTTP 405，而是有8种方法/参数组合诊断。

### 哪些地方仍然卡住

- 端点修复结果依赖稳定网络环境执行
- 300394公司IR页面URL仍无法自动发现
- 300394互动易平台URL需人工查找

## 研究员详情

### 1. 300308.SZ：baseline 未回退

维持Phase 68完整证据链路。23条深度证据保留。fallback可选补充。

### 2. 688041.SH：SSE / company / known URL 修复结果

SSE端点：8个URL变量已就绪，覆盖 query.do / shtml / 公告列表 / STAR board 等多种格式。Hygon 官网 https://www.hygon.cn 和 IR 页面 https://www.hygon.cn/ir 已填入。网络执行后可验证HTTP状态。

### 3. 300394.SZ：IRM / SZSE / company / known URL 修复结果

IRM端点：8个变量，覆盖 POST/GET、form/JSON、stock/companyCode/securityCode 参数、有无 Referer。SZSE端点：8个变量诊断。公司IR URL仍无法自动发现。

### 4. 多源 fallback 能力边界

- 已就绪：IRM/SZSE/SSE 端点诊断和修复框架
- 需网络执行：所有端点的真实HTTP验证
- 需手动：300394公司IR URL、300394互动易平台URL
- 不能做的事：自动全市场URL发现、绕过验证码、OCR

### 5. 当前不能推出的判断

- 688041.SH的具体业务证据（端点修复已就绪但待网络执行）
- 300394.SZ的任何披露证据（端点修复已就绪但待网络执行）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
"""
 return {"phase73_internal_brief":{"sections":5,"tickers_covered":3,"markdown":brief_md}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:print(r["phase73_internal_brief"]["markdown"])
 elif a.json:print(json.dumps({k:v for k,v in r["phase73_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
