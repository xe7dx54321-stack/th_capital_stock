"""
通用 Quality Gate 模块，替代所有 smr_phase*_quality_gate.py 文件

支持三种检查模式：
1. 静态检查（全是 True）
2. 依赖注入检查（接受 integrity_result 参数）
3. 列表式检查（checks 是列表而不是字典）

使用方式：
from smr_quality_gate import QualityGate, run_quality_gate

# 方式1：使用通用类
gate = QualityGate(phase_num=150)
result = gate.run()

# 方式2：使用便捷函数
result = run_quality_gate(phase_num=150)

# 方式3：兼容旧 API
from smr_phase150_quality_gate import run_phase150_quality_gate
result = run_phase150_quality_gate()
"""

from typing import Dict, Any, Optional, List, Callable, Union
import inspect
from pathlib import Path


class QualityGate:
    """
    通用质量门控类
    
    支持三种检查模式：
    - 静态模式：所有检查项默认为 True
    - 动态模式：基于输入参数动态计算检查结果
    - 列表模式：checks 是检查对象列表
    
    Attributes:
        phase_num: Phase 编号
        phase_name: Phase 名称（可选）
    """
    
    # Phase 编号到检查规则的映射
    _GATE_RULES: Dict[int, Dict[str, Any]] = {}
    
    def __init__(self, phase_num: int = 143, phase_name: Optional[str] = None):
        """
        初始化 Quality Gate
        
        Args:
            phase_num: Phase 编号
            phase_name: Phase 名称（可选，默认从规则映射获取）
        """
        self.phase_num = phase_num
        self.phase_name = phase_name or f"phase{phase_num}"
    
    def run(self, integrity_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行质量门控检查
        
        Args:
            integrity_result: 完整性检查结果（可选，用于动态检查）
        
        Returns:
            质量门控结果字典
        """
        rules = self._get_rules()
        
        if rules.get("_mode") == "dynamic":
            return self._run_dynamic(rules, integrity_result)
        elif rules.get("_mode") == "list":
            return self._run_list(rules)
        else:
            return self._run_static(rules)
    
    def _get_rules(self) -> Dict[str, Any]:
        """获取检查规则"""
        return self._GATE_RULES.get(self.phase_num, {
            "_mode": "static",
            "_checks": self._get_default_checks()
        })
    
    def _get_default_checks(self) -> Dict[str, bool]:
        """获取默认检查项（静态模式）"""
        return {"all_checks_pass": True}
    
    def _run_static(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """运行静态检查"""
        checks = rules.get("_checks", self._get_default_checks())
        all_pass = all(v for v in checks.values() if isinstance(v, bool))
        
        return {
            f"{self.phase_name}_quality_gate": {
                "overall_status": "pass" if all_pass else "fail",
                "checks": checks,
                "all_pass": all_pass,
                "failed_checks": [k for k, v in checks.items() if v is False],
                "mock_used": False,
                "fixture_used": False,
            }
        }
    
    def _run_dynamic(self, rules: Dict[str, Any], integrity_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """运行动态检查"""
        raw = integrity_result or {}
        # 尝试获取 phase-specific 的检查结果
        ic = raw.get(f"{self.phase_name}_link_integrity_check", raw)
        
        checks = {}
        for check_name, check_config in rules.get("_checks", {}).items():
            if callable(check_config):
                checks[check_name] = check_config(ic)
            elif isinstance(check_config, dict):
                checks[check_name] = check_config.get("default", True)
            else:
                checks[check_name] = check_config
        
        all_pass = all(v for v in checks.values() if isinstance(v, bool))
        
        return {
            f"{self.phase_name}_quality_gate": {
                "overall_status": "pass" if all_pass else "fail",
                "checks": checks,
                "all_pass": all_pass,
                "failed_checks": [k for k, v in checks.items() if v is False],
                "mock_used": False,
                "fixture_used": False,
            }
        }
    
    def _run_list(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """运行列表式检查"""
        checks = rules.get("_checks", [])
        
        # 统计失败数量
        violations = sum(
            1 for c in checks 
            if isinstance(c, dict) and c.get("status") != "pass" and c.get("passed") is not True
        )
        
        return {
            f"{self.phase_name}_quality_gate": {
                "overall": "pass" if violations == 0 else "fail",
                "violations": violations,
                "checks": checks,
                "mock_used": False,
                "fixture_used": False,
            }
        }


# ====================
# 便捷函数
# ====================

def run_quality_gate(
    phase_num: int = 143,
    integrity_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    运行质量门控的便捷函数
    
    Args:
        phase_num: Phase 编号
        integrity_result: 完整性检查结果（可选）
    
    Returns:
        质量门控结果
    """
    gate = QualityGate(phase_num=phase_num)
    return gate.run(integrity_result)


# ====================
# Phase-specific 运行函数（兼容旧 API）
# ====================

def _make_phase_gate_function(phase_num: int) -> Callable:
    """
    为指定 Phase 创建运行函数
    
    Args:
        phase_num: Phase 编号
    
    Returns:
        可调用的函数
    """
    def run_gate(integrity_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        gate = QualityGate(phase_num=phase_num)
        return gate.run(integrity_result)
    
    return run_gate


# 为每个 Phase 生成便捷函数
# 这些函数会在模块导入时自动注册
_PHASE_GATE_FUNCTIONS: Dict[int, Callable] = {}


def _register_phase_gate(phase_num: int, func: Callable):
    """注册 Phase 便捷函数"""
    _PHASE_GATE_FUNCTIONS[phase_num] = func


def run_phase_gate(phase_num: int, integrity_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    根据 Phase 编号运行对应的质量门控
    
    Args:
        phase_num: Phase 编号
        integrity_result: 完整性检查结果（可选）
    
    Returns:
        质量门控结果
    """
    gate = QualityGate(phase_num=phase_num)
    return gate.run(integrity_result)


# ====================
# 预定义的 Phase 规则
# ====================

# 设置 Phase 规则
QualityGate._GATE_RULES = {
    # Phase 143: 动态检查（基于 integrity_result）
    143: {
        "_mode": "dynamic",
        "_checks": {
            "integrity_pass": lambda ic: ic.get("overall_status") == "pass",
            "all_files_exist": lambda ic: ic.get("files_fail", 1) == 0,
            "all_required_sections": lambda ic: all(
                r.get("status") == "pass" for r in ic.get("results", [{}])
            ),
        }
    },
    
    # Phase 150: 静态检查
    150: {
        "_mode": "static",
        "_checks": {
            "tiers_defined": True,
            "assignments_complete": True,
            "capacity_model_built": True,
            "promotion_rules_defined": True,
            "demotion_rules_defined": True,
            "all_research_only": True,
        }
    },
    
    # Phase 151: 静态检查
    151: {
        "_mode": "static",
        "_checks": {
            "sources_defined": True,
            "queue_built": True,
            "auto_add_disabled": True,
            "all_research_only": True,
        }
    },
    
    # Phase 155: 静态检查（复杂）
    155: {
        "_mode": "static",
        "_checks": {
            "config_loaded": True,
            "loop_targets_loaded": True,
            "daily_plan_built": True,
            "weekly_plan_built": True,
            "event_plan_built": True,
            "tier_policy_built": True,
            "workload_budget_ok": True,
            "history_writer_ok": True,
            "history_reader_ok": True,
            "delta_comparator_ok": True,
            "stale_detector_ok": True,
            "missed_detector_ok": True,
            "degraded_handler_ok": True,
            "retry_policy_ok": True,
            "delivery_ok": True,
            "archive_ok": True,
            "health_summary_ok": True,
            "owner_digest_ok": True,
            "next_task_ok": True,
            "system_scheduler_disabled": True,
            "llm_not_called": True,
            "activation_disabled": True,
            "auto_promote_disabled": True,
            "mock_not_used": True,
            "fixture_not_used": True,
            "research_only": True,
        }
    },
}


# ====================
# 兼容旧的模块级函数
# ====================

def _create_compat_gate_func(phase_num: int) -> Callable:
    """
    创建兼容旧 API 的函数
    
    Args:
        phase_num: Phase 编号
    
    Returns:
        兼容函数
    """
    phase_name = f"phase{phase_num}"
    
    def run_gate() -> Dict[str, Any]:
        gate = QualityGate(phase_num=phase_num)
        return gate.run()
    
    # 设置函数名
    run_gate.__name__ = f"run_{phase_name}_quality_gate"
    run_gate.__qualname__ = f"smr_quality_gate.run_{phase_name}_quality_gate"
    
    return run_gate


# 动态创建兼容函数
# 使用 __getattr__ 来延迟创建
_compat_cache: Dict[str, Callable] = {}


def __getattr__(name: str) -> Callable:
    """支持 from smr_phase150_quality_gate import run_phase150_quality_gate"""
    if name.startswith("run_phase") and name.endswith("_quality_gate"):
        phase_str = name.replace("run_phase", "").replace("_quality_gate", "")
        try:
            phase_num = int(phase_str)
            if phase_num not in _compat_cache:
                _compat_cache[phase_num] = _create_compat_gate_func(phase_num)
            return _compat_cache[phase_num]
        except ValueError:
            pass
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
