"""
阶段 12：统一记忆与阶段抽取 —— Python 端测试
=================================================
覆盖 Master Plan §阶段 12 的 7 条验收 + 4 层记忆类型

运行方式：
    python -m pytest tests/test_unified_memory_phase12.py -v
或
    python tests/test_unified_memory_phase12.py
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# 保证 smr_app 包可被 import
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_LIB = PROJECT_ROOT / "08_scripts" / "lib"
for p in (str(PROJECT_ROOT), str(SCRIPTS_LIB)):
    if p not in sys.path:
        sys.path.insert(0, p)

from smr_app.adapters.memory import (
    ALLOWED_TRANSITIONS,
    create_memory_candidate,
    current_approved,
    delete_session_memories,
    edit_memory_candidate,
    ensure_memory_schema,
    flag_conflicting_memories,
    get_memory,
    list_conflicting_candidates,
    record_retrieval,
    review_memory,
    search_memories_with_hit_tracking,
)


def _make_empty_db() -> sqlite3.Connection:
    """
    函数说明（小白友好）：
    -----------------------
    建一个临时在内存里的 SQLite 数据库，跑完测试自动销毁，不会污染真实数据库。

    参数：无
    返回值：sqlite3.Connection —— 内存数据库连接
    异常处理：无（sqlite3 内存库不会失败）
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    ensure_memory_schema(conn)
    return conn


class TestPhase12_Acceptance1_CandidateNotUsedAsFact(unittest.TestCase):
    """
    验收 1：candidate 不作为已确认事实使用
    """

    def test_candidate_is_not_returned_by_current_approved(self):
        """候选记忆不应该被 current_approved() 当作已确认事实返回"""
        conn = _make_empty_db()

        # 先建一个 candidate 状态的记忆
        create_memory_candidate(
            conn,
            entity_type="stock",
            entity_id="002396.SZ",
            memory_type="valuation",
            content={"pe_ttm": 198, "remark": "偏高"},
            evidence_links=[
                {"evidence_id": "ev_test_001", "relation": "supports"}
            ],
            confidence=0.7,
        )

        # 未审核前：current_approved 应该返回 None（没有 approved 的）
        fact = current_approved(conn, "stock", "002396.SZ", "valuation")
        self.assertIsNone(fact, "candidate 状态不能被当作已确认事实！")

    def test_approved_is_returned_after_review(self):
        """用户 approve 后，current_approved 才能拿到"""
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn,
            entity_type="stock",
            entity_id="300474.SZ",
            memory_type="thesis",
            content={"driver": "算力需求+自主可控"},
            evidence_links=[
                {"evidence_id": "ev_test_002", "relation": "supports"}
            ],
        )

        review_memory(conn, mem["memory_id"], "approve", "tester", "确认论点有效")

        fact = current_approved(conn, "stock", "300474.SZ", "thesis")
        self.assertIsNotNone(fact, "approve 后应该能拿到已确认事实")
        self.assertEqual(fact["status"], "approved")


class TestPhase12_Acceptance2_UserCanCRUD(unittest.TestCase):
    """
    验收 2：用户可确认、编辑、拒绝、归档
    """

    def test_approve_reject_archive_workflow(self):
        """三条基本审核动作都必须按状态机允许的方式工作"""
        conn = _make_empty_db()

        # 1) approve 流程
        m1 = create_memory_candidate(
            conn, entity_type="stock", entity_id="688008.SH", memory_type="risk",
            content={"risk": "行业竞争激烈"},
            evidence_links=[{"evidence_id": "ev_r1", "relation": "supports"}],
        )
        r1 = review_memory(conn, m1["memory_id"], "approve", "u1", "确认")
        self.assertEqual(r1["status"], "approved")

        # 2) reject 流程
        m2 = create_memory_candidate(
            conn, entity_type="stock", entity_id="688008.SH", memory_type="risk",
            content={"risk": "马上退市（谣言）"},
            evidence_links=[{"evidence_id": "ev_r2", "relation": "supports"}],
        )
        r2 = review_memory(conn, m2["memory_id"], "reject", "u1", "与事实不符")
        self.assertEqual(r2["status"], "rejected")

        # 3) archive 流程（已 approved 也能归档）
        r3 = review_memory(conn, m1["memory_id"], "archive", "u1", "过时了")
        self.assertEqual(r3["status"], "archived")

    def test_edit_candidate_before_approve(self):
        """
        用户可以在 approve 之前编辑 candidate 的内容
        （比如用户觉得 AI 提取的事实不够准确，改一下再确认）
        """
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn, entity_type="stock", entity_id="300308.SZ", memory_type="fundamental",
            content={"revenue_yoy": 0.30, "net_profit_yoy": 0.45},
            evidence_links=[{"evidence_id": "ev_e1", "relation": "supports"}],
        )

        # 编辑：把净利同比从 0.45 改成 0.52，加个备注
        edited = edit_memory_candidate(
            conn,
            memory_id=mem["memory_id"],
            content={"revenue_yoy": 0.30, "net_profit_yoy": 0.52, "remark": "2025Q1 快报"},
            evidence_links=mem["evidence_links"],
            editor="tester",
            edit_reason="Q1 快报已出，修正净利同比",
        )

        self.assertEqual(edited["content"]["net_profit_yoy"], 0.52, "编辑后内容必须更新")
        self.assertEqual(edited["content"]["remark"], "2025Q1 快报")
        # 必须保留编辑痕迹（field_diff 或 review_log 里）
        self.assertGreater(len(edited["review_log"]), 0, "编辑操作必须留下审核日志")


