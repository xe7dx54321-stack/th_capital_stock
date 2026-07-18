"""
dispatch_proposal.py 的单元测试

覆盖：
    - list_proposals: 列出提案（pending/approved/rejected）
    - approve_proposal: 批准单个（写 stock_pool + 更新状态）
    - reject_proposal: 拒绝单个（不写 stock_pool + 更新状态）
    - approve_all / reject_all: 批量操作
    - not_found / already_processed: 边界情况
    - dry_run: 预览模式不写入
    - write_to_stock_pool: stock_pool 写入字段正确性
    - render_proposals_table: 表格渲染
    - load_policy: 配置读取
"""

import json
import sqlite3
import sys
from pathlib import Path

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "08_scripts" / "lib"))

import pytest

# import 被测模块
import dispatch_proposal as dp


# ============================================================
# 测试夹具：内存数据库 + 表结构初始化
# ============================================================

def make_in_memory_db():
    """
    创建内存数据库，初始化 discovery_proposal 和 stock_pool 表。

    小白讲解：每个测试都用全新的内存数据库（不碰真实数据库文件），
    测试之间互不影响。
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE discovery_proposal (
            proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            name TEXT,
            market TEXT,
            sector TEXT,
            composite_score REAL,
            score_card_json TEXT,
            discovery_evidence_json TEXT,
            status TEXT DEFAULT 'pending_approval',
            approved_by TEXT,
            approved_at TEXT,
            reason TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(ticker)
        );
        CREATE TABLE stock_pool (
            pool_type TEXT,
            ts_code TEXT,
            sector TEXT,
            added_date TEXT,
            added_reason TEXT,
            score REAL,
            status TEXT
        );
    """)
    return conn


def insert_proposal(conn, ticker, name="测试股票", market="A",
                    sector="semiconductor_compute", composite_score=6.5,
                    score_card_json=None, discovery_evidence_json=None,
                    status="pending_approval"):
    """插入一条提案用于测试"""
    if score_card_json is None:
        score_card_json = json.dumps({
            "fundamental_quality": 7.0,
            "valuation_position": 5.5,
            "technical_momentum": 6.0,
            "theme_relevance": 7.5,
            "industry_position": 6.0,
            "composite_score": composite_score,
            "red_flags": [],
        })
    if discovery_evidence_json is None:
        discovery_evidence_json = json.dumps({
            "methods": ["theme_extension", "supply_chain"],
            "sources": ["概念板块：光模块"],
            "hit_methods": 2,
        })
    conn.execute(
        """
        INSERT INTO discovery_proposal
            (ticker, name, market, sector, composite_score,
             score_card_json, discovery_evidence_json, status, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticker, name, market, sector, composite_score,
         score_card_json, discovery_evidence_json, status, "测试推荐理由"),
    )
    conn.commit()


# ============================================================
# 常量测试
# ============================================================

class TestConstants:
    """测试模块常量定义是否正确"""

    def test_status_constants(self):
        """验证提案状态常量"""
        assert dp.STATUS_PENDING == "pending_approval"
        assert dp.STATUS_APPROVED == "approved"
        assert dp.STATUS_REJECTED == "rejected"

    def test_approved_pool_type(self):
        """验证批准入池的 pool_type 是 'candidate'"""
        assert dp.APPROVED_POOL_TYPE == "candidate"

    def test_default_approved_by(self):
        """验证默认批准人标识"""
        assert dp.DEFAULT_APPROVED_BY == "human_operator"


# ============================================================
# ensure_proposal_table 测试
# ============================================================

class TestEnsureProposalTable:
    """测试表存在性检查/创建"""

    def test_ensure_proposal_table_creates_when_missing(self):
        """如果表不存在，ensure_proposal_table 应该创建它"""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dp.ensure_proposal_table(conn)
        # 验证表已创建
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='discovery_proposal'"
        ).fetchone()
        assert row is not None
        conn.close()

    def test_ensure_proposal_table_idempotent(self):
        """如果表已存在，ensure_proposal_table 不应报错"""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        dp.ensure_proposal_table(conn)
        dp.ensure_proposal_table(conn)  # 再调用一次不应该报错
        conn.close()


# ============================================================
# relation_exists 测试
# ============================================================

class TestRelationExists:
    """测试表/视图存在性检查"""

    def test_relation_exists_for_table(self):
        """存在的表返回 True"""
        conn = make_in_memory_db()
        assert dp.relation_exists(conn, "discovery_proposal") is True
        assert dp.relation_exists(conn, "stock_pool") is True
        conn.close()

    def test_relation_not_exists(self):
        """不存在的表返回 False"""
        conn = make_in_memory_db()
        assert dp.relation_exists(conn, "nonexistent_table") is False
        conn.close()


# ============================================================
# list_proposals 测试
# ============================================================

class TestListProposals:
    """测试列出提案"""

    def test_list_empty_proposals(self):
        """空表返回空列表"""
        conn = make_in_memory_db()
        result = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert result == []
        conn.close()

    def test_list_pending_proposals(self):
        """列出 pending_approval 提案"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", composite_score=7.5)
        insert_proposal(conn, "688041.SH", composite_score=6.0)

        result = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert len(result) == 2
        # 应按 composite_score 降序排序
        assert result[0]["ticker"] == "300308.SZ"
        assert result[0]["composite_score"] == 7.5
        assert result[1]["ticker"] == "688041.SH"
        conn.close()

    def test_list_only_pending_status(self):
        """只返回指定状态的提案"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", status="pending_approval")
        insert_proposal(conn, "688041.SH", status="approved")
        insert_proposal(conn, "688256.SH", status="rejected")

        pending = dp.list_proposals(conn, dp.STATUS_PENDING)
        approved = dp.list_proposals(conn, dp.STATUS_APPROVED)
        rejected = dp.list_proposals(conn, dp.STATUS_REJECTED)

        assert len(pending) == 1
        assert pending[0]["ticker"] == "300308.SZ"
        assert len(approved) == 1
        assert approved[0]["ticker"] == "688041.SH"
        assert len(rejected) == 1
        assert rejected[0]["ticker"] == "688256.SH"
        conn.close()

    def test_list_orders_null_score_last(self):
        """composite_score 为 NULL 的排到最后"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", composite_score=5.0)
        insert_proposal(conn, "688041.SH", composite_score=None)

        result = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert len(result) == 2
        # 有分数的在前，NULL 在后
        assert result[0]["ticker"] == "300308.SZ"
        assert result[1]["ticker"] == "688041.SH"
        conn.close()


