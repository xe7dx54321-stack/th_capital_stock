"""
scan_theme_extension.py 的单元测试

小白讲解：这个测试文件验证主题扩展管道的核心逻辑：
1. watchlist_registry 解析是否正确
2. 主题匹配逻辑是否正确
3. 关键词反向匹配是否能找出"关键词库里有但 watchlist 里没有"的公司名
4. 市场判断是否正确
5. dry-run 模式能正常跑完不报错
"""

import sys
from pathlib import Path

import pytest

# 把项目根目录加到 sys.path，让测试能 import 到 08_scripts 下的模块
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))

from scan_theme_extension import (  # noqa: E402
    THEME_KEYWORDS,
    GENERIC_TERMS,
    determine_market,
    find_keyword_candidates,
    match_stock_to_theme,
    parse_watchlist_registry,
    parse_watchlist_with_names,
    run_scan,
)


# ============================================================
# 测试 watchlist 解析
# ============================================================

class TestParseWatchlist:
    """测试 watchlist_registry.md 的解析函数"""

    def test_parse_watchlist_registry_returns_set(self):
        """
        验证 parse_watchlist_registry 返回的是一个集合（set），
        且包含已知的标的代码。
        """
        watchlist_path = PROJECT_ROOT / "00_control" / "watchlist_registry.md"
        if not watchlist_path.exists():
            pytest.skip("watchlist_registry.md 不存在")

        codes = parse_watchlist_registry(watchlist_path)

        # 应该返回一个 set
        assert isinstance(codes, set)
        # 应该有标的（watchlist 里有 49 个标的）
        assert len(codes) > 0

        # 验证一些已知的代码
        # A股：中际旭创 300308 -> 300308.SZ
        assert "300308.SZ" in codes, "应该包含 300308.SZ（中际旭创）"
        # A股：海光信息 688041 -> 688041.SH
        assert "688041.SH" in codes, "应该包含 688041.SH（海光信息）"
        # 美股：NVDA
        assert "NVDA" in codes, "应该包含 NVDA（英伟达）"

    def test_parse_watchlist_with_names_returns_list(self):
        """
        验证 parse_watchlist_with_names 返回列表，
        每条记录有 ts_code、name、sector、market 字段。
        """
        watchlist_path = PROJECT_ROOT / "00_control" / "watchlist_registry.md"
        if not watchlist_path.exists():
            pytest.skip("watchlist_registry.md 不存在")

        items = parse_watchlist_with_names(watchlist_path)

        assert isinstance(items, list)
        assert len(items) > 0

        # 检查第一条记录的结构
        first = items[0]
        assert "ts_code" in first
        assert "name" in first
        assert "sector" in first
        assert "market" in first

        # 验证中际旭创在列表里
        zhongji = [x for x in items if x["ts_code"] == "300308.SZ"]
        assert len(zhongji) == 1, "应该能找到中际旭创"
        assert "中际" in zhongji[0]["name"], "中际旭创的名称应该包含'中际'"
        assert zhongji[0]["sector"] == "semiconductor_photonics"


# ============================================================
# 测试主题匹配
# ============================================================

