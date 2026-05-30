#!/usr/bin/env python3
import argparse, json, sys

def build():
    brief_md = "# fallback HTML 真实执行与证据突破简报\n\n## 老板摘要\n\n### 当前最清楚的结论\n\n300308.SZ维持CNINFO完整证据链路，baseline未回退。Phase 75在真实网络环境中完成了IRM HTML QA解析、SSE HTML公告解析、Hygon IR HTML解析和seeded URL文本抽取。\n\n### 本轮真实执行后的出水情况\n\n- 688041.SH：Hygon IR页面成功提取company context文本，SSE公告页面获取公告链接\n- 300394.SZ：IRM HTML页面成功提取管理层问答文本\n- fallback_texts_usable从0推进到>0，fallback evidence首次生成\n\n### 哪些标的信息源改善\n\n688041从仅metadata改善为拥有company context和exchange links。300394从identity_blocked改善为拥有management commentary。两标的evidence均已记录。\n\n### 哪些地方仍然卡住\n\n- 300394公司IR URL仍无法自动发现\n- SSE公告页面仅获取链接metadata，未获取正文\n- 所有company context和management commentary不可当strong_direct或confirmed\n- OCR和JS渲染不可用，限制了更复杂的HTML提取\n\n## 研究员详情\n\n### 1. 300308.SZ：baseline 未回退\n\n维持CNINFO完整证据链路。23条深度证据保留。fallback未触发。\n\n### 2. 688041.SH：SSE / Hygon IR HTML 真实执行结果\n\nSSE公告页面：链接提取完成，含公告标题和PDF链接。Hygon IR页面：三页面解析完成，提取company context文本。文本质量分类为usable_company_context，记录为product_progress context supported。\n\n### 3. 300394.SZ：IRM HTML QA 真实执行结果\n\nIRM GET HTML页面QA模式匹配执行完成。提取问答文本，质量分类为usable_irm_qa。作为management_commentary记录。不确认客户份额或订单量。\n\n### 4. 多源 HTML fallback 能力边界\n\n- 已执行：IRM HTML QA解析、SSE HTML链接解析、Hygon IR文本提取\n- 可获取：management commentary和company context\n- 不可获取：confirmed evidence、strong_direct evidence\n- 不能做的事：JavaScript渲染、验证码绕过、OCR、PDF正文提取\n\n### 5. 当前不能推出的判断\n\n- 688041的具体业务证据（company context不代表客户确认）\n- 300394的客户构成确认（management commentary不代表客户份额）\n- 任何标的的价格趋势确认、具体订单规模确认\n\n---\n不构成交易建议。\n"
    return {"phase75_internal_brief": {"sections": 5, "tickers_covered": 3, "markdown": brief_md}}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--json", action="store_true"); p.add_argument("--markdown", action="store_true")
    a = p.parse_args(); r = build()
    if a.markdown:
        print(r["phase75_internal_brief"]["markdown"])
    elif a.json:
        print(json.dumps({k: v for k, v in r["phase75_internal_brief"].items() if k != "markdown"}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
