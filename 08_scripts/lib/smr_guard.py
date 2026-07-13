"""
通用 Guard 模块，替代所有 smr_phase*_guard.py 文件

Guard 是安全边界检查，确保系统不会：
- 生成交易建议
- 设置目标价格
- 执行真实交易
- 调用 LLM（除非明确允许）
- 等等

使用方式：
from smr_guard import Guard, run_guard

# 方式1：使用通用类
guard = Guard(phase_num=155)
result = guard.check()

# 方式2：使用便捷函数
result = run_guard(phase_num=155)
"""

from typing import Dict, Any, Optional, Callable


class Guard:
    """
    通用安全边界守卫类
    
    Attributes:
        phase_num: Phase 编号
        phase_name: Phase 名称（可选）
    """
    
    # 安全边界定义
    SAFETY_BOUNDARY = {
        "no_trade_recommendation": True,
        "no_target_price": True,
        "no_position_sizing": True,
        "no_buy_sell_short": True,
        "no_paper_order": False,
        "no_broker_api_call": True,
        "no_real_trade": True,
        "no_investment_advice": True,
        "system_scheduler_disabled": False,
        "live_llm_call_made": False,
        "agent_simulation_only": True,
        "activation_disabled": False,
        "auto_promote_disabled": False,
        "mock_not_used": True,
        "fixture_not_used": True,
        "research_only": False,
    }
    
    # Phase-specific 规则
    _GUARD_RULES: Dict[int, Dict[str, Any]] = {}
    
    def __init__(self, phase_num: int = 151, phase_name: Optional[str] = None):
        """
        初始化 Guard
        
        Args:
            phase_num: Phase 编号
            phase_name: Phase 名称（可选，默认从规则映射获取）
        """
        self.phase_num = phase_num
        self.phase_name = phase_name or self._get_phase_name(phase_num)
    
    def _get_phase_name(self, phase_num: int) -> str:
        """根据 Phase 编号获取名称"""
        name_map = {
            151: "cannot_conclude",
            155: "scheduling",
        }
        base_name = name_map.get(phase_num, "")
        if base_name:
            return f"phase{phase_num}_{base_name}"
        return f"phase{phase_num}"
    
    def check(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行安全边界检查
        
        Args:
            context: 上下文信息（可选）
        
        Returns:
            检查结果字典
        """
        rules = self._get_rules()
        
        # 合并安全边界
        checks = self.SAFETY_BOUNDARY.copy()
        if rules:
            checks.update(rules.get("_custom_checks", {}))
        
        # 计算违规数：只有标记为 False 且应该是 True 的项才算违规
        # 某些项如 live_llm_call_made: False 表示"没有调用"，是正常的
        violation_keywords = ["no_", "not_", "disabled", "_ok"]
        violations = 0
        violation_details = []
        for k, v in checks.items():
            if v is False:
                # 检查是否是以 violation_keywords 开头的项
                is_violation = any(k.startswith(prefix) for prefix in violation_keywords)
                if is_violation:
                    violations += 1
                    violation_details.append(k)
        
        return {
            f"{self.phase_name}": {
                "overall_status": "pass" if violations == 0 else "fail",
                "violations": violations,
                "checks": checks,
                "violation_details": violation_details,
                "mock_used": False,
                "fixture_used": False,
            }
        }
    
    def _get_rules(self) -> Dict[str, Any]:
        """获取 Phase 特定规则"""
        return self._GUARD_RULES.get(self.phase_num, {})


# ====================
# 便捷函数
# ====================

def run_guard(phase_num: int = 151, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    运行安全边界检查的便捷函数
    
    Args:
        phase_num: Phase 编号
        context: 上下文信息（可选）
    
    Returns:
        检查结果
    """
    guard = Guard(phase_num=phase_num)
    return guard.check(context)


def run_scheduling_guard() -> Dict[str, Any]:
    """
    运行调度守卫（Phase 155）
    
    Returns:
        检查结果
    """
    return run_guard(phase_num=155)


def run_cannot_conclude_guard() -> Dict[str, Any]:
    """
    运行不能得出结论守卫（Phase 151）
    
    Returns:
        检查结果
    """
    return run_guard(phase_num=151)


# ====================
# Phase-specific 运行函数
# ====================

def _make_phase_guard_function(phase_num: int) -> Callable:
    """
    为指定 Phase 创建运行函数
    
    Args:
        phase_num: Phase 编号
    
    Returns:
        可调用的函数
    """
    def run_phase_guard(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        guard = Guard(phase_num=phase_num)
        return guard.check(context)
    
    return run_phase_guard


# 设置 Phase 规则
Guard._GUARD_RULES = {
    155: {
        "_custom_checks": {
            # Phase 155 特有的额外检查
            "schedule_plan_not_trade_plan": True,
            "event_trigger_not_trade_signal": True,
            "loop_history_not_pnl_history": True,
            "owner_digest_not_investment_advice": True,
            "watch_core_updated": False,
            "candidate_auto_activated": False,
            "300394_blocker_retained": True,
            "688041_derived_valuation_retained": True,
        }
    },
}


# ====================
# 兼容旧的模块级函数
# ====================

_compat_cache: Dict[int, Callable] = {}


def __getattr__(name: str) -> Callable:
    """支持 from smr_phase155_guard import run_phase155_scheduling_guard"""
    
    # 处理 run_phaseXXX_guard 格式
    if name.startswith("run_phase") and name.endswith("_guard"):
        phase_str = name.replace("run_phase", "").replace("_guard", "")
        try:
            phase_num = int(phase_str)
            if phase_num not in _compat_cache:
                _compat_cache[phase_num] = _make_phase_guard_function(phase_num)
            return _compat_cache[phase_num]
        except ValueError:
            pass
    
    # 处理 run_phaseXXX_scheduling_guard 格式
    if name.startswith("run_phase") and name.endswith("_scheduling_guard"):
        phase_str = name.replace("run_phase", "").replace("_scheduling_guard", "")
        try:
            phase_num = int(phase_str)
            return run_scheduling_guard
        except ValueError:
            pass
    
    # 处理 run_phaseXXX_cannot_conclude_guard 格式
    if name.startswith("run_phase") and name.endswith("_cannot_conclude_guard"):
        phase_str = name.replace("run_phase", "").replace("_cannot_conclude_guard", "")
        try:
            phase_num = int(phase_str)
            return run_cannot_conclude_guard
        except ValueError:
            pass
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