class TestPhase12_Acceptance3_TagsProjectHits(unittest.TestCase):
    """
    验收 3：支持标签、项目、命中次数和最近命中
    """

    def test_memory_supports_tags_and_project(self):
        """一条记忆可以带多个标签 + 所属项目 ID"""
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn, entity_type="stock", entity_id="300474.SZ", memory_type="thesis",
            content={"driver": "GPU国产替代"},
            evidence_links=[{"evidence_id": "ev_t1", "relation": "supports"}],
            confidence=0.9,
            # 新增字段：标签 + 项目
            tags=["GPU", "国产替代", "算力"],
            project_id="proj_supernode_2026",
        )

        got = get_memory(conn, mem["memory_id"])
        self.assertEqual(got["tags"], ["GPU", "国产替代", "算力"], "标签必须正确存取")
        self.assertEqual(got["project_id"], "proj_supernode_2026", "项目 ID 必须正确存取")

    def test_hit_count_and_last_hit_tracking(self):
        """每次检索命中，hit_count +1，last_hit_at 更新"""
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn, entity_type="stock", entity_id="300474.SZ", memory_type="valuation",
            content={"pe_ttm": 80, "remark": "历史高位"},
            evidence_links=[{"evidence_id": "ev_h1", "relation": "supports"}],
        )
        review_memory(conn, mem["memory_id"], "approve", "u1", "确认")

        # 初始状态：命中次数=0，最近命中=None
        fresh = get_memory(conn, mem["memory_id"])
        self.assertEqual(fresh["hit_count"], 0, "新建记忆的命中次数必须=0")
        self.assertIsNone(fresh["last_hit_at"], "新建记忆的最近命中必须=None")

        # 模拟 3 次检索命中
        for i in range(3):
            search_memories_with_hit_tracking(
                conn,
                entity_type="stock",
                entity_id="300474.SZ",
                memory_type="valuation",
                retrieval_reason="研究 300474 估值参考历史",
                retrieval_context={"workflow": "deep_research_v3", "ticker": "300474.SZ"},
            )

        after = get_memory(conn, mem["memory_id"])
        self.assertEqual(after["hit_count"], 3, "3 次检索后命中次数应该=3")
        self.assertIsNotNone(after["last_hit_at"], "最近命中时间必须被更新")


class TestPhase12_Acceptance4_RetrievalAuditTrail(unittest.TestCase):
    """
    验收 4：记忆检索记录为什么命中、如何使用
    """

    def test_retrieval_log_records_why_and_how(self):
        """每次命中记忆，都要写一条 retrieval_log，包含"为什么命中 + 如何使用"字段"""
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn, entity_type="stock", entity_id="300474.SZ", memory_type="thesis",
            content={"driver": "国产算力"},
            evidence_links=[{"evidence_id": "ev_l1", "relation": "supports"}],
        )
        review_memory(conn, mem["memory_id"], "approve", "u1", "ok")

        # 手动写一次 retrieval 记录（验收 4 核心）
        record_retrieval(
            conn,
            memory_id=mem["memory_id"],
            retrieval_reason="300474 与 688256 同属 GPU 赛道，引用同行业逻辑",
            retrieval_usage="作为行业比较段的论点参考，写入报告 §2.2",
            retrieval_context={
                "workflow": "swing_compare_v2",
                "source_ticker": "688256.SH",
                "target_ticker": "300474.SZ",
            },
            consumer="research_agent_v3",
        )

        # 查数据库里的 retrieval_log
        rows = conn.execute(
            "SELECT * FROM memory_retrieval_log WHERE memory_id=? ORDER BY retrieval_id",
            (mem["memory_id"],),
        ).fetchall()

        self.assertEqual(len(rows), 1, "必须有 1 条检索记录")
        row = dict(rows[0])
        self.assertIn("GPU", row["retrieval_reason"], "必须记录为什么命中（原因）")
        self.assertIn("§2.2", row["retrieval_usage"], "必须记录如何使用（用途）")
        self.assertIn("688256.SH", row["retrieval_context_json"], "必须记录上下文（JSON）")
        self.assertEqual(row["consumer"], "research_agent_v3", "必须记录谁用的")


