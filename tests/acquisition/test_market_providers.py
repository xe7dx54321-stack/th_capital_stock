from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from smr_app.acquisition.contracts import AcquisitionMode, AcquisitionRequest, DataRequirement
from smr_app.acquisition.kernel import AcquisitionKernel
from smr_app.acquisition.providers.market import (
    CrossValidatedValuationProvider,
    PeerComparisonProvider,
    SzseMarketProvider,
    TencentMarketProvider,
    expected_completed_a_share_session,
    parse_baidu_valuation,
    parse_eastmoney_quote,
    parse_szse_quote,
    parse_tencent_quote,
)
from smr_app.acquisition.store import AcquisitionStore
from smr_app.research.acquisition_materializer_v3 import materialize_acquired_stock_data
from smr_app.runtime.migrations import apply_migrations


UTC = timezone.utc


def _request(
    data_type: str,
    required_fields: tuple[str, ...],
    *,
    ticker: str = "300308.SZ",
) -> AcquisitionRequest:
    return AcquisitionRequest.create(
        DataRequirement(
            entity_key=ticker,
            data_type=data_type,
            market="A",
            required_fields=required_fields,
        ),
        AcquisitionMode.FORCE_REFRESH,
        "run_market_test",
        datetime(2026, 7, 22, 6, 30, tzinfo=UTC),
    )


def _tencent_line(
    code: str = "300308", name: str = "中际旭创", price: str = "1073.19",
    *, market_cap_100m: str = "11968.59", float_market_cap_100m: str = "11911.76",
    pe_ttm: str = "80.06", pb_mrq: str = "34.55",
) -> str:
    parts = [""] * 86
    parts[0] = "51"
    parts[1] = name
    parts[2] = code
    parts[3] = price
    parts[4] = "1136.55"
    parts[5] = "1110.00"
    parts[6] = "334656"
    parts[30] = "20260722142927"
    parts[32] = "-5.57"
    parts[33] = "1138.88"
    parts[34] = "1061.20"
    parts[37] = "3700761"
    parts[38] = "3.02"
    parts[39] = pe_ttm  # PE(TTM)
    parts[44] = float_market_cap_100m  # 流通市值（亿元）
    parts[45] = market_cap_100m  # 总市值（亿元）
    parts[46] = pb_mrq
    parts[52] = "52.18"  # 预测/动态 PE
    parts[53] = "109.57"  # 上年 PE
    return f'v_sz{code}="' + "~".join(parts) + '";'


def _eastmoney_payload(code: str = "300308", name: str = "中际旭创", price: int = 107319) -> dict:
    return {
        "data": {
            "f43": price,
            "f44": 113888,
            "f45": 106120,
            "f46": 111000,
            "f47": 334656,
            "f48": 37007606250.07,
            "f57": code,
            "f58": name,
            "f60": 113655,
            "f116": 1196858664374.79,
            "f117": 1191176270351.82,
            "f162": 5218,
            "f167": 3455,
            "f168": 302,
        }
    }


