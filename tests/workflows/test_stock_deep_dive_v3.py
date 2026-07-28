from __future__ import annotations

import sqlite3
import unittest

from smr_app.adapters.research_context_v3 import collect_stock_research_context, provider_status
from smr_app.research.analysis_v3 import (
    build_stock_analysis_v3,
    extract_a_share_annual_metrics,
    extract_operating_metrics,
)
from smr_app.research.report_v3 import compile_stock_research_report_v3, validate_stock_research_report_v3
from smr_app.research.research_plan_v3 import build_stock_research_plan
from smr_app.workflows.stock_deep_dive import stock_deep_dive_definition


ANNUAL_TEXT = """主要会计数据和财务指标
2025 年
2024 年
本年比上年增减
2023 年
38,239,935,640.67
23,862,159,738.37
60.25%
10,717,984,471.03
10,797,254,300.45
5,171,485,967.85
108.78%
2,173,527,747.77
10,710,053,246.51
5,068,356,338.29
111.31%
2,123,669,234.59
10,896,126,160.03
3,164,582,957.85
244.31%
1,897,126,918.71
9.80
9.71
4.72
4.63
107.63%
109.72%
2.00
1.97
43.84%
31.23%
12.61%
16.58%
45,288,970,887.78
28,866,276,555.26
56.89%
20,006,747,461.32
29,765,156,275.68
19,133,887,012.66
55.56%
14,261,022,312.40
公司最近三个会计年度不存在持续经营不确定性。
监管指引第 4 号——创业板行业信息披露中的通信相关业务披露要求 产品系列 产品外观 产品特性 应用场景
公司主营业务为高端光通信收发模块的研发、生产及销售，为云数据中心客户提供 400G、800G 和 1.6T 产品。
采购模式、以销定产、直接销售、客户认证、产能、产量、销量、毛利率、行业、市场份额、未来需求、研发与风险。
"""


