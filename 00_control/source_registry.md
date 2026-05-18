# SMR 输入源注册表

> 这份注册表定义的是“系统应该吃哪些输入”，不是说这些输入今天都已经完全接上了。
> `Status` 表示建设状态：`live`（已接入）、`experimental`（实验中）、`planned`（计划中）。
> `Enabled` 表示是否纳入当前正式建设面。

## Sources

| Source Key | Name | Layer | Provider | Source Class | Entity Scope | Markets | Cadence | Freshness SLA Hours | Status | Enabled | Cost | Confidence | Owner Profile | Notes |
|------------|------|-------|----------|--------------|--------------|---------|---------|---------------------|--------|---------|------|------------|---------------|-------|
| ah_daily_bar | A/H 日线行情 | market_price | akshare_eastmoney | market_data | stock | SZ,SH,BJ,HK | daily_close | 18 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/data_harvester/ah_daily_bar.py` 主入口。 |
| us_daily_bar | 美股对标日线行情 | market_price | akshare_sina | market_data | stock | US | daily_close | 18 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/data_harvester/ah_daily_bar.py --us-only`。 |
| us_signal_earnings | 美股强波动信号 | signal | derived_from_us_daily_bar | derived_signal | stock,sector | US | daily_close | 20 | live | yes | low | medium | openclaw_factor_exec | 现有 `08_scripts/us_signal_harvester/earnings_monitor.py`。 |
| trend_factor | 趋势因子快照 | factor | smr_internal | derived_factor | stock | SZ,SH,BJ,HK | daily_close | 20 | live | yes | low | medium | openclaw_factor_exec | 现有 `08_scripts/factor_engine/trend.py`。 |
| fundamental_factor | 轻量基本面因子 | factor | smr_internal | derived_factor | stock | SZ,SH,BJ,HK | daily_close | 24 | live | yes | low | medium | openclaw_factor_exec | 现有 `08_scripts/factor_engine/fundamental.py`。 |
| us_linkage_factor | 美股映射联动因子 | factor | smr_internal | derived_factor | stock,sector | US,SZ,SH,BJ,HK | daily_close | 20 | live | yes | low | medium | openclaw_factor_exec | 现有 `08_scripts/factor_engine/us_linkage.py`。 |
| cninfo_announcement | A 股法定公告 | company_event | cninfo | official_filing | stock | SZ,SH,BJ | intraday_batch | 6 | live | yes | low | high | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_cninfo_announcements.py`；其中已覆盖“投资者关系活动记录表 / 业绩说明会公告”等高价值一手披露，只是后续需要在事件层单独抬出来。 |
| hkex_announcement | 港股法定公告 | company_event | hkexnews | official_filing | stock | HK | intraday_batch | 6 | live | yes | low | high | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_hkex_announcements.py`。 |
| sec_submissions_json | SEC 公司申报清单 | company_event | sec | official_filing | stock | US,HK | daily_close | 24 | live | yes | low | high | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_sec_official_materials.py`；先接公司 submissions JSON（公司申报清单 JSON）和目标映射，用于官方材料发现。 |
| sec_filing_document | SEC 主文件正文 | company_event | sec | official_filing | stock | US,HK | daily_close | 24 | live | yes | low | high | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_sec_official_materials.py`；覆盖 8-K / 6-K / 10-K / 10-Q / 20-F 主文件。 |
| sec_earnings_material | SEC 业绩附件材料 | company_event | sec | official_filing | stock | US,HK | daily_close | 24 | live | yes | low | high | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_sec_official_materials.py`；优先抓 EX-99、业绩稿、presentation（演示稿）、transcript（电话会稿）等。 |
| official_ir_page_discovery | 官方 IR 入口发现页 | company_event | official_ir | official_company_ir | stock | US,HK | daily_close | 24 | live | yes | low | medium | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_ir_primary_materials.py`；保留官方 IR 落地页快照，作为一手材料发现入口。 |
| official_ir_material | 官方 IR 一手材料 | company_event | official_ir | official_company_ir | stock | US,HK | daily_close | 24 | live | yes | low | high | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_ir_primary_materials.py`；覆盖业绩稿、演示稿、电话会稿、webcast 页面等。 |
| eastmoney_report_search | 东方财富研报搜索页 | text_research | eastmoney | sellside_research | stock | SZ,SH,BJ | intraday_batch | 12 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_eastmoney_stock_reports.py`。 |
| eastmoney_report_article | 东方财富研报正文 | text_research | eastmoney | sellside_research | stock | SZ,SH,BJ | intraday_batch | 12 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_eastmoney_report_articles.py`。 |
| eastmoney_report_pdf_text | 东方财富研报 PDF 文本 | text_research | eastmoney_pdf | sellside_research | stock | SZ,SH,BJ | intraday_batch | 18 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/wiki/extract_eastmoney_report_pdf_text.py`。 |
| eastmoney_report_structured | 东方财富研报结构化 | text_research | eastmoney | structured_research | stock | SZ,SH,BJ | intraday_batch | 18 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/wiki/extract_eastmoney_report_structured.py`。 |
| eastmoney_report_table_structured | 东方财富研报表格结构化 | text_research | eastmoney | structured_research | stock | SZ,SH,BJ | intraday_batch | 18 | live | yes | low | medium | openclaw_data_exec | 现有 `08_scripts/wiki/extract_eastmoney_report_table_structured.py`。 |
| eastmoney_news_search | 东方财富新闻搜索页 | text_news | eastmoney | public_news | stock | SZ,SH,BJ | intraday_batch | 8 | live | yes | low | low | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_eastmoney_news_search.py`。 |
| eastmoney_news_article | 东方财富新闻正文 | text_news | eastmoney | public_news | stock | SZ,SH,BJ | intraday_batch | 8 | live | yes | low | low | openclaw_data_exec | 现有 `08_scripts/wiki/fetch_eastmoney_news_articles.py`。 |
| source_manifest | 外部源统一清单 | control | smr_internal | manifest | system | ALL | on_change | 2 | live | yes | low | high | openclaw_data_exec | 现有 `08_scripts/wiki/build_source_manifest.py`。 |
| stock_connect_flow | 北向 / 南向资金流 | capital_flow | hkex_connect | official_market_flow | stock,market,sector | SZ,SH,HK | daily_close | 12 | live | yes | low | high | openclaw_data_exec | 已接入 `08_scripts/events/snapshot_stock_connect_flow.py`；四路成交概况走官方日频，港股通持有数量走官方日频，沪/深股通持有数量当前按官方季频补齐。 |
| margin_balance | 融资融券余额 | capital_flow | exchange_margin | official_market_flow | stock,market | SZ,SH | daily_close | 12 | live | yes | low | high | openclaw_data_exec | 已接入 `08_scripts/events/snapshot_margin_balance.py`，走上交所 / 深交所官方口径，支持自动回退到最近可用交易日。 |
| block_trade_feed | 大宗交易 | capital_flow | exchange_block_trade | official_market_flow | stock | SZ,SH,BJ,HK | daily_close | 12 | planned | yes | low | medium | openclaw_data_exec | 用于识别大额交易和潜在资金切换。 |
| corp_action_calendar | 公司事件日历 | calendar | official_filings_derived | derived_calendar | stock | SZ,SH,BJ,HK,US | daily_close | 12 | planned | yes | low | high | openclaw_data_exec | 目标覆盖财报日、股东会、解禁、分红、回购、减持。 |
| earnings_calendar | 业绩披露日历 | calendar | official_filings_derived | derived_calendar | stock | SZ,SH,BJ,HK,US | daily_close | 12 | planned | yes | low | high | openclaw_data_exec | 目标先从公告和法定文件中归一化。 |
| macro_nbs | 国家统计局宏观序列 | macro | nbs | official_macro | macro,sector | CN | scheduled_release | 24 | planned | yes | low | high | openclaw_data_exec | 覆盖工业增加值、PMI、消费、投资、就业等。 |
| macro_pbc | 人民银行流动性序列 | macro | pbc | official_macro | macro | CN | scheduled_release | 24 | planned | yes | low | high | openclaw_data_exec | 覆盖社融、M2、利率等。 |
| macro_customs | 海关进出口序列 | macro | china_customs | official_macro | macro,sector | CN | scheduled_release | 24 | planned | yes | low | high | openclaw_data_exec | 覆盖出口、进口、分品类景气。 |
| management_language | 管理层语言变化 | interpretation | hermes_derived | llm_derived_text_signal | stock | SZ,SH,BJ,HK,US | on_new_filing | 24 | planned | yes | medium | medium | hermes_research_curator | 基于公告、财报、业绩会与 IR 文本。 |
| consensus_revision | 一致预期修正 | expectation | commercial_or_sellside | expectation_signal | stock | SZ,SH,BJ,HK,US | daily_close | 24 | planned | no | high | medium | hermes_research_curator | 后续若要做预期差，基本绕不过商业源。 |
| premium_research_morgan_stanley | Morgan Stanley Research（摩根士丹利研究） | text_research | morgan_stanley | licensed_sellside_research | stock,sector | US,HK,CN | daily_close | 24 | planned | no | high | high | hermes_research_curator | 官方研究平台是机构授权源，不建议公开野抓；后续按企业账号 / client portal（客户门户）方式接。 |
| premium_research_jpm | J.P. Morgan Research（摩根大通研究） | text_research | jpmorgan | licensed_sellside_research | stock,sector | US,HK,CN | daily_close | 24 | planned | no | high | high | hermes_research_curator | 官方研究平台是授权源，后续只做合规接入位。 |
| premium_research_citi | Citi Research（花旗研究） | text_research | citi | licensed_sellside_research | stock,sector | US,HK,CN | daily_close | 24 | planned | no | high | high | hermes_research_curator | 官方研究平台是授权源，后续按公司现有终端 / 账号方案接。 |
| premium_research_goldman | Goldman Sachs Research（高盛研究） | text_research | goldman_sachs | licensed_sellside_research | stock,sector | US,HK,CN | daily_close | 24 | planned | no | high | high | hermes_research_curator | 官方研究平台是授权源，后续只接正规授权链路。 |
| public_analyst_signal_marketscreener | MarketScreener 公开卖方信号摘要 | text_research | marketscreener | public_analyst_summary | stock,sector | US,HK,CN | daily_close | 24 | live | yes | low | medium | openclaw_data_exec | 已接入正式链路，当前抓共识评级、覆盖分析师数、目标价区间和相对现价空间，适合做卖方信号，不适合当全文研报替代。 |
| public_analyst_signal_marketbeat | MarketBeat 公开评级与目标价摘要 | text_research | marketbeat | public_analyst_summary | stock,sector | US | daily_close | 24 | planned | yes | low | medium | openclaw_data_exec | 当前实测被 Cloudflare（反爬拦截）限制，先保留注册位，不纳入正式生产。 |
| public_transcript_fool | The Motley Fool 公开电话会文字稿 | text_research | fool | public_transcript | stock | US,HK | daily_close | 24 | live | yes | low | medium | openclaw_data_exec | 新增 `08_scripts/wiki/fetch_public_transcripts_fool.py`；优先从个股 `quote`（行情页）发现 transcript 链接，缺失时再回退 `Earnings Call Transcripts`（业绩电话会文字稿）总列表，适合作为管理层原话复核入口。 |
| public_transcript_seekingalpha | Seeking Alpha 公开电话会文本 | text_research | seekingalpha | public_transcript | stock | US,HK | daily_close | 24 | planned | yes | medium | medium | hermes_research_curator | 当前实测存在验证码 / Access denied（拒绝访问）限制，先保留注册位，不纳入正式生产。 |