class FakeMarketTransport:
    def szse_quote(self, code: str):
        return {
            "datetime": "2026-07-22 14:29",
            "code": "0",
            "data": {
                "code": code,
                "name": "中际旭创" if code == "300308" else f"同行{code}",
                "close": "1136.55",
                "open": "1110.00",
                "now": "1073.19" if code == "300308" else "100.00",
                "high": "1138.88",
                "low": "1061.20",
                "volume": 334656,
                "amount": 37007606250.07,
                "delta": "-63.36",
                "deltaPercent": "-5.57",
                "marketTime": "2026-07-22 14:29:27",
            },
        }

    def szse_history(self, code: str):
        return {
            "code": "0",
            "data": {
                "code": code,
                "picupdata": [
                    ["2026-07-17", "1057.36", "979.46", "950.55", "1072.00", "-133.54", "-12.00", 561861, 56485631462.0],
                    ["2026-07-20", "1028.43", "1004.00", "967.68", "1057.77", "24.54", "2.51", 453665, 46094376324.0],
                    ["2026-07-21", "1020.01", "1136.55", "988.82", "1136.80", "132.55", "13.20", 481157, 51302197634.0],
                    ["2026-07-22", "1110.00", "1073.19", "1061.20", "1138.88", "-63.36", "-5.57", 334656, 37007606250.0],
                ],
            },
        }

    def tencent_quote(self, ticker: str):
        code = ticker.split(".", 1)[0]
        if code == "300308":
            return _tencent_line(code=code)
        return _tencent_line(
            code=code, name=f"同行{code}", price="100.00", market_cap_100m="1000.00",
            float_market_cap_100m="800.00", pe_ttm="25.00", pb_mrq="4.00",
        )

    def tencent_history(self, ticker: str):
        key = "sz" + ticker.split(".", 1)[0]
        return {
            "code": 0,
            "data": {
                key: {
                    "qfqday": [
                        ["2026-07-20", "1028.43", "1004.00", "1057.77", "967.68", "453665"],
                        ["2026-07-21", "1020.01", "1136.55", "1136.80", "988.82", "481157"],
                        ["2026-07-22", "1110.00", "1073.19", "1138.88", "1061.20", "334656"],
                    ]
                }
            },
        }

    def eastmoney_quote(self, ticker: str):
        code = ticker.split(".", 1)[0]
        if code == "300308":
            return _eastmoney_payload()
        payload = _eastmoney_payload(code=code, name=f"同行{code}", price=10000)
        payload["data"].update({"f116": 100_000_000_000, "f117": 80_000_000_000, "f162": 2500, "f167": 400, "f168": 100})
        return payload

    def eastmoney_quotes(self, tickers: list[str]):
        return {"data": {"diff": [
            ({
                "f2": 1073.19, "f3": -5.57, "f5": 334656, "f6": 37007606250.07,
                "f8": 3.02, "f9": 52.18, "f12": "300308", "f14": "中际旭创",
                "f15": 1138.88, "f16": 1061.20, "f17": 1110.0, "f18": 1136.55,
                "f20": 1_196_858_664_374.79, "f21": 1_191_176_270_351.82, "f23": 34.55,
            } if ticker.startswith("300308") else {
                "f2": 100.0, "f3": 0.0, "f5": 1000, "f6": 10_000_000,
                "f8": 1.0, "f9": 25.0, "f12": ticker.split(".", 1)[0],
                "f14": f"同行{ticker.split('.', 1)[0]}", "f15": 101.0, "f16": 99.0,
                "f17": 100.0, "f18": 100.0, "f20": 100_000_000_000,
                "f21": 80_000_000_000, "f23": 4.0,
            })
            for ticker in tickers
        ]}}

    def baidu_valuation(self, ticker: str, indicator: str):
        code = ticker.split(".", 1)[0]
        if code == "300308":
            values = {"总市值": 11968.59, "市盈率(TTM)": 80.06, "市净率": 34.55}
        else:
            values = {"总市值": 1000.0, "市盈率(TTM)": 25.0, "市净率": 4.0}
        return {
            "Result": [{"DisplayData": {"resultData": {"tplData": {"result": {
                "chartInfo": [{"body": [["2026-07-22", str(values[indicator])]], "unit": ""}]
            }}}}}]
        }


class MarketProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeMarketTransport()
        self.clock = lambda: datetime(2026, 7, 22, 6, 30, tzinfo=UTC)  # 上海 14:30，日线只认前一交易日

    def test_expected_completed_session_respects_intraday_weekend_and_holiday(self) -> None:
        self.assertEqual("2026-07-21", expected_completed_a_share_session(datetime(2026, 7, 22, 6, 30, tzinfo=UTC)))
        self.assertEqual("2026-07-17", expected_completed_a_share_session(datetime(2026, 7, 19, 8, 0, tzinfo=UTC)))
        self.assertEqual("2026-06-18", expected_completed_a_share_session(datetime(2026, 6, 19, 11, 0, tzinfo=UTC)))

    def test_tencent_parser_uses_total_market_cap_and_real_ttm_pe_fields(self) -> None:
        quote = parse_tencent_quote(_tencent_line(), "300308.SZ")
        self.assertAlmostEqual(1_196_859_000_000, quote["market_cap_cny"])
        self.assertAlmostEqual(1_191_176_000_000, quote["float_market_cap_cny"])
        self.assertEqual(80.06, quote["pe_ttm"])
        self.assertEqual(52.18, quote["pe_forward"])
        self.assertEqual(34.55, quote["pb_mrq"])
        self.assertNotIn("ps_ttm", quote)

    def test_eastmoney_parser_applies_documented_scaling(self) -> None:
        quote = parse_eastmoney_quote(_eastmoney_payload(), "300308.SZ", "2026-07-22T14:29:27+08:00")
        self.assertEqual(1073.19, quote["price"])
        self.assertEqual(52.18, quote["pe_ttm"])
        self.assertEqual(34.55, quote["pb_mrq"])
        self.assertAlmostEqual(1_196_858_664_374.79, quote["market_cap_cny"])

    def test_baidu_parser_uses_latest_valid_dated_value(self) -> None:
        payload = self.transport.baidu_valuation("300308.SZ", "市盈率(TTM)")
        payload["Result"][0]["DisplayData"]["resultData"]["tplData"]["result"]["chartInfo"][0]["body"].insert(
            0, ["2026-07-21", "79.00"]
        )
        parsed = parse_baidu_valuation(payload, "300308.SZ", "市盈率(TTM)")
        self.assertEqual("2026-07-22", parsed["date"])
        self.assertEqual(80.06, parsed["value"])

    def test_szse_daily_bars_exclude_unfinished_intraday_bar(self) -> None:
        provider = SzseMarketProvider(transport=self.transport, clock=self.clock)
        batch = provider.acquire(_request("daily_bars", ("trade_date", "open", "high", "low", "close", "volume")))
        self.assertEqual("2026-07-21", batch.available_through)
        self.assertEqual({"trade_date", "open", "high", "low", "close", "volume"}, set(batch.required_fields_present))
        self.assertFalse(any(fact.as_of == "2026-07-22" for fact in batch.facts))
        latest_close = [fact for fact in batch.facts if fact.as_of == "2026-07-21" and fact.field_name == "close"]
        self.assertEqual(1136.55, latest_close[0].value)

    def test_szse_realtime_quote_preserves_official_timestamp_and_currency(self) -> None:
        provider = SzseMarketProvider(transport=self.transport, clock=self.clock)
        batch = provider.acquire(_request("realtime_quote", ("price", "quote_time", "currency")))
        facts = {fact.field_name: fact.value for fact in batch.facts}
        self.assertEqual(1073.19, facts["price"])
        self.assertEqual("2026-07-22T14:29:27+08:00", facts["quote_time"])
        self.assertEqual("CNY", facts["currency"])
        self.assertEqual("official", batch.documents[0].authority_tier.value)

    def test_szse_quote_repairs_non_cumulative_top_level_volume_from_minute_rows(self) -> None:
        payload = self.transport.szse_quote("300308")
        payload["data"]["volume"] = 689
        payload["data"]["picupdata"] = [
            ["14:55", "1061.00", "1100.00", "-75.55", "-6.65", 1000, 106_100_000],
            ["14:56", "1060.80", "1099.00", "-75.75", "-6.66", 2000, 212_160_000],
        ]
        quote = parse_szse_quote(payload, "300308.SZ")
        self.assertEqual(3000, quote["volume_lots"])
        self.assertEqual("minute_rows_sum", quote["volume_source"])

    def test_tencent_provider_is_a_real_fallback_for_daily_bars(self) -> None:
        provider = TencentMarketProvider(transport=self.transport, clock=self.clock)
        batch = provider.acquire(_request("daily_bars", ("trade_date", "open", "high", "low", "close", "volume")))
        self.assertEqual("2026-07-21", batch.available_through)
        self.assertEqual("reputable_secondary", batch.documents[0].authority_tier.value)

    def test_cross_validated_valuation_rejects_price_disagreement(self) -> None:
        class BadTransport(FakeMarketTransport):
            def szse_quote(self, code: str):
                payload = super().szse_quote(code)
                payload["data"]["now"] = "900.00"
                return payload

        provider = CrossValidatedValuationProvider(transport=BadTransport(), clock=self.clock)
        with self.assertRaisesRegex(ValueError, "price disagreement"):
            provider.acquire(_request("valuation_snapshot", ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of")))

    def test_cross_validated_valuation_has_traceable_formula_inputs(self) -> None:
        provider = CrossValidatedValuationProvider(transport=self.transport, clock=self.clock)
        batch = provider.acquire(_request("valuation_snapshot", ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of")))
        facts = {fact.field_name: fact.value for fact in batch.facts}
        self.assertEqual(1073.19, facts["price"])
        self.assertAlmostEqual(1_196_859_000_000, facts["market_cap"])
        self.assertEqual(80.06, facts["pe_ttm"])
        self.assertEqual(34.55, facts["pb_mrq"])
        self.assertEqual("cross_validated", batch.quality_status)
        self.assertEqual(3, len(batch.documents))

    def test_shanghai_target_uses_eastmoney_tencent_baidu_cross_validation(self) -> None:
        provider = CrossValidatedValuationProvider(transport=self.transport, clock=self.clock)
        batch = provider.acquire(_request(
            "valuation_snapshot",
            ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of"),
            ticker="688205.SH",
        ))
        facts = {fact.field_name: fact.value for fact in batch.facts}
        self.assertEqual(100.0, facts["price"])
        self.assertEqual(25.0, facts["pe_ttm"])
        self.assertEqual("eastmoney_tencent_baidu_cross_validation", batch.metadata["verification_method"])
        self.assertEqual("secondary_market_quote", batch.documents[0].source_type)

    def test_shanghai_valuation_survives_eastmoney_transport_failure(self) -> None:
        class EastmoneyFailureTransport(FakeMarketTransport):
            def eastmoney_quote(self, ticker: str):
                raise RuntimeError("eastmoney unavailable")

        provider = CrossValidatedValuationProvider(
            transport=EastmoneyFailureTransport(),
            clock=self.clock,
        )
        batch = provider.acquire(_request(
            "valuation_snapshot",
            ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of"),
            ticker="688205.SH",
        ))
        facts = {fact.field_name: fact.value for fact in batch.facts}
        self.assertEqual(100.0, facts["price"])
        self.assertEqual(25.0, facts["pe_ttm"])
        self.assertEqual("cross_validated", batch.quality_status)
        self.assertEqual(
            "tencent_price_baidu_valuation_cross_validation",
            batch.metadata["verification_method"],
        )
        self.assertTrue(batch.metadata["price_source_fallback"])
        self.assertIn("eastmoney unavailable", batch.metadata["price_source_error"])

    def test_previous_session_baidu_values_are_price_scaled_before_validation(self) -> None:
        class PreviousSessionTransport(FakeMarketTransport):
            def baidu_valuation(self, ticker: str, indicator: str):
                payload = super().baidu_valuation(ticker, indicator)
                scale = 1073.19 / 1136.55
                current = {"总市值": 11968.59, "市盈率(TTM)": 80.06, "市净率": 34.55}[indicator]
                chart = payload["Result"][0]["DisplayData"]["resultData"]["tplData"]["result"]["chartInfo"][0]
                chart["body"] = [["2026-07-21", str(current / scale)]]
                return payload

        provider = CrossValidatedValuationProvider(transport=PreviousSessionTransport(), clock=self.clock)
        batch = provider.acquire(_request("valuation_snapshot", ("price", "market_cap", "pe_ttm", "pb_mrq", "as_of")))
        self.assertEqual("2026-07-21", batch.metadata["baidu_source_date"])
        self.assertEqual(80.06, {fact.field_name: fact.value for fact in batch.facts}["pe_ttm"])

    def test_peer_matrix_uses_explicit_registry_and_one_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "peers.json"
            config_path.write_text(json.dumps({
                "300308.SZ": {
                    "methodology": "同属 A 股高速光模块产业链，按业务直接可比性筛选",
                    "peers": [
                        {"ticker": "300502.SZ", "name": "新易盛", "reason": "高速光模块直接可比"},
                        {"ticker": "300394.SZ", "name": "天孚通信", "reason": "光器件与光引擎可比"},
                    ],
                }
            }, ensure_ascii=False), encoding="utf-8")
            provider = PeerComparisonProvider(config_path=config_path, transport=self.transport, clock=self.clock)
            batch = provider.acquire(_request("peer_comparison", ("peer_set", "selection_reason", "comparable_metrics", "as_of")))
        facts = {fact.field_name: fact.value for fact in batch.facts}
        self.assertEqual(["300502.SZ", "300394.SZ"], facts["peer_set"])
        self.assertEqual(2, len(facts["comparable_metrics"]))
        self.assertTrue(all(row["as_of"] == "2026-07-22T14:29:27+08:00" for row in facts["comparable_metrics"]))
        self.assertIn("高速光模块", facts["selection_reason"])

    def test_peer_matrix_isolates_material_pb_disagreement_instead_of_publishing_it(self) -> None:
        class PbDisagreementTransport(FakeMarketTransport):
            def baidu_valuation(self, ticker: str, indicator: str):
                payload = super().baidu_valuation(ticker, indicator)
                if indicator == "市净率":
                    payload["Result"][0]["DisplayData"]["resultData"]["tplData"]["result"]["chartInfo"][0]["body"] = [
                        ["2026-07-22", "2.00"]
                    ]
                return payload

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "peers.json"
            config_path.write_text(json.dumps({
                "300308.SZ": {
                    "methodology": "同产业链显式同行",
                    "peers": [{"ticker": "300502.SZ", "name": "新易盛", "reason": "直接可比"}],
                }
            }, ensure_ascii=False), encoding="utf-8")
            provider = PeerComparisonProvider(
                config_path=config_path, transport=PbDisagreementTransport(), clock=self.clock,
            )
            batch = provider.acquire(_request("peer_comparison", ("peer_set", "selection_reason", "comparable_metrics", "as_of")))
        peer = {fact.field_name: fact.value for fact in batch.facts}["comparable_metrics"][0]
        self.assertIsNone(peer["pb_mrq"])
        self.assertIn("pb_source_disagreement_not_rankable", peer["valuation_flags"])

    def test_market_facts_materialize_into_v3_context_without_legacy_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "control.db"
            config_path = root / "peers.json"
            config_path.write_text(json.dumps({
                "300308.SZ": {
                    "methodology": "同属 A 股高速光模块产业链，采用同币种同一时点口径",
                    "peers": [{"ticker": "300502.SZ", "name": "新易盛", "reason": "高速光模块直接可比"}],
                }
            }, ensure_ascii=False), encoding="utf-8")
            apply_migrations(db_path)
            store = AcquisitionStore(db_path)
            providers = [
                SzseMarketProvider(transport=self.transport, clock=self.clock),
                TencentMarketProvider(transport=self.transport, clock=self.clock),
                CrossValidatedValuationProvider(transport=self.transport, clock=self.clock),
                PeerComparisonProvider(config_path=config_path, transport=self.transport, clock=self.clock),
            ]
            kernel = AcquisitionKernel(store, providers, clock=self.clock)
            requirements = (
                DataRequirement("300308.SZ", "daily_bars", "A", required_fields=("trade_date", "open", "high", "low", "close", "volume")),
                DataRequirement("300308.SZ", "realtime_quote", "A", required_fields=("price", "quote_time", "currency")),
                DataRequirement("300308.SZ", "valuation_snapshot", "A", required_fields=("price", "market_cap", "pe_ttm", "pb_mrq", "as_of")),
                DataRequirement("300308.SZ", "peer_comparison", "A", required_fields=("peer_set", "selection_reason", "comparable_metrics", "as_of")),
            )
            for requirement in requirements:
                result = kernel.acquire(requirement, mode=AcquisitionMode.FORCE_REFRESH)
                self.assertEqual("acquired", result.status)
            fundamentals, valuation, evidence, freshness = {}, {}, {"items": []}, {"blocking_level": "block"}
            context = {"provider_status": {}, "corpus": {"filings": [], "chunks": []}, "graph": {}, "instruments": {"target": {}, "peers": []}}
            result = materialize_acquired_stock_data(
                store, ticker="300308.SZ", fundamentals=fundamentals, valuation=valuation,
                evidence=evidence, research_context=context, freshness=freshness,
            )
        self.assertEqual(3, result["daily_bars_materialized"])
        self.assertTrue(result["quote_materialized"])
        self.assertTrue(result["valuation_materialized"])
        self.assertEqual(1, result["peers_materialized"])
        self.assertEqual("2026-07-21", context["instruments"]["target"]["daily_bars"][0]["trade_date"])
        self.assertEqual(1073.19, context["instruments"]["target"]["quote"]["price"])
        self.assertEqual(80.06, valuation["pe_ttm"])
        self.assertEqual("300502.SZ", context["instruments"]["peers"][0]["ticker"])
        self.assertEqual("fresh", freshness["status"])


if __name__ == "__main__":
    unittest.main()