def create_source() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE filing_documents(
            filing_id TEXT,ticker TEXT,market TEXT,company_name TEXT,filing_type TEXT,title TEXT,
            published_at TEXT,source_key TEXT,source_url TEXT,parse_status TEXT
        );
        CREATE TABLE document_chunks(
            chunk_id TEXT,document_id TEXT,document_type TEXT,source_key TEXT,ticker TEXT,market TEXT,
            section_name TEXT,chunk_index INTEGER,text TEXT,evidence_id TEXT,chunk_section_type TEXT,
            investment_relevance_score REAL,financial_table_score REAL,guidance_relevance_score REAL,
            risk_relevance_score REAL,business_update_score REAL,exclude_reason TEXT,usable_for_core_claim INTEGER
        );
        CREATE TABLE evidence_items(evidence_id TEXT);
        CREATE TABLE news_items(
            news_id TEXT,source_key TEXT,source_name TEXT,title TEXT,body TEXT,url TEXT,published_at TEXT,
            credibility REAL,tickers_json TEXT,themes_json TEXT
        );
        CREATE TABLE market_event(
            event_id TEXT,source_key TEXT,event_family TEXT,event_type TEXT,entity_id TEXT,title TEXT,
            event_date TEXT,publish_time TEXT,importance TEXT,status TEXT,source_path TEXT
        );
        CREATE TABLE stock_pool(pool_type TEXT,ts_code TEXT,sector TEXT,added_date TEXT,status TEXT);
        CREATE TABLE sector_config(
            sector_key TEXT,sector_name TEXT,vcr_priority TEXT,smr_focus TEXT,ah_universe TEXT,us_benchmarks TEXT
        );
        CREATE TABLE daily_bar(
            ts_code TEXT,trade_date TEXT,open REAL,close REAL,high REAL,low REAL,vol REAL,amount REAL,
            pct_chg REAL,turnover REAL,market TEXT
        );
        CREATE TABLE valuation_snapshot(ticker TEXT,generated_at TEXT,current_price REAL,valuation_status TEXT);
        CREATE TABLE fundamentals_snapshot(ticker TEXT,created_at TEXT,period TEXT,revenue REAL);
        """
    )
    conn.execute(
        "INSERT INTO filing_documents VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("doc1", "300308.SZ", "A", "中际旭创股份有限公司", "annual_report", "2025年年度报告",
         "2026-03-31", "cninfo", "https://example.test/annual.pdf", "parsed"),
    )
    conn.execute(
        "INSERT INTO document_chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("chunk1", "doc1", "annual_report", "cninfo", "300308.SZ", "A", "主要会计数据和财务指标", 0,
         ANNUAL_TEXT, "ev_annual", "financial_statement", .98, 1.0, .8, .7, .9, None, 1),
    )
    conn.execute(
        "INSERT INTO news_items VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("n1", "official_media", "官方媒体", "公司下一代产品推进", "只作背景", "https://example.test/n1",
         "2026-06-01", .8, '["300308.SZ"]', '["photonics"]'),
    )
    conn.execute(
        "INSERT INTO market_event VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("e1", "cninfo", "filing", "investor_relations", "300308.SZ", "投资者关系活动记录",
         "2026-05-15", "2026-05-15", "high", "active", "doc"),
    )
    conn.execute("INSERT INTO stock_pool VALUES ('seed','300308.SZ','photonics','2026-01-01','active')")
    conn.execute(
        "INSERT INTO sector_config VALUES ('photonics','光通信','P1','core','300308,300502,300394','LITE,MRVL')"
    )
    for ticker, price in (("300308.SZ", 1128.35), ("300502.SZ", 95.0), ("300394.SZ", 73.0)):
        conn.execute(
            "INSERT INTO daily_bar VALUES (?, '2026-07-08', ?, ?, ?, ?, 100, NULL, 1, NULL, 'A')",
            (ticker, price, price, price, price),
        )
        conn.execute(
            "INSERT INTO daily_bar VALUES (?, '2026-06-10', ?, ?, ?, ?, 100, NULL, 1, NULL, 'A')",
            (ticker, price * .9, price * .9, price * .9, price * .9),
        )
    conn.commit()
    return conn


class StockDeepDiveV3Tests(unittest.TestCase):
    def test_runtime_definition_exposes_the_real_v3_stage_chain(self) -> None:
        stage_ids = [stage.stage_id for stage in stock_deep_dive_definition().stages]
        self.assertEqual(27, len(stage_ids))
        self.assertEqual(
            stage_ids[:4],
            ["validate_input", "build_research_plan", "build_data_requirements", "check_provider_health"],
        )
        self.assertIn("retrieve_official_filings", stage_ids)
        self.assertLess(stage_ids.index("evaluate_cached_requirements"), stage_ids.index("acquire_missing_requirements"))
        self.assertLess(stage_ids.index("acquire_missing_requirements"), stage_ids.index("validate_acquired_data"))
        self.assertLess(stage_ids.index("validate_acquired_data"), stage_ids.index("materialize_acquired_data"))
        self.assertLess(stage_ids.index("materialize_acquired_data"), stage_ids.index("normalize_research_data"))
        self.assertIn("analyze_financials", stage_ids)
        self.assertEqual(stage_ids[-3:], ["draft_report", "validate_report", "persist_outputs"])

    def test_research_plan_has_complete_standard_structure(self) -> None:
        plan = build_stock_research_plan("300308.SZ", "A")
        self.assertEqual("3.0", plan["plan_version"])
        self.assertGreaterEqual(len(plan["sections"]), 15)
        self.assertGreaterEqual(len(plan["questions"]), 15)
        self.assertIn("financials", {item["section_id"] for item in plan["sections"]})

    def test_provider_status_degrades_missing_sources_without_throwing(self) -> None:
        source = sqlite3.connect(":memory:")
        control = sqlite3.connect(":memory:")
        status = provider_status(source, control)
        self.assertEqual("unavailable", status["official_filings"]["status"])
        self.assertEqual("unavailable", status["memory"]["status"])

    def test_annual_report_metrics_are_extracted_deterministically(self) -> None:
        result = extract_a_share_annual_metrics([{"chunk_id": "c1", "evidence_id": "ev_annual", "text": ANNUAL_TEXT}])
        self.assertEqual("available", result["status"])
        self.assertAlmostEqual(38_239_935_640.67, result["metrics"]["revenue"]["2025"])
        self.assertAlmostEqual(.6025, result["metrics"]["revenue"]["yoy"])
        self.assertAlmostEqual(10_896_126_160.03, result["metrics"]["operating_cash_flow"]["2025"])
        self.assertAlmostEqual(.4384, result["metrics"]["weighted_roe"]["2025"])

    def test_annual_report_parser_handles_repeated_balance_sheet_year_header(self) -> None:
        realistic = ANNUAL_TEXT.replace(
            "16.58%\n45,288,970,887.78",
            "16.58%\n2025\n2024\n2023\n45,288,970,887.78",
        )
        result = extract_a_share_annual_metrics([{"chunk_id": "c-real", "evidence_id": "ev_real", "text": realistic}])
        self.assertAlmostEqual(45_288_970_887.78, result["metrics"]["total_assets"]["2025"])
        self.assertAlmostEqual(29_765_156_275.68, result["metrics"]["attributable_equity"]["2025"])

    def test_annual_report_parser_handles_sse_column_major_thousand_yuan_table(self) -> None:
        sse_text = """六、近三年主要会计数据和财务指标
