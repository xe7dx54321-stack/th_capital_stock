#!/usr/bin/env python3
import argparse,json,sys
def build():
 brief_md="""# fallback HTML 解析与真实文本抽取简报

## 老板摘要

### 当前最清楚的结论

300308.SZ 维持CNINFO完整证据链路，baseline未回退。Phase 74 建立了通用HTML解析层、IRM HTML QA解析器、SSE HTML公告解析器、Hygon IR HTML解析器，对Phase 73确认可访问的HTML页面执行结构化解析和文本抽取。

### 本轮 HTML 解析后的出水情况

- IRM HTML：正则QA模式匹配已就绪，可提取问答文本
- SSE HTML：链接提取和PDF检测已就绪，可提取公告链接
- Hygon IR：三页面解析已就绪，含boilerplate移除和中文比例检测
- 通用工具：visible text、link extraction、PDF detection、date extraction、text hash

### 哪些标的信息源改善

688041不再只是SSE HTML可访问，而是有公告链接提取和Hygon IR三页面文本抽取。300394不再只是IRM HTML可访问，而是有正则QA模式匹配。

### 哪些地方仍然卡住

- HTML解析结果依赖稳定网络环境执行
- 300394公司IR URL仍无法自动发现

## 研究员详情

### 1. 300308.SZ：baseline 未回退

维持Phase 68完整证据链路。23条深度证据保留。fallback可选补充。

### 2. 688041.SH：SSE / Hygon IR HTML 解析结果

SSE公告页面：链接提取器已就绪，含PDF检测。Hygon三页面：官网、IR、announcements均已配置解析器。网络执行后可抽取公告链接、文本和PDF URL。

### 3. 300394.SZ：IRM HTML QA 解析结果

IRM GET HTML页面QA模式匹配已就绪。正则模式覆盖问/答、提问/回答、question/answer多种格式。网络执行后可提取QA文本。

### 4. 多源 HTML fallback 能力边界

- 已就绪：通用HTML解析工具、IRM QA解析器、SSE链接解析器、Hygon IR解析器
- 需网络执行：所有HTML页面的真实抓取和解析
- 需手动：300394公司IR URL
- 不能做的事：JavaScript渲染、验证码绕过、OCR

### 5. 当前不能推出的判断

- 688041的具体业务证据（HTML解析已就绪但待网络执行）
- 300394的任何披露证据（IRM HTML QA解析已就绪但待网络执行）
- 任何标的的价格趋势确认、客户构成确认、具体订单规模确认

---
不构成交易建议。
"""
 return{"phase74_internal_brief":{"sections":5,"tickers_covered":3,"markdown":brief_md}}
def main():
 p=argparse.ArgumentParser();p.add_argument("--json",action="store_true");p.add_argument("--markdown",action="store_true")
 a=p.parse_args();r=build()
 if a.markdown:print(r["phase74_internal_brief"]["markdown"])
 elif a.json:print(json.dumps({k:v for k,v in r["phase74_internal_brief"].items() if k!="markdown"},ensure_ascii=False,indent=2))
 else:print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
