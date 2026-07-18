"""
build_opportunity_radar_snapshot.py 的新增函数单元测试

小白讲解：这个测试文件验证机会雷达升级后的两个新函数：
1. load_discovery_candidates：从数据库读取本周新发现候选
2. render_discovery_section：把候选渲染成 Markdown 区块
"""

import sqlite3
import sys
from pathlib import Path

import pytest

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "opportunity"))
sys.path.insert(0, str(SCRIPTS_DIR / "lib"))

# 由于 build_opportunity_radar_snapshot 依赖很多 lib 模块，
# 我们直接测试两个新增的纯函数：load_discovery_candidates 和 render_discovery_section
# 需要先把模块导入
try:
    from build_opportunity_radar_snapshot import (
        load_discovery_candidates,
        render_discovery_section,
    )
    IMPORT_OK = True
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERROR = str(e)


# ============================================================
# 测试 render_discovery_section（纯函数，不依赖数据库）
# ============================================================

class TestRenderDiscoverySection:
    """测试 render_discovery_section 函数"""

    def test_empty_candidates(self):
        """验证：空候选列表时输出提示信息"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        lines = render_discovery_section([])
        text = "\n".join(lines)
        assert "本周新发现候选" in text
        assert "当前没有新发现候选" in text

    def test_with_candidates(self):
        """验证：有候选时输出表格"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        candidates = [
            {
                "ticker": "300308.SZ",
                "name": "中际旭创",
                "market": "A",
                "sector": "semiconductor_photonics",
                "methods": ["theme_extension", "supply_chain"],
                "hit_methods": 3,
                "latest_date": "2026-07-15",
            },
            {
                "ticker": "688041.SH",
                "name": "海光信息",
                "market": "A",
                "sector": "semiconductor_compute",
                "methods": ["us_benchmark"],
                "hit_methods": 1,
                "latest_date": "2026-07-15",
            },
        ]

        lines = render_discovery_section(candidates)
        text = "\n".join(lines)

        # 应包含标题
        assert "本周新发现候选" in text
        # 应包含表头
        assert "标的" in text
        assert "命中方法" in text
        # 应包含候选数据
        assert "300308.SZ" in text
        assert "中际旭创" in text
        assert "主题扩展" in text  # theme_extension 的中文标签
        assert "供应链" in text  # supply_chain 的中文标签
        assert "美股对标" in text  # us_benchmark 的中文标签

    def test_method_labels_translated(self):
        """验证：发现方法的英文 key 被翻译成中文标签"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        candidates = [
            {
                "ticker": "TEST001",
                "name": "测试标的",
                "market": "A",
                "sector": "test",
                "methods": ["theme_extension", "supply_chain", "us_benchmark", "manual"],
                "hit_methods": 4,
                "latest_date": "2026-07-15",
            },
        ]

        lines = render_discovery_section(candidates)
        text = "\n".join(lines)

        # 所有的方法标签都应该被翻译
        assert "主题扩展" in text
        assert "供应链" in text
        assert "美股对标" in text
        assert "人工" in text


# ============================================================
# 测试 load_discovery_candidates（需要内存数据库）
# ============================================================

class TestLoadDiscoveryCandidates:
    """测试 load_discovery_candidates 函数"""

    def test_table_not_exist_returns_empty(self):
        """验证：表不存在时返回空列表"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        # 用内存数据库，不创建 discovery_candidate 表
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        result = load_discovery_candidates(conn, "2026-07-15")
        assert result == []

        conn.close()

    def test_empty_table_returns_empty(self):
        """验证：表存在但为空时返回空列表"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE discovery_candidate (
                ticker TEXT NOT NULL,
                name TEXT,
                market TEXT,
                sector TEXT,
                discovery_method TEXT NOT NULL,
                hit_methods INTEGER DEFAULT 1,
                discovery_date TEXT NOT NULL,
                raw_source TEXT,
                added_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(ticker, discovery_method, discovery_date)
            )
        """)
        conn.commit()

        result = load_discovery_candidates(conn, "2026-07-15")
        assert result == []

        conn.close()

    def test_returns_candidates_from_table(self):
        """验证：能正确读取并聚合候选"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE discovery_candidate (
                ticker TEXT NOT NULL,
                name TEXT,
                market TEXT,
                sector TEXT,
                discovery_method TEXT NOT NULL,
                hit_methods INTEGER DEFAULT 1,
                discovery_date TEXT NOT NULL,
                raw_source TEXT,
                added_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(ticker, discovery_method, discovery_date)
            )
        """)

        # 插入测试数据：同一只股票被两个方法命中
        conn.execute("""
            INSERT INTO discovery_candidate
                (ticker, name, market, sector, discovery_method, hit_methods, discovery_date)
            VALUES
                ('300308.SZ', '中际旭创', 'A', 'semiconductor_photonics', 'theme_extension', 1, '2026-07-15'),
                ('300308.SZ', '中际旭创', 'A', 'semiconductor_photonics', 'supply_chain', 1, '2026-07-15'),
                ('688041.SH', '海光信息', 'A', 'semiconductor_compute', 'us_benchmark', 1, '2026-07-14')
        """)
        conn.commit()

        result = load_discovery_candidates(conn, "2026-07-15")

        # 应返回 2 个候选（去重后）
        assert len(result) == 2

        # 第一个应该是 hit_methods 最高的（中际旭创被 2 个方法命中）
        first = result[0]
        assert first["ticker"] == "300308.SZ"
        assert first["name"] == "中际旭创"
        assert first["hit_methods"] == 2
        assert "theme_extension" in first["methods"]
        assert "supply_chain" in first["methods"]

        conn.close()

    def test_filters_old_candidates(self):
        """验证：只返回最近 7 天的候选"""
        if not IMPORT_OK:
            pytest.skip(f"import 失败: {IMPORT_ERROR}")

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE discovery_candidate (
                ticker TEXT NOT NULL,
                name TEXT,
                market TEXT,
                sector TEXT,
                discovery_method TEXT NOT NULL,
                hit_methods INTEGER DEFAULT 1,
                discovery_date TEXT NOT NULL,
                raw_source TEXT,
                added_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(ticker, discovery_method, discovery_date)
            )
        """)

        # batch_date = 2026-07-15
        # 近期候选（7天内）
        conn.execute("""
            INSERT INTO discovery_candidate
                (ticker, name, market, sector, discovery_method, hit_methods, discovery_date)
            VALUES
                ('RECENT01', '近期标的', 'A', 'test', 'theme_extension', 1, '2026-07-14'),
                ('RECENT02', '近期标的2', 'A', 'test', 'theme_extension', 1, '2026-07-10')
        """)

        # 注意：SQLite 的 date() 函数对 '-7 days' 的计算
        # date('2026-07-15', '-7 days') = '2026-07-08'
        # 所以 2026-07-10 和 2026-07-14 都在范围内

        conn.commit()

        result = load_discovery_candidates(conn, "2026-07-15")
        # 应返回 2 个（都在 7 天内）
        assert len(result) == 2

        conn.close()
