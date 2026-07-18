"""
aggregate_discovery_candidates.py 的单元测试

小白讲解：这个测试文件验证候选聚合管道的核心逻辑：
1. 策略配置读取是否正确
2. 门禁开关检查是否正确
3. 3 道门筛选逻辑是否正确（门1基本过滤、门2主题相关性、门3技术面）
4. VFM 数据缺失时的降级处理
5. dry-run 模式能正常跑完不报错
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "08_scripts" / "lib"))

from aggregate_discovery_candidates import (  # noqa: E402
    GATE_THRESHOLDS,
    check_gate1,
    check_gate2,
    check_gate3,
    check_guard_switches,
    load_policy,
    run_aggregate,
    run_three_gates,
)


# ============================================================
# 测试策略配置读取
# ============================================================

class TestLoadPolicy:
    """测试 load_policy 函数"""

    def test_returns_dict(self):
        """验证返回类型是 dict"""
        policy = load_policy()
        assert isinstance(policy, dict)

    def test_has_required_keys(self):
        """验证包含必要的配置项"""
        policy = load_policy()
        assert "mode" in policy
        assert "max_candidates_per_theme" in policy
        assert "min_composite_score_for_proposal" in policy
        assert "require_human_approval_before_pool" in policy
        assert "scan_schedule" in policy

    def test_development_mode_defaults(self):
        """验证开发模式默认值"""
        policy = load_policy()
        # 应该是 development 模式
        assert policy["mode"] == "development"
        # 需要人工确认入池（硬约束）
        assert policy["require_human_approval_before_pool"] is True
        # 最低提案评分 6.0
        assert policy["min_composite_score_for_proposal"] == 6.0


# ============================================================
# 测试门禁开关检查
# ============================================================

class TestCheckGuardSwitches:
    """测试 check_guard_switches 函数"""

    def test_returns_dict(self):
        """验证返回类型是 dict"""
        switches = check_guard_switches()
        assert isinstance(switches, dict)

    def test_has_required_keys(self):
        """验证包含必要的开关项"""
        switches = check_guard_switches()
        assert "self_discovery_enabled" in switches
        assert "auto_proposal_enabled" in switches

    def test_development_mode_defaults_false(self):
        """验证开发模式下两个开关都是 False"""
        switches = check_guard_switches()
        # 开发模式下两个开关都应该默认 False
        assert switches["self_discovery_enabled"] is False
        assert switches["auto_proposal_enabled"] is False


# ============================================================
# 测试门 1：基本过滤
# ============================================================

class TestCheckGate1:
    """测试 check_gate1 函数"""

    def test_pass_with_good_score(self):
        """验证：composite_score >= 4.0 且无严重 red_flag，应通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {"composite_score": 7.5, "red_flags": []}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is True
        assert "7.5" in reason

    def test_fail_with_low_score(self):
        """验证：composite_score < 4.0，应不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {"composite_score": 3.5, "red_flags": []}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is False
        assert "3.5" in reason

    def test_fail_with_severe_red_flag(self):
        """验证：有严重 red_flag（如 ST），应不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {"composite_score": 8.0, "red_flags": ["ST"]}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is False
        assert "ST" in reason

    def test_pass_with_non_severe_red_flag(self):
        """验证：有非严重 red_flag（如高估值），应通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {"composite_score": 6.0, "red_flags": ["短期波动加大"]}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is True

    def test_degraded_mode_pass_with_multiple_hits(self):
        """验证：无VFM数据但被多个方法命中(>=2)，降级通过"""
        candidate = {"hit_methods": 3, "sector": "semiconductor_compute"}
        vfm = {}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is True
        assert "多个方法命中" in reason

    def test_degraded_mode_fail_with_single_hit(self):
        """验证：无VFM数据且只被1个方法命中，降级不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {}
        passed, reason = check_gate1(candidate, vfm)
        assert passed is False
        assert "待评分" in reason


# ============================================================
# 测试门 2：主题相关性
# ============================================================

class TestCheckGate2:
    """测试 check_gate2 函数"""

    def test_pass_with_high_theme_relevance(self):
        """验证：theme_relevance >= 5.0，应通过"""
        candidate = {"sector": "semiconductor_compute"}
        vfm = {"theme_relevance": 6.0, "industry_position": 3.0}
        passed, reason = check_gate2(candidate, vfm)
        assert passed is True
        assert "6.0" in reason

    def test_pass_with_high_industry_position(self):
        """验证：industry_position >= 6.0，应通过"""
        candidate = {"sector": "semiconductor_compute"}
        vfm = {"theme_relevance": 3.0, "industry_position": 7.0}
        passed, reason = check_gate2(candidate, vfm)
        assert passed is True
        assert "7.0" in reason

    def test_fail_with_both_low(self):
        """验证：theme_relevance < 5.0 且 industry_position < 6.0，应不通过"""
        candidate = {"sector": "semiconductor_compute"}
        vfm = {"theme_relevance": 4.0, "industry_position": 5.0}
        passed, reason = check_gate2(candidate, vfm)
        assert passed is False

    def test_degraded_mode_pass_with_sector(self):
        """验证：无VFM数据但有sector标签，降级通过"""
        candidate = {"sector": "embodied_ai"}
        vfm = {}
        passed, reason = check_gate2(candidate, vfm)
        assert passed is True
        assert "sector" in reason

    def test_degraded_mode_fail_without_sector(self):
        """验证：无VFM数据且无sector标签，降级不通过"""
        candidate = {"sector": ""}
        vfm = {}
        passed, reason = check_gate2(candidate, vfm)
        assert passed is False