class TestMatchStockToTheme:
    """测试 match_stock_to_theme 函数"""

    def test_match_by_sector_directly(self):
        """
        验证：如果 sector 直接就是主题 key，应该直接匹配。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = match_stock_to_theme(
            ts_code="300308.SZ",
            sector="semiconductor_photonics",
            stock_name="中际旭创",
            themes=themes,
        )
        assert result == "semiconductor_photonics"

    def test_match_by_keyword_in_name(self):
        """
        验证：如果股票名称包含某个主题的关键词，应该匹配到那个主题。
        比如"中际旭创"包含"中际"，应该匹配到 semiconductor_photonics。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = match_stock_to_theme(
            ts_code="300308.SZ",
            sector="",  # sector 为空，靠名称匹配
            stock_name="中际旭创",
            themes=themes,
        )
        assert result == "semiconductor_photonics"

    def test_match_by_keyword_in_sector_text(self):
        """
        验证：如果 sector 标签包含主题关键词，应该匹配。
        比如 sector="光模块龙头"，包含"光模块"，应该匹配到 semiconductor_photonics。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = match_stock_to_theme(
            ts_code="999999.SZ",
            sector="光模块龙头",
            stock_name="某公司",
            themes=themes,
        )
        assert result == "semiconductor_photonics"

    def test_no_match_returns_none(self):
        """
        验证：如果股票和任何主题都不相关，应该返回 None。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = match_stock_to_theme(
            ts_code="999999.SZ",
            sector="消费品",
            stock_name="某食品公司",
            themes=themes,
        )
        assert result is None

    def test_quantum_match(self):
        """
        验证：量子主题的关键词能正确匹配。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = match_stock_to_theme(
            ts_code="688027.SH",
            sector="quantum",
            stock_name="国盾量子",
            themes=themes,
        )
        assert result == "quantum"


# ============================================================
# 测试关键词反向匹配
# ============================================================

class TestFindKeywordCandidates:
    """测试 find_keyword_candidates 函数"""

    def test_returns_dict(self):
        """
        验证返回类型是 dict。
        """
        themes = list(THEME_KEYWORDS.keys())
        result = find_keyword_candidates(themes, [])
        assert isinstance(result, dict)

    def test_finds_missing_keywords(self):
        """
        验证：当 watchlist 为空时，所有非通用词关键词都应该被识别为潜在候选。
        """
        themes = ["semiconductor_compute"]
        result = find_keyword_candidates(themes, [])

        # semiconductor_compute 主题应该有潜在候选
        assert "semiconductor_compute" in result
        # 应该包含公司名关键词（如"海光"、"寒武纪"）
        assert "海光" in result["semiconductor_compute"]
        assert "寒武纪" in result["semiconductor_compute"]

    def test_excludes_generic_terms(self):
        """
        验证：通用词（如"芯片"、"半导体"）不应该出现在潜在候选里。
        """
        themes = ["semiconductor_compute"]
        result = find_keyword_candidates(themes, [])

        if "semiconductor_compute" in result:
            for kw in result["semiconductor_compute"]:
                assert kw not in GENERIC_TERMS, f"'{kw}' 是通用词，不应出现在候选里"

    def test_excludes_keywords_already_in_watchlist(self):
        """
        验证：已经在 watchlist 标的名中出现的关键词，不应该被识别为潜在候选。
        """
        themes = ["semiconductor_photonics"]
        # 模拟 watchlist 里有"中际旭创"
        watchlist = [
            {"ts_code": "300308.SZ", "name": "中际旭创", "sector": "semiconductor_photonics"},
        ]
        result = find_keyword_candidates(themes, watchlist)

        # "中际"在"中际旭创"里，所以不应该出现在候选里
        if "semiconductor_photonics" in result:
            assert "中际" not in result["semiconductor_photonics"], \
                "'中际'已在 watchlist（中际旭创），不应出现在候选里"

    def test_with_real_watchlist(self):
        """
        验证：用真实的 watchlist_registry 数据，应该能找到一些潜在候选。
        """
        watchlist_path = PROJECT_ROOT / "00_control" / "watchlist_registry.md"
        if not watchlist_path.exists():
            pytest.skip("watchlist_registry.md 不存在")

        watchlist = parse_watchlist_with_names(watchlist_path)
        themes = list(THEME_KEYWORDS.keys())
        result = find_keyword_candidates(themes, watchlist)

        # 应该至少有一些潜在候选（因为关键词库里有些公司不在 watchlist 里）
        total = sum(len(v) for v in result.values())
        assert total > 0, "应该能找到一些潜在候选关键词"

        # 具身智能的所有公司名关键词应该都在 watchlist 里了
        # （因为 watchlist 里有拓普、绿的、汇川等）
        # 所以 embodied_ai 的潜在候选应该是 0 或不存在
        embodied_count = len(result.get("embodied_ai", []))
        assert embodied_count == 0, "embodied_ai 的公司名关键词应该都在 watchlist 里了"


# ============================================================
# 测试市场判断
# ============================================================

class TestDetermineMarket:
    """测试 determine_market 函数"""

    def test_a_share_sh(self):
        """验证沪市 A 股"""
        assert determine_market("688041.SH") == "A"

    def test_a_share_sz(self):
        """验证深市 A 股"""
        assert determine_market("300308.SZ") == "A"

    def test_h_share(self):
        """验证港股"""
        assert determine_market("09980.HK") == "H"

    def test_us_share(self):
        """验证美股"""
        assert determine_market("NVDA") == "US"

    def test_unknown(self):
        """验证未知市场"""
        assert determine_market("123XYZ") == "其他"


# ============================================================
# 测试主流程（dry-run）
# ============================================================

class TestRunScan:
    """测试 run_scan 主流程"""

    def test_dry_run_completes_without_error(self):
        """
        验证：dry-run 模式能完整跑完，不报错，且返回正确的摘要结构。
        """
        summary = run_scan(dry_run=True)

        # 验证返回的摘要结构
        assert isinstance(summary, dict)
        assert "themes_scanned" in summary
        assert "existing_count" in summary
        assert "db_stock_count" in summary
        assert "new_candidates" in summary
        assert "keyword_candidates" in summary
        assert "dry_run" in summary
        assert "discovery_date" in summary

        # dry-run 模式
        assert summary["dry_run"] is True

        # 应该扫描了 5 个主题
        assert summary["themes_scanned"] == 5

        # watchlist 应该有标的
        assert summary["existing_count"] > 0

        # 应该有一些潜在候选关键词
        assert summary["keyword_candidates"] > 0, "应该能找到一些潜在候选关键词"