class TestPhase12_Acceptance5_ConflictingMemoryCoexist(unittest.TestCase):
    """
    验收 5：矛盾记忆并存并进入审核
    """

    def test_two_contradictory_candidates_coexist_and_flagged(self):
        """同一只股票同一个 memory_type 下，两个内容相反的 candidate 应该：
        1) 两者并存（不会自动删一个）
        2) 被自动打上 conflict 标记
        3) 出现在 list_conflicting_candidates() 里等待人工审核
        """
        conn = _make_empty_db()

        # 候选 A：说"增速 > 50%"
        ca = create_memory_candidate(
            conn, entity_type="stock", entity_id="688256.SH", memory_type="fundamental",
            content={"growth_driver": "AI 服务器需求旺盛，增速>50%"},
            evidence_links=[{"evidence_id": "ev_c_a", "relation": "supports"}],
            confidence=0.8,
            tags=["看多"],
        )

        # 候选 B：说"增速 < 20%"（明显相反）
        cb = create_memory_candidate(
            conn, entity_type="stock", entity_id="688256.SH", memory_type="fundamental",
            content={"growth_driver": "下游云厂砍单，增速<20%"},
            evidence_links=[{"evidence_id": "ev_c_b", "relation": "supports"}],
            confidence=0.7,
            tags=["看空"],
        )

        # 1) 两者都存在（没被自动删）
        self.assertIsNotNone(get_memory(conn, ca["memory_id"]))
        self.assertIsNotNone(get_memory(conn, cb["memory_id"]))

        # 2) 调用 flag_conflicting_memories 后，两条都被标成需要审核
        conflicts_flagged = flag_conflicting_memories(
            conn, entity_type="stock", entity_id="688256.SH", memory_type="fundamental"
        )
        self.assertGreaterEqual(len(conflicts_flagged), 2, "两条都应该被标记为冲突")

        # 3) list_conflicting_candidates 必须能列出这两条
        pending = list_conflicting_candidates(conn)
        ids = {m["memory_id"] for m in pending}
        self.assertIn(ca["memory_id"], ids, "候选 A 必须出现在冲突审核列表")
        self.assertIn(cb["memory_id"], ids, "候选 B 必须出现在冲突审核列表")

        # 状态：conflict 后再 approve 时需要审核人选择一条
        # （不强制，留给人判断；但两条都保持 candidate + conflict_flag）
        for mem_id in (ca["memory_id"], cb["memory_id"]):
            self.assertTrue(get_memory(conn, mem_id)["conflict_flag"],
                            f"{mem_id} 冲突标记应该=True")