# ============================================================
# 测试门 3：技术面有吸引力
# ============================================================

class TestCheckGate3:
    """测试 check_gate3 函数"""

    def test_pass_with_high_momentum(self):
        """验证：technical_momentum >= 5.0，应通过"""
        candidate = {}
        vfm = {"technical_momentum": 6.5, "red_flags": []}
        passed, reason = check_gate3(candidate, vfm)
        assert passed is True
        assert "6.5" in reason

    def test_fail_with_low_momentum(self):
        """验证：technical_momentum < 5.0 且无反转/突破信号，应不通过"""
        candidate = {}
        vfm = {"technical_momentum": 3.0, "red_flags": []}
        passed, reason = check_gate3(candidate, vfm)
        assert passed is False

    def test_pass_with_reversal_signal(self):
        """验证：technical_momentum < 5.0 但有反转信号，应通过"""
        candidate = {}
        vfm = {"technical_momentum": 3.0, "red_flags": ["底部反转信号"]}
        passed, reason = check_gate3(candidate, vfm)
        assert passed is True
        assert "反转" in reason

    def test_pass_with_breakthrough_signal(self):
        """验证：technical_momentum < 5.0 但有突破信号，应通过"""
        candidate = {}
        vfm = {"technical_momentum": 4.0, "red_flags": ["向上突破"]}
        passed, reason = check_gate3(candidate, vfm)
        assert passed is True
        assert "突破" in reason

    def test_degraded_mode_fail_without_vfm(self):
        """验证：无VFM数据，降级不通过（技术面无法评估）"""
        candidate = {}
        vfm = {}
        passed, reason = check_gate3(candidate, vfm)
        assert passed is False
        assert "待评分" in reason


# ============================================================
# 测试 3 道门综合筛选
# ============================================================

class TestRunThreeGates:
    """测试 run_three_gates 函数"""

    def test_all_pass(self):
        """验证：3 道门全部通过"""
        candidate = {"hit_methods": 2, "sector": "semiconductor_compute"}
        vfm = {
            "composite_score": 7.0,
            "theme_relevance": 6.0,
            "technical_momentum": 5.5,
            "red_flags": [],
        }
        result = run_three_gates(candidate, vfm)
        assert result["passed"] is True
        assert result["gate1"][0] is True
        assert result["gate2"][0] is True
        assert result["gate3"][0] is True

    def test_fail_gate1_only(self):
        """验证：只门1不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {
            "composite_score": 3.0,  # < 4.0
            "theme_relevance": 6.0,
            "technical_momentum": 5.5,
            "red_flags": [],
        }
        result = run_three_gates(candidate, vfm)
        assert result["passed"] is False
        assert result["gate1"][0] is False
        assert result["gate2"][0] is True
        assert result["gate3"][0] is True

    def test_fail_gate2_only(self):
        """验证：只门2不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {
            "composite_score": 7.0,
            "theme_relevance": 3.0,  # < 5.0
            "industry_position": 4.0,  # < 6.0
            "technical_momentum": 5.5,
            "red_flags": [],
        }
        result = run_three_gates(candidate, vfm)
        assert result["passed"] is False
        assert result["gate1"][0] is True
        assert result["gate2"][0] is False
        assert result["gate3"][0] is True

    def test_fail_gate3_only(self):
        """验证：只门3不通过"""
        candidate = {"hit_methods": 1, "sector": "semiconductor_compute"}
        vfm = {
            "composite_score": 7.0,
            "theme_relevance": 6.0,
            "technical_momentum": 3.0,  # < 5.0
            "red_flags": [],
        }
        result = run_three_gates(candidate, vfm)
        assert result["passed"] is False
        assert result["gate1"][0] is True
        assert result["gate2"][0] is True
        assert result["gate3"][0] is False

    def test_degraded_mode_multiple_hits(self):
        """
        验证：降级模式下（无VFM数据），被多个方法命中的候选
        通过门1和门2，但门3不通过（技术面无法评估）。
        """
        candidate = {"hit_methods": 3, "sector": "embodied_ai"}
        vfm = {}
        result = run_three_gates(candidate, vfm)
        # 门1: 降级通过（hit_methods >= 2）
        assert result["gate1"][0] is True
        # 门2: 降级通过（有 sector）
        assert result["gate2"][0] is True
        # 门3: 降级不通过（无 VFM 数据）
        assert result["gate3"][0] is False
        assert result["passed"] is False


# ============================================================
# 测试主流程
# ============================================================

class TestRunAggregate:
    """测试 run_aggregate 主流程"""

    def test_dry_run_completes_without_error(self):
        """
        验证：dry-run 模式能完整跑完，不报错。
        即使 discovery_candidate 表为空也能正常运行。
        """
        summary = run_aggregate(dry_run=True)

        assert isinstance(summary, dict)
        # 表为空时返回 0
        assert "total_candidates" in summary
        assert "dry_run" in summary
        assert summary["dry_run"] is True

    def test_dry_run_with_force_proposal(self):
        """验证：dry-run + force-proposal 也能正常跑完"""
        summary = run_aggregate(dry_run=True, force_proposal=True)
        assert isinstance(summary, dict)
        assert summary["dry_run"] is True