主要会计数据 2025年 2024年 单位：千元 币种：人民币 本期比上年同期增减（%） 2023年
营业收入 利润总额 归属于上市公司股东的净利润
归属于上市公司股东的扣除非经常性损益的净利润 经营活动产生的现金流量净额
933,791.45 72,429.29 71,555.91 841,304.70 107,214.69 100,455.11
10.99 -32.44 -28.77 818,505.53 108,513.01 92,104.47
38,877.39 73,813.09 -47.33 56,173.16 51,923.11 211,092.36
2025年末 2024年末 -75.40 本期末比上年同期末增减（%） 17,430.33 2023年末
归属于上市公司股东的净资产 总资产
2,317,795.43 2,853,193.56 2,242,260.60 2,620,439.03 3.37 8.88 2,169,349.91 2,559,593.58
主要财务指标 2025年 2024年 2023年
基本每股收益 稀释每股收益 扣非基本每股收益 加权平均净资产收益率 扣非加权平均净资产收益率
0.45 0.45 0.25 3.14 1.70 0.64 0.63 0.47 4.55 3.34
-29.69 -28.57 -46.81 减少1.41个百分点 1.64 0.60 0.60 0.37 4.59 2.80
11.81 12.31 0.5 10.10
报告期末公司前三年主要会计数据和财务指标的说明"""
        result = extract_a_share_annual_metrics([
            {"chunk_id": "c-sse", "evidence_id": "ev_sse", "text": sse_text},
        ])
        self.assertEqual("available", result["status"])
        self.assertEqual("sse_column_major", result["table_layout"])
        self.assertAlmostEqual(933_791_450.0, result["metrics"]["revenue"]["2025"])
        self.assertAlmostEqual(71_555_910.0, result["metrics"]["attributable_net_income"]["2025"])
        self.assertAlmostEqual(51_923_110.0, result["metrics"]["operating_cash_flow"]["2025"])
        self.assertAlmostEqual(2_853_193_560.0, result["metrics"]["total_assets"]["2025"])
        self.assertAlmostEqual(0.0314, result["metrics"]["weighted_roe"]["2025"])
        self.assertAlmostEqual(-0.0141, result["metrics"]["weighted_roe"]["change_pp"])

    def test_operating_parser_extracts_product_margin_customer_and_risk_exposures(self) -> None:
        operating_text = """五、报告期内主要经营情况
单位：千元 币种：人民币
主营业务分产品情况
分产品 营业收入 营业成本 毛利率（%） 营业收入比上年增减（%） 营业成本比上年增减（%）
传输类 638,044.21 452,834.40 29.03 -11.84 -6.81
接入和数据类 281,722.66 214,343.50 23.92 180.55 150.39
合计 919,766.87 667,177.90 27.46 11.17 16.37
主营业务分地区情况
前五名客户销售额531,910.10千元，占年度销售总额56.96%。
传输类产品库存量大幅增长107.39%，主要是低速模块库存大幅增长。
"""
        balance_text = """（三）资产、负债情况分析 单位：千元 币种：人民币