# ============================================================
# approve_proposal 测试
# ============================================================

class TestApproveProposal:
    """测试批准单个提案"""

    def test_approve_writes_to_stock_pool(self):
        """批准后应写入 stock_pool 表"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", composite_score=7.5, sector="semiconductor_photonics")

        result = dp.approve_proposal(conn, "300308.SZ", approved_by="lisha", reason="测试批准")

        assert result["action"] == "approved"
        assert result["ticker"] == "300308.SZ"
        assert result["dry_run"] is False
        assert result["proposal_id"] is not None

        # 验证 stock_pool 已写入
        pool_rows = conn.execute("SELECT * FROM stock_pool WHERE ts_code=?", ("300308.SZ",)).fetchall()
        assert len(pool_rows) == 1
        pool = dict(pool_rows[0])
        assert pool["pool_type"] == "candidate"
        assert pool["ts_code"] == "300308.SZ"
        assert pool["sector"] == "semiconductor_photonics"
        assert pool["score"] == 7.5
        assert pool["status"] == "active"
        assert "approved from discovery_proposal" in pool["added_reason"]
        assert "lisha" in pool["added_reason"]
        conn.close()

    def test_approve_updates_proposal_status(self):
        """批准后 proposal 状态应更新为 approved"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")

        dp.approve_proposal(conn, "300308.SZ", approved_by="lisha", reason="OK")

        row = conn.execute(
            "SELECT status, approved_by, reason FROM discovery_proposal WHERE ticker=?",
            ("300308.SZ",),
        ).fetchone()
        assert row["status"] == "approved"
        assert row["approved_by"] == "lisha"
        assert "OK" in row["reason"] or row["reason"] == "OK"
        conn.close()

    def test_approve_not_found(self):
        """批准不存在的 ticker 返回 not_found"""
        conn = make_in_memory_db()
        result = dp.approve_proposal(conn, "999999.SZ")
        assert result["action"] == "not_found"
        assert "未找到" in result["message"]
        conn.close()

    def test_approve_already_processed(self):
        """重复批准已处理的提案返回 already_processed"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", status="approved")

        result = dp.approve_proposal(conn, "300308.SZ")
        assert result["action"] == "already_processed"
        assert "已处理过" in result["message"]
        conn.close()

    def test_approve_dry_run_does_not_write(self):
        """dry-run 模式不应写入数据库"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", composite_score=7.0)

        result = dp.approve_proposal(conn, "300308.SZ", dry_run=True)

        assert result["action"] == "approved"
        assert result["dry_run"] is True
        assert "dry-run" in result["message"]

        # 验证 stock_pool 没写入
        pool_count = conn.execute("SELECT COUNT(*) FROM stock_pool").fetchone()[0]
        assert pool_count == 0
        # 验证 proposal 状态没变
        row = conn.execute(
            "SELECT status FROM discovery_proposal WHERE ticker=?", ("300308.SZ",)
        ).fetchone()
        assert row["status"] == "pending_approval"
        conn.close()

    def test_approve_sets_approved_at_timestamp(self):
        """批准后应记录 approved_at 时间戳"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")

        dp.approve_proposal(conn, "300308.SZ")

        row = conn.execute(
            "SELECT approved_at FROM discovery_proposal WHERE ticker=?", ("300308.SZ",)
        ).fetchone()
        assert row["approved_at"] is not None
        assert len(row["approved_at"]) > 0
        conn.close()


# ============================================================
# reject_proposal 测试
# ============================================================

class TestRejectProposal:
    """测试拒绝单个提案"""

    def test_reject_does_not_write_stock_pool(self):
        """拒绝不应写入 stock_pool"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")

        result = dp.reject_proposal(conn, "300308.SZ", reason="估值过高")

        assert result["action"] == "rejected"
        assert result["dry_run"] is False

        pool_count = conn.execute("SELECT COUNT(*) FROM stock_pool").fetchone()[0]
        assert pool_count == 0
        conn.close()

    def test_reject_updates_status(self):
        """拒绝后 proposal 状态应更新为 rejected"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")

        dp.reject_proposal(conn, "300308.SZ", approved_by="lisha", reason="估值过高")

        row = conn.execute(
            "SELECT status, approved_by, reason FROM discovery_proposal WHERE ticker=?",
            ("300308.SZ",),
        ).fetchone()
        assert row["status"] == "rejected"
        assert row["approved_by"] == "lisha"
        assert "估值过高" in row["reason"]
        conn.close()

    def test_reject_not_found(self):
        """拒绝不存在的 ticker 返回 not_found"""
        conn = make_in_memory_db()
        result = dp.reject_proposal(conn, "999999.SZ")
        assert result["action"] == "not_found"
        conn.close()

    def test_reject_already_processed(self):
        """重复拒绝已处理的提案返回 already_processed"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", status="rejected")

        result = dp.reject_proposal(conn, "300308.SZ")
        assert result["action"] == "already_processed"
        conn.close()

    def test_reject_dry_run(self):
        """dry-run 模式不写入"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")

        result = dp.reject_proposal(conn, "300308.SZ", dry_run=True)

        assert result["action"] == "rejected"
        assert result["dry_run"] is True

        row = conn.execute(
            "SELECT status FROM discovery_proposal WHERE ticker=?", ("300308.SZ",)
        ).fetchone()
        assert row["status"] == "pending_approval"
        conn.close()


# ============================================================
# approve_all / reject_all 测试
# ============================================================

class TestBatchOperations:
    """测试批量批准/拒绝"""

    def test_approve_all(self):
        """批准所有 pending 提案"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", composite_score=7.5)
        insert_proposal(conn, "688041.SH", composite_score=6.0)
        insert_proposal(conn, "688256.SH", composite_score=5.5)

        results = dp.approve_all(conn, approved_by="lisha")

        assert len(results) == 3
        assert all(r["action"] == "approved" for r in results)

        # 验证 stock_pool 写入 3 条
        pool_count = conn.execute("SELECT COUNT(*) FROM stock_pool").fetchone()[0]
        assert pool_count == 3

        # 验证所有 proposal 状态都是 approved
        approved_count = conn.execute(
            "SELECT COUNT(*) FROM discovery_proposal WHERE status='approved'"
        ).fetchone()[0]
        assert approved_count == 3
        conn.close()

    def test_reject_all(self):
        """拒绝所有 pending 提案"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")
        insert_proposal(conn, "688041.SH")

        results = dp.reject_all(conn, reason="本轮全部放弃")

        assert len(results) == 2
        assert all(r["action"] == "rejected" for r in results)

        # 验证 stock_pool 没写入
        pool_count = conn.execute("SELECT COUNT(*) FROM stock_pool").fetchone()[0]
        assert pool_count == 0

        rejected_count = conn.execute(
            "SELECT COUNT(*) FROM discovery_proposal WHERE status='rejected'"
        ).fetchone()[0]
        assert rejected_count == 2
        conn.close()

    def test_approve_all_empty(self):
        """没有 pending 提案时 approve_all 返回空列表"""
        conn = make_in_memory_db()
        results = dp.approve_all(conn)
        assert results == []
        conn.close()

    def test_approve_all_skips_non_pending(self):
        """approve_all 只处理 pending 的，跳过已处理的"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ", status="pending_approval")
        insert_proposal(conn, "688041.SH", status="approved")
        insert_proposal(conn, "688256.SH", status="rejected")

        results = dp.approve_all(conn)
        assert len(results) == 1
        assert results[0]["ticker"] == "300308.SZ"
        conn.close()

    def test_approve_all_dry_run(self):
        """approve_all 的 dry-run 模式"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")
        insert_proposal(conn, "688041.SH")

        results = dp.approve_all(conn, dry_run=True)

        assert len(results) == 2
        assert all(r["dry_run"] is True for r in results)

        # 验证没写入
        pool_count = conn.execute("SELECT COUNT(*) FROM stock_pool").fetchone()[0]
        assert pool_count == 0
        pending_count = conn.execute(
            "SELECT COUNT(*) FROM discovery_proposal WHERE status='pending_approval'"
        ).fetchone()[0]
        assert pending_count == 2
        conn.close()


# ============================================================
# write_to_stock_pool 测试
# ============================================================

class TestWriteToStockPool:
    """测试写 stock_pool 的字段正确性"""

    def test_write_to_stock_pool_fields(self):
        """验证 stock_pool 写入的所有字段"""
        conn = make_in_memory_db()
        proposal = {
            "proposal_id": 42,
            "ticker": "300308.SZ",
            "name": "中际旭创",
            "market": "A",
            "sector": "semiconductor_photonics",
            "composite_score": 7.8,
        }

        dp.write_to_stock_pool(conn, proposal, approved_by="lisha", event_time="2026-07-15 10:00:00")

        row = conn.execute("SELECT * FROM stock_pool WHERE ts_code=?", ("300308.SZ",)).fetchone()
        pool = dict(row)
        assert pool["pool_type"] == "candidate"
        assert pool["ts_code"] == "300308.SZ"
        assert pool["sector"] == "semiconductor_photonics"
        assert pool["added_date"] == "2026-07-15 10:00:00"
        assert pool["score"] == 7.8
        assert pool["status"] == "active"
        assert "proposal_id=42" in pool["added_reason"]
        assert "approved_by=lisha" in pool["added_reason"]
        conn.close()

    def test_write_to_stock_pool_null_score(self):
        """composite_score 为 None 时 stock_pool.score 也为 None"""
        conn = make_in_memory_db()
        proposal = {
            "proposal_id": 1,
            "ticker": "300308.SZ",
            "sector": "test",
            "composite_score": None,
        }
        dp.write_to_stock_pool(conn, proposal, "test", "2026-07-15")
        row = conn.execute("SELECT score FROM stock_pool WHERE ts_code=?", ("300308.SZ",)).fetchone()
        assert row["score"] is None
        conn.close()


# ============================================================
# load_policy 测试
# ============================================================

class TestLoadPolicy:
    """测试读取策略配置"""

    def test_load_policy_returns_defaults_when_file_missing(self, monkeypatch):
        """策略文件不存在时返回默认值"""
        monkeypatch.setattr(dp, "POLICY_PATH", Path("/nonexistent/path/policy.json"))
        policy = dp.load_policy()
        assert policy["require_human_approval_before_pool"] is True
        assert policy["mode"] == "development"
        assert policy["min_composite_score_for_proposal"] == 6.0

    def test_load_policy_require_human_default_true(self):
        """验证 require_human_approval_before_pool 默认是 True（硬约束）"""
        # 即使文件读不到，默认值也应该是 True
        policy = dp.load_policy()
        assert policy["require_human_approval_before_pool"] is True


# ============================================================
# render_proposals_table 测试
# ============================================================

class TestRenderProposalsTable:
    """测试表格渲染（只验证不报错）"""

    def test_render_empty_list(self, capsys):
        """空列表渲染不报错"""
        dp.render_proposals_table([], "待批准")
        captured = capsys.readouterr()
        assert "没有" in captured.out
        assert "待批准" in captured.out

    def test_render_non_empty_list(self, capsys):
        """非空列表渲染不报错"""
        proposals = [{
            "proposal_id": 1,
            "ticker": "300308.SZ",
            "name": "中际旭创",
            "market": "A",
            "sector": "semiconductor_photonics",
            "composite_score": 7.5,
            "score_card_json": json.dumps({
                "fundamental_quality": 7.0,
                "valuation_position": 5.5,
                "technical_momentum": 6.0,
                "theme_relevance": 7.5,
                "industry_position": 6.0,
                "red_flags": ["注意: 估值偏高"],
            }),
            "discovery_evidence_json": json.dumps({
                "methods": ["theme_extension"],
                "hit_methods": 1,
            }),
            "reason": "测试理由",
            "created_at": "2026-07-15 10:00:00",
        }]
        dp.render_proposals_table(proposals, "待批准")
        captured = capsys.readouterr()
        assert "300308.SZ" in captured.out
        assert "中际旭创" in captured.out
        assert "fundamental_quality" in captured.out

    def test_render_handles_invalid_json(self, capsys):
        """无效 JSON 不应导致崩溃"""
        proposals = [{
            "proposal_id": 1,
            "ticker": "300308.SZ",
            "name": "测试",
            "market": "A",
            "sector": "test",
            "composite_score": 5.0,
            "score_card_json": "invalid json{",
            "discovery_evidence_json": "invalid json{",
            "reason": "",
            "created_at": "2026-07-15",
        }]
        dp.render_proposals_table(proposals, "待批准")
        captured = capsys.readouterr()
        assert "300308.SZ" in captured.out


# ============================================================
# 集成测试：完整流程
# ============================================================

class TestIntegrationFlow:
    """集成测试：模拟完整的人工批准流程"""

    def test_full_flow_list_approve_verify(self):
        """完整流程：插入提案 → 列出 → 批准 → 验证入池"""
        conn = make_in_memory_db()

        # 1. 插入 3 条提案
        insert_proposal(conn, "300308.SZ", composite_score=7.5, sector="semiconductor_photonics")
        insert_proposal(conn, "688041.SH", composite_score=6.0, sector="semiconductor_compute")
        insert_proposal(conn, "688256.SH", composite_score=4.5, sector="semiconductor_compute")

        # 2. 列出 pending，应有 3 条
        pending = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert len(pending) == 3

        # 3. 批准 300308.SZ
        result = dp.approve_proposal(conn, "300308.SZ", approved_by="lisha", reason="优质标的")
        assert result["action"] == "approved"

        # 4. 拒绝 688256.SH
        result = dp.reject_proposal(conn, "688256.SH", reason="评分偏低")
        assert result["action"] == "rejected"

        # 5. 验证 pending 只剩 1 条
        pending = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert len(pending) == 1
        assert pending[0]["ticker"] == "688041.SH"

        # 6. 验证 stock_pool 只有 1 条（被批准的）
        pool_rows = conn.execute("SELECT * FROM stock_pool").fetchall()
        assert len(pool_rows) == 1
        assert dict(pool_rows[0])["ts_code"] == "300308.SZ"

        # 7. 验证 approved/rejected 状态
        approved = dp.list_proposals(conn, dp.STATUS_APPROVED)
        rejected = dp.list_proposals(conn, dp.STATUS_REJECTED)
        assert len(approved) == 1
        assert len(rejected) == 1
        conn.close()

    def test_full_flow_approve_all_then_no_pending(self):
        """批准所有后 pending 应为空"""
        conn = make_in_memory_db()
        insert_proposal(conn, "300308.SZ")
        insert_proposal(conn, "688041.SH")

        dp.approve_all(conn, approved_by="admin")

        pending = dp.list_proposals(conn, dp.STATUS_PENDING)
        assert len(pending) == 0
        approved = dp.list_proposals(conn, dp.STATUS_APPROVED)
        assert len(approved) == 2
        conn.close()
