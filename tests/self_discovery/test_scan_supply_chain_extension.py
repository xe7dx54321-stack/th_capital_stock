"""
scan_supply_chain_extension.py 的单元测试

小白讲解：这个测试文件验证产业链扩展管道的核心逻辑：
1. 供应链上下游匹配逻辑是否正确
2. 关键词反向匹配是否能找出"供应链关键词里有但 watchlist 里没有"的公司名
3. dry-run 模式能正常跑完不报错
"""

import sys
from pathlib import Path

import pytest

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))

from scan_supply_chain_extension import (  # noqa: E402
    SUPPLY_CHAIN_KEYWORDS,
    GENERIC_TERMS,
    find_supply_chain_keyword_candidates,
    match_stock_to_supply_chain,
    run_scan,
)


# ============================================================
# 测试供应链匹配
# ============================================================

class TestMatchStockToSupplyChain:
    """测试 match_stock_to_supply_chain 函数"""

    def test_match_upstream_keyword(self):
        """
        验证：股票名称包含上游关键词时，能匹配到上游位置。
        比如"北方华创"包含"北方华创"（半导体设备上游），应该匹配。
        """
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        matches = match_stock_to_supply_chain(
            ts_code="002371.SZ",
            sector="",
            stock_name="北方华创",
            themes=themes,
        )
        # 应该匹配到 semiconductor_compute 的 upstream
        assert len(matches) > 0
        upstream_match = [m for m in matches if m["position"] == "upstream"]
        assert any(m["theme"] == "semiconductor_compute" for m in upstream_match)

    def test_match_downstream_keyword(self):
        """
        验证：股票名称包含下游关键词时，能匹配到下游位置。
        比如"浪潮信息"包含"浪潮"（服务器下游），应该匹配。
        """
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        matches = match_stock_to_supply_chain(
            ts_code="000977.SZ",
            sector="",
            stock_name="浪潮信息",
            themes=themes,
        )
        assert len(matches) > 0
        downstream_match = [m for m in matches if m["position"] == "downstream"]
        assert any(m["theme"] == "semiconductor_compute" for m in downstream_match)

    def test_no_match_returns_empty(self):
        """
        验证：和供应链无关的股票返回空列表。
        """
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        matches = match_stock_to_supply_chain(
            ts_code="999999.SZ",
            sector="消费品",
            stock_name="某食品公司",
            themes=themes,
        )
        assert matches == []

    def test_match_both_upstream_and_downstream(self):
        """
        验证：一只股票可以同时匹配上游和下游。
        比如"埃斯顿"既做伺服（上游）也做整机（下游）。
        """
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        matches = match_stock_to_supply_chain(
            ts_code="002747.SZ",
            sector="",
            stock_name="埃斯顿",
            themes=themes,
        )
        positions = {m["position"] for m in matches}
        assert "upstream" in positions, "埃斯顿应该匹配到上游"
        assert "downstream" in positions, "埃斯顿应该匹配到下游"


# ============================================================
# 测试关键词反向匹配
# ============================================================

class TestFindSupplyChainKeywordCandidates:
    """测试 find_supply_chain_keyword_candidates 函数"""

    def test_returns_dict(self):
        """验证返回类型是 dict"""
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        result = find_supply_chain_keyword_candidates(themes, [])
        assert isinstance(result, dict)

    def test_finds_missing_upstream(self):
        """
        验证：当 watchlist 为空时，所有非通用词上游关键词都应被识别为潜在候选。
        """
        themes = ["semiconductor_compute"]
        result = find_supply_chain_keyword_candidates(themes, [])

        assert "semiconductor_compute" in result
        # 上游应该有候选
        assert len(result["semiconductor_compute"]["upstream"]) > 0
        # 应该包含"北方华创"
        assert "北方华创" in result["semiconductor_compute"]["upstream"]

    def test_finds_missing_downstream(self):
        """
        验证：当 watchlist 为空时，下游关键词也被识别为潜在候选。
        """
        themes = ["semiconductor_compute"]
        result = find_supply_chain_keyword_candidates(themes, [])

        assert "semiconductor_compute" in result
        assert len(result["semiconductor_compute"]["downstream"]) > 0
        assert "浪潮" in result["semiconductor_compute"]["downstream"]

    def test_excludes_generic_terms(self):
        """验证：通用词不会出现在候选里"""
        themes = list(SUPPLY_CHAIN_KEYWORDS.keys())
        result = find_supply_chain_keyword_candidates(themes, [])

        for theme_key, positions in result.items():
            for position in ("upstream", "downstream"):
                for kw in positions[position]:
                    assert kw not in GENERIC_TERMS, \
                        f"'{kw}' 是通用词，不应出现在候选里"

    def test_excludes_keywords_in_watchlist(self):
        """
        验证：已在 watchlist 中的关键词不会出现在候选里。
        比如"中际"在"中际旭创"里，不应出现。
        """
        themes = ["semiconductor_photonics"]
        watchlist = [
            {"ts_code": "300308.SZ", "name": "中际旭创", "sector": "semiconductor_photonics"},
            {"ts_code": "300502.SZ", "name": "新易盛", "sector": "semiconductor_photonics"},
        ]
        result = find_supply_chain_keyword_candidates(themes, watchlist)

        if "semiconductor_photonics" in result:
            all_kws = result["semiconductor_photonics"]["upstream"] + \
                      result["semiconductor_photonics"]["downstream"]
            # "新易盛"在 watchlist 里，"新易盛"关键词不应出现
            assert "新易盛" not in all_kws, "'新易盛'已在 watchlist，不应出现在候选里"

    def test_upstream_and_downstream_separated(self):
        """验证：上游和下游关键词分开存储"""
        themes = ["semiconductor_compute"]
        result = find_supply_chain_keyword_candidates(themes, [])

        assert "semiconductor_compute" in result
        assert "upstream" in result["semiconductor_compute"]
        assert "downstream" in result["semiconductor_compute"]
        assert isinstance(result["semiconductor_compute"]["upstream"], list)
        assert isinstance(result["semiconductor_compute"]["downstream"], list)


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
        assert "themes_scanned" in summary
        assert "existing_count" in summary
        assert "db_stock_count" in summary
        assert "new_candidates" in summary
        assert "keyword_candidates_upstream" in summary
        assert "keyword_candidates_downstream" in summary
        assert "dry_run" in summary
        assert "discovery_date" in summary

        assert summary["dry_run"] is True
        assert summary["themes_scanned"] == 5
        assert summary["existing_count"] > 0

        # 应该有上游和下游的潜在候选关键词
        assert summary["keyword_candidates_upstream"] > 0, "应该有上游潜在候选"
        assert summary["keyword_candidates_downstream"] > 0, "应该有下游潜在候选"