存货 545,464.00 19.12 354,061.55 13.51 54.06 其他流动资产
固定资产 303,337.92 10.63 260,499.63 9.94 16.44 在建工程
在建工程 182,649.98 6.40 57,278.87 2.19 218.88 使用权资产
应付账款 333,765.55 11.70 200,958.97 7.67 66.09 应交税费
"""
        risk_text = """单位：千元 币种：人民币
公司应收账款账面价值为247,308.80千元，应收票据账面价值为224,782.07千元，
应收账款和应收票据合计占流动资产的比例为21.58%。
公司存货账面价值为545,464.00千元，占流动资产的比例为24.93%。
"""
        result = extract_operating_metrics([
            {
                "chunk_id": "operations",
                "evidence_id": "ev_annual",
                "chunk_section_type": "operating_results",
                "text": operating_text,
            },
            {
                "chunk_id": "balance",
                "evidence_id": "ev_annual",
                "chunk_section_type": "balance_sheet_analysis",
                "text": balance_text,
            },
            {
                "chunk_id": "risks",
                "evidence_id": "ev_annual",
                "chunk_section_type": "risk_factors",
                "text": risk_text,
            },
        ])
        self.assertEqual("available", result["status"])
        self.assertEqual("a_share_product_segment", result["table_layout"])
        self.assertEqual(["传输类", "接入和数据类"], [
            row["name"] for row in result["segments"]
        ])
        self.assertAlmostEqual(0.2746, result["current_gross_margin"])
        self.assertAlmostEqual(-0.0324, result["current_gross_margin"] - result["previous_gross_margin"], places=3)
        self.assertAlmostEqual(0.5696, result["customer_concentration"]["top_five_share"])
        self.assertAlmostEqual(545_464_000.0, result["balance_sheet_rows"]["inventory"]["current"])
        self.assertAlmostEqual(2.1888, result["balance_sheet_rows"]["construction_in_progress"]["yoy"])
        self.assertAlmostEqual(247_308_800.0, result["risk_exposures"]["receivables"])
        self.assertAlmostEqual(0.2493, result["risk_exposures"]["inventory_current_asset_share"])

    def test_collection_builds_real_corpus_graph_and_instruments(self) -> None:
        source = create_source()
        control = sqlite3.connect(":memory:")
        context = collect_stock_research_context(source, control, ticker="300308.SZ", market="A")
        self.assertEqual("中际旭创股份有限公司", context["identity"]["company_name"])
        self.assertEqual(1, len(context["corpus"]["filings"]))
        self.assertEqual(1, len(context["corpus"]["chunks"]))
        self.assertEqual("300502.SZ", context["graph"]["peers"][0])
        self.assertTrue(context["instruments"]["target"]["daily_bars"])

    def test_collection_excludes_accounting_and_internal_control_noise_chunks(self) -> None:
        source = create_source()
        source.execute(
            "INSERT INTO document_chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("noise1", "doc1", "annual_report", "cninfo", "300308.SZ", "A", "资产负债表", 9,
             "市场份额 未来需求 主营业务 内部控制制度建设及实施情况 " * 80,
             "ev_noise", "financial_statement", 1.0, 1.0, 1.0, 1.0, 1.0, None, 1),
        )
        source.commit()
        context = collect_stock_research_context(source, sqlite3.connect(":memory:"), ticker="300308.SZ", market="A")
        noise = next((item for item in context["corpus"]["chunks"] if item["evidence_id"] == "ev_noise"), None)
        if noise:
            self.assertFalse({"business", "industry", "products", "growth"}.intersection(noise["research_topics"]))

    def test_collection_supports_legacy_raw_chunk_schema(self) -> None:
        source = sqlite3.connect(":memory:")
        source.executescript(
            """
            CREATE TABLE filing_documents(
                filing_id TEXT,ticker TEXT,market TEXT,company_name TEXT,filing_type TEXT,title TEXT,
                published_at TEXT,source_key TEXT,source_url TEXT,parse_status TEXT
            );
            CREATE TABLE document_chunks(
                chunk_id TEXT,document_id TEXT,document_type TEXT,source_key TEXT,ticker TEXT,market TEXT,
                section_name TEXT,chunk_index INTEGER,text TEXT,evidence_id TEXT,created_at TEXT,metadata_json TEXT
            );
            """
        )
        source.execute(
            "INSERT INTO filing_documents VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("doc-old", "300308.SZ", "A", "中际旭创股份有限公司", "annual_report", "年度报告",
             "2026-03-31", "cninfo", "doc", "parsed"),
        )
        source.execute(
            "INSERT INTO document_chunks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("raw-1", "doc-old", "annual_report", "cninfo", "300308.SZ", "A", "主营业务", 0,
             ANNUAL_TEXT, "ev_raw", "2026-04-01", "{}"),
        )
        context = collect_stock_research_context(source, sqlite3.connect(":memory:"), ticker="300308.SZ", market="A")
        self.assertEqual("ev_raw", context["corpus"]["chunks"][0]["evidence_id"])
        self.assertIn("business", context["corpus"]["chunks"][0]["research_topics"])

    def test_report_is_long_form_cited_and_contains_no_system_metadata(self) -> None:
        source = create_source()
        control = sqlite3.connect(":memory:")
        plan = build_stock_research_plan("300308.SZ", "A")
        context = collect_stock_research_context(source, control, ticker="300308.SZ", market="A")
        context["instruments"]["target"]["valuation"] = {
            "current_price": 1128.35,
            "market_cap": 1_000_000_000_000,
            "pe_ttm": 80.0,
            "pb": 30.0,
            "generated_at": "2026-07-21T14:30:00+08:00",
            "source_evidence_ids": ["ev_valuation"],
            "metadata": {
                "verification_method": "tencent_price_baidu_valuation_cross_validation",
            },
        }
        analysis = build_stock_analysis_v3(context, plan)
        packet = {
            "schema_version": "2.0", "workflow_version": "3.0", "ticker": "300308.SZ", "market": "A",
            "generated_at": "2026-07-21T00:00:00+00:00",
            "quality": {"usable_evidence_ids": ["ev_annual", "ev_valuation"]},
            "research_v3": {"plan": plan, "context": context, "analysis": analysis},
        }
        report = compile_stock_research_report_v3(packet)
        validation = validate_stock_research_report_v3(report, packet, minimum_characters=2_500)
        self.assertEqual("passed", validation["status"], validation["errors"])
        self.assertIn("营业收入", report)
        self.assertIn("经营现金流", report)
        self.assertIn("[ev_annual]", report)
        self.assertNotIn("德科立", report)
        self.assertNotIn("任务编号：", report)
        self.assertNotIn("隔离字段数量", report)
        self.assertNotIn("监管指引第 4 号", report)
        self.assertNotIn("产品外观", report)
        self.assertIn("独立价格源本次不可用，未宣称双源价格核验", report)
        self.assertNotIn("价格已由两个独立行情源交叉核验", report)

    def test_broker_only_material_cannot_pass_as_a_deep_research_report(self) -> None:
        source = create_source()
        context = collect_stock_research_context(source, sqlite3.connect(":memory:"), ticker="300308.SZ", market="A")
        context["identity"]["company_name"] = "德科立"
        context["identity"]["ticker"] = "688205.SH"
        context["corpus"]["filings"] = []
        context["corpus"]["chunks"] = []
        context["corpus"]["broker_reports"] = [{
            "evidence_id": "broker:test_dekeli",
            "title": "DCI 放量与 OCS 布局",
            "source_name": "测试证券",
            "published_at": "2026-06-17",
            "rating": "增持",
            "research_topics": ["business", "industry", "products", "growth", "financials", "risks"],
            "text": (
                "2025年公司营业收入9.34亿元，传输类、接入及数据类收入占比分别为68.3%、30.2%。"
                "2026年一季度营收2.5亿元，同环比分别28.0%、5.0%；实现归母净利润0.2亿元，"
                "同环比分别35.1%、10.0%。现有产能约为12亿元，泰国工厂新增产能10亿元，"
                "无锡二期再新增10亿元产能，总产能将达到32亿元。"
            ),
        }]
        plan = build_stock_research_plan("688205.SH", "A")
        analysis = build_stock_analysis_v3(context, plan)
        packet = {
            "schema_version": "2.0", "workflow_version": "3.0", "ticker": "688205.SH", "market": "A",
            "generated_at": "2026-07-21T00:00:00+00:00", "quality": {"usable_evidence_ids": []},
            "research_v3": {"plan": plan, "context": context, "analysis": analysis},
        }
        report = compile_stock_research_report_v3(packet)
        validation = validate_stock_research_report_v3(report, packet, minimum_characters=3_500)
        self.assertEqual("failed", validation["status"])
        self.assertIn(
            "insufficient_primary_research_evidence",
            {item["code"] for item in validation["errors"]},
        )
        self.assertIn("二级研究材料", report)
        self.assertIn("不是已通过一手证据门的事实", report)
        self.assertIn("[broker:test_dekeli]", report)
        self.assertNotIn("本报告的价值是建立", report)
        self.assertNotIn("下一步必须补齐", report)
        self.assertNotIn("年报披露的多平台", report)
        self.assertNotIn("已经把高速光模块需求转化为", report)

    def test_unknown_citation_is_rejected(self) -> None:
        packet = {
            "quality": {"usable_evidence_ids": []},
            "research_v3": {"context": {"corpus": {}}, "analysis": {"coverage": {"score": 1.0}}},
        }
        report = "\n".join(f"## {name}" for name in (
            "投资摘要与核心判断", "公司画像与商业模式", "行业阶段与需求驱动", "产品矩阵与核心竞争力",
            "财务深度分析", "同行比较与竞争格局", "估值分析", "催化剂与时间表",
            "风险、反面证据与证伪条件", "三种情景", "后续跟踪指标", "结论", "证据索引",
        )) + "\n[ev_missing]" + "研究" * 2_000
        result = validate_stock_research_report_v3(report, packet)
        self.assertEqual("failed", result["status"])
        self.assertIn("unknown_report_citation", {item["code"] for item in result["errors"]})

    def test_numeric_narrative_contradiction_is_rejected(self) -> None:
        packet = {
            "quality": {"usable_evidence_ids": ["ev_official"]},
            "research_v3": {
                "context": {
                    "corpus": {
                        "filings": [{"filing_id": "f1"}],
                        "chunks": [{"evidence_id": "ev_official"}],
                    },
                },
                "analysis": {
                    "annual_financials": {
                        "status": "available",
                        "periods": ["2025", "2024", "2023"],
                        "metrics": {
                            "revenue": {"yoy": 0.10},
                            "attributable_net_income": {"yoy": -0.28},
                            "operating_cash_flow": {"yoy": -0.75},
                            "weighted_roe": {"change_pp": -0.0141},
                        },
                    },
                    "coverage": {"score": 1.0},
                },
            },
        }
        report = "\n".join(f"## {name}" for name in (
            "投资摘要与核心判断", "公司画像与商业模式", "行业阶段与需求驱动", "产品矩阵与核心竞争力",
            "经营模式、客户与供应链", "财务深度分析", "同行比较与竞争格局", "增长驱动与预测边界",
            "估值分析", "催化剂与时间表", "风险、反面证据与证伪条件", "三种情景",
            "后续跟踪指标", "结论", "证据索引",
        )) + "\n利润增速快于收入，三项指标同时上行，较上年提升。[ev_official]" + "研究" * 2_000
        result = validate_stock_research_report_v3(report, packet, minimum_characters=1_000)
        self.assertIn(
            "numeric_narrative_contradiction",
            {item["code"] for item in result["errors"]},
        )


if __name__ == "__main__":
    unittest.main()