class TestPhase12_Acceptance6_SessionDeleteSafety(unittest.TestCase):
    """
    验收 6：删除会话不误删正式研究记忆
    """

    def test_delete_session_only_removes_session_working_memory(self):
        """
        会话工作记忆（memory_type='session_working' + 绑定 session_id）删除时，
        不应该影响同实体下已 approved 的研究事实记忆。
        """
        conn = _make_empty_db()
        session_id = "sess_delete_demo_001"

        # 1) 先建一条正式的 approved 研究记忆（没有 session_id 绑定）
        fm = create_memory_candidate(
            conn, entity_type="stock", entity_id="300308.SZ", memory_type="valuation",
            content={"pe_ttm": 30, "remark": "合理估值"},
            evidence_links=[{"evidence_id": "ev_safe1", "relation": "supports"}],
        )
        review_memory(conn, fm["memory_id"], "approve", "u1", "确认")

        # 2) 建 3 条会话工作记忆（绑定 session_id，memory_type='session_working'）
        session_mem_ids = []
        for i in range(3):
            sm = create_memory_candidate(
                conn, entity_type="session", entity_id=session_id,
                memory_type="session_working",
                content={"round": i, "question": f"第{i}轮用户问题草稿"},
                evidence_links=[],  # 会话记忆不强制证据
                session_id=session_id,
            )
            session_mem_ids.append(sm["memory_id"])

        # 3) 还建一条别人的会话记忆（另一个 session_id），验证不误删
        other_session_mem = create_memory_candidate(
            conn, entity_type="session", entity_id="sess_other",
            memory_type="session_working",
            content={"round": 0},
            evidence_links=[],
            session_id="sess_other",
        )

        # 执行删除会话
        deleted = delete_session_memories(conn, session_id=session_id)
        self.assertEqual(deleted, 3, "应该正好删除当前会话的 3 条工作记忆")

        # 4) 正式研究记忆必须还在！
        self.assertIsNotNone(get_memory(conn, fm["memory_id"]),
                             "正式 approved 研究记忆绝对不能被删！")

        # 5) 别人的会话记忆必须还在！
        self.assertIsNotNone(get_memory(conn, other_session_mem["memory_id"]),
                             "其他会话的记忆不能被误删！")

        # 6) 被删除的 3 条，都查不到了
        for sid in session_mem_ids:
            self.assertIsNone(get_memory(conn, sid),
                              f"会话 {sid} 应该被删掉了，但还查到了")


class TestPhase12_Acceptance7_NoPreferenceHallucination(unittest.TestCase):
    """
    验收 7：不从系统生成文本中臆测用户偏好
    """

    def test_user_preference_must_have_explicit_user_source(self):
        """
        存 user_preference 类型的记忆时，必须显式指定：
          - preference_source='user_explicit'（用户亲口说的）
          - 或者是 preference_source='approved_user_action'（用户通过批准行为体现的）
        如果 preference_source 是 'system_inferred'（AI 自己猜的），直接抛错不让存。
        这样就不会"从系统生成文本中臆测用户偏好"！
        """
        conn = _make_empty_db()

        # 1) 合法：用户明确表达的偏好，可以存
        good = create_memory_candidate(
            conn, entity_type="user", entity_id="default_user",
            memory_type="user_preference",
            content={"risk_tolerance": "保守", "style": "长线价值", "industry_blacklist": ["军工"]},
            evidence_links=[],
            # 验收 7 关键字段：偏好必须有显式来源
            preference_source="user_explicit",
            preference_explicit_ref="会话 s_abc 第 3 轮用户原话：'我受不了回撤超过 15%'",
        )
        self.assertIsNotNone(get_memory(conn, good["memory_id"]), "合法用户偏好应该被成功保存")

        # 2) 非法：AI 从"系统生成文本"里猜用户偏好（比如看了一眼 AI 自己写的报告，就说用户喜欢成长股）
        #    必须直接抛错，不能存！
        with self.assertRaises(ValueError) as ctx:
            create_memory_candidate(
                conn, entity_type="user", entity_id="default_user",
                memory_type="user_preference",
                content={"style": "偏好高成长小盘"},  # 猜的
                evidence_links=[],
                preference_source="system_inferred",  # 非法来源
            )
        self.assertIn("user_explicit", str(ctx.exception),
                      "system_inferred 的用户偏好绝对不能存！错误信息应该引导用 user_explicit")

    def test_analysis_framework_memory_type(self):
        """
        4 层记忆之「分析框架」：跨标的复用的方法、传导链、验证清单
        memory_type='analysis_framework'
        """
        conn = _make_empty_db()
        mem = create_memory_candidate(
            conn, entity_type="framework", entity_id="fw_gpu_valuation_v1",
            memory_type="analysis_framework",
            content={
                "name": "GPU 公司估值框架 V1",
                "chain": ["算力需求 -> GPU 出货量 -> ASP -> 营收 -> 净利"],
                "checklist": ["1. 云厂资本开支", "2. 代工厂订单", "3. HBM 供货情况"],
            },
            evidence_links=[],
            tags=["估值框架", "GPU", "半导体"],
            project_id="proj_framework_library",
        )
        review_memory(conn, mem["memory_id"], "approve", "u1", "框架验证有效")

        got = get_memory(conn, mem["memory_id"])
        self.assertEqual(got["memory_type"], "analysis_framework")
        self.assertEqual(len(got["content"]["checklist"]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
