"""
scan_us_benchmark_extension.py 的单元测试

小白讲解：这个测试文件验证美股对标映射管道的核心逻辑：
1. 美股对标映射匹配是否正确
2. 关键词反向匹配是否能找出"映射词库里有但 watchlist 里没有"的公司名
3. dry-run 模式能正常跑完不报错
"""

import sys
from pathlib import Path

import pytest

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))

from scan_us_benchmark_extension import (  # noqa: E402
    US_BENCHMARK_MAPPING,
    GENERIC_TERMS,
    find_benchmark_keyword_candidates,
    match_stock_to_us_benchmark,
    run_scan,
)


# ============================================================
# 测试美股对标映射匹配
# ============================================================

class TestMatchStockToUsBenchmark:
    """测试 match_stock_to_us_benchmark 函数"""

    def test_match_nvda_mapping(self):
        """
        验证：包含"海光"的股票应该匹配到 NVDA（英伟达）。
        """
        matches = match_stock_to_us_benchmark("688041.SH", "海光信息")
        assert len(matches) > 0
        nvda_match = [m for m in matches if m["us_symbol"] == "NVDA"]
        assert len(nvda_match) == 1
        assert nvda_match[0]["sector"] == "semiconductor_compute"

    def test_match_tsla_mapping(self):
        """
        验证：包含"拓普"的股票应该匹配到 TSLA（特斯拉）。
        """
        matches = match_stock_to_us_benchmark("601689.SH", "拓普集团")
        assert len(matches) > 0
        tsla_match = [m for m in matches if m["us_symbol"] == "TSLA"]
        assert len(tsla_match) == 1
        assert tsla_match[0]["sector"] == "embodied_ai"

    def test_match_multiple_benchmarks(self):
        """
        验证：一只股票可以匹配多个美股对标。
        比如"海光信息"包含"海光"，同时匹配 NVDA 和 AMD 和 INTC。
        """
        matches = match_stock_to_us_benchmark("688041.SH", "海光信息")
        us_symbols = {m["us_symbol"] for m in matches}
        # 海光信息应该匹配到 NVDA、AMD、INTC（它们都有"海光"关键词）
        assert "NVDA" in us_symbols
        assert "AMD" in us_symbols
        assert "INTC" in us_symbols

    def test_no_match_returns_empty(self):
        """
        验证：和所有美股对标都无关的股票返回空列表。
        """
        matches = match_stock_to_us_benchmark("999999.SZ", "某食品公司")
        assert matches == []

    def test_ionq_quantum_mapping(self):
        """
        验证：量子主题的美股对标能正确匹配。
        "国盾量子"应该匹配到 IONQ、RGTI、QBTS。
        """
        matches = match_stock_to_us_benchmark("688027.SH", "国盾量子")
        us_symbols = {m["us_symbol"] for m in matches}
        assert "IONQ" in us_symbols
        assert "RGTI" in us_symbols
        assert "QBTS" in us_symbols


# ============================================================
# 测试关键词反向匹配
# ============================================================

class TestFindBenchmarkKeywordCandidates:
    """测试 find_benchmark_keyword_candidates 函数"""

    def test_returns_dict(self):
        """验证返回类型是 dict"""
        result = find_benchmark_keyword_candidates([])
        assert isinstance(result, dict)

    def test_finds_missing_when_watchlist_empty(self):
        """
        验证：当 watchlist 为空时，所有非通用词映射关键词都应被识别为潜在候选。
        """
        result = find_benchmark_keyword_candidates([])

        # NVDA 应该有缺失的映射关键词
        assert "NVDA" in result
        assert len(result["NVDA"]["missing_keywords"]) > 0
        # 应该包含"海光"
        assert "海光" in result["NVDA"]["missing_keywords"]

    def test_excludes_generic_terms(self):
        """验证：通用词不会出现在候选里"""
        result = find_benchmark_keyword_candidates([])

        for us_symbol, info in result.items():
            for kw in info["missing_keywords"]:
                assert kw not in GENERIC_TERMS, \
                    f"'{kw}' 是通用词，不应出现在候选里"

    def test_excludes_keywords_in_watchlist(self):
        """
        验证：已在 watchlist 中的关键词不会出现在候选里。
        比如"海光"在"海光信息"里（如果在 watchlist），不应出现。
        """
        watchlist = [
            {"ts_code": "688041.SH", "name": "海光信息", "sector": "semiconductor_compute"},
        ]
        result = find_benchmark_keyword_candidates(watchlist)

        # NVDA 的缺失关键词里不应该有"海光"
        if "NVDA" in result:
            assert "海光" not in result["NVDA"]["missing_keywords"], \
                "'海光'已在 watchlist（海光信息），不应出现在候选里"

    def test_with_real_watchlist(self):
        """
        验证：用真实的 watchlist_registry 数据，应该能找到一些潜在候选。
        """
        from scan_theme_extension import parse_watchlist_with_names

        watchlist_path = PROJECT_ROOT / "00_control" / "watchlist_registry.md"
        if not watchlist_path.exists():
            pytest.skip("watchlist_registry.md 不存在")

        watchlist = parse_watchlist_with_names(watchlist_path)
        result = find_benchmark_keyword_candidates(watchlist)

        total = sum(len(v["missing_keywords"]) for v in result.values())
        assert total > 0, "应该能找到一些潜在候选关键词"

    def test_mapping_type_preserved(self):
        """验证：映射类型（业务对标/供应链对标/估值锚对标）被正确保留"""
        result = find_benchmark_keyword_candidates([])

        # NVDA 是业务对标
        if "NVDA" in result:
            assert result["NVDA"]["mapping_type"] == "业务对标"
        # IONQ 是估值锚对标
        if "IONQ" in result:
            assert result["IONQ"]["mapping_type"] == "估值锚对标"
        # VRT 是供应链对标
        if "VRT" in result:
            assert result["VRT"]["mapping_type"] == "供应链对标"


# ============================================================
# 测试主流程
# ============================================================

class TestRunScan:
    """测试 run_scan 主流程"""

    def test_dry_run_completes_without_error(self):
        """
        验证：dry-run 模式能完整跑完，不报错，且返回正确的摘要结构。
        """
        summary = run_scan(dry_run=True)

        assert isinstance(summary, dict)
        assert "us_benchmarks_scanned" in summary
        assert "existing_count" in summary
        assert "db_stock_count" in summary
        assert "new_candidates" in summary
        assert "keyword_candidates" in summary
        assert "dry_run" in summary
        assert "discovery_date" in summary

        assert summary["dry_run"] is True
        # 应该扫描了 18 只美股对标
        assert summary["us_benchmarks_scanned"] == 18
        assert summary["existing_count"] > 0
        # 应该有潜在候选关键词
        assert summary["keyword_candidates"] > 0, "应该能找到一些潜在候选关键词"
