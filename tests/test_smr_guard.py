"""
测试通用 Guard 模块

运行方式：
python test_smr_guard.py
"""

import pytest
from pathlib import Path
import sys

# 添加 lib 目录到路径
lib_path = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
sys.path.insert(0, str(lib_path))
print(f"添加路径: {lib_path}")

from smr_guard import Guard, run_guard, run_scheduling_guard, run_cannot_conclude_guard


class TestGuard:
    """测试 Guard 类的各项功能"""
    
    def test_phase151_guard(self):
        """测试 Phase 151 Guard"""
        guard = Guard(phase_num=151)
        result = guard.check()
        
        assert "phase151_cannot_conclude" in result
        assert result["phase151_cannot_conclude"]["overall_status"] == "pass"
        assert result["phase151_cannot_conclude"]["violations"] == 0
    
    def test_phase155_guard(self):
        """测试 Phase 155 Guard（调度守卫）"""
        guard = Guard(phase_num=155)
        result = guard.check()
        
        assert "phase155_scheduling" in result
        assert result["phase155_scheduling"]["overall_status"] == "pass"
        # Phase 155 有一些 False 值（按设计）
        assert "schedule_plan_not_trade_plan" in result["phase155_scheduling"]["checks"]
        assert "no_trade_recommendation" in result["phase155_scheduling"]["checks"]
    
    def test_run_guard_function(self):
        """测试 run_guard 便捷函数"""
        result = run_guard(phase_num=151)
        
        assert "phase151_cannot_conclude" in result
    
    def test_run_scheduling_guard(self):
        """测试 run_scheduling_guard 函数"""
        result = run_scheduling_guard()
        
        assert "phase155_scheduling" in result
    
    def test_run_cannot_conclude_guard(self):
        """测试 run_cannot_conclude_guard 函数"""
        result = run_cannot_conclude_guard()
        
        assert "phase151_cannot_conclude" in result
    
    def test_unknown_phase(self):
        """测试未知 Phase（使用默认规则）"""
        guard = Guard(phase_num=999)
        result = guard.check()
        
        assert "phase999" in result
        assert result["phase999"]["overall_status"] == "pass"
    
    def test_safety_boundary_present(self):
        """测试安全边界定义存在"""
        guard = Guard(phase_num=151)
        result = guard.check()
        
        # 应该有所有安全边界检查
        checks = result[list(result.keys())[0]]["checks"]
        assert "no_trade_recommendation" in checks
        assert "no_target_price" in checks
        assert "no_real_trade" in checks


if __name__ == "__main__":
    """直接运行测试"""
    print("=" * 60)
    print("运行 Guard 测试")
    print("=" * 60)
    
    test_guard = TestGuard()
    
    # 运行测试
    test_methods = [
        ("test_phase151_guard", test_guard.test_phase151_guard),
        ("test_phase155_guard", test_guard.test_phase155_guard),
        ("test_run_guard_function", test_guard.test_run_guard_function),
        ("test_run_scheduling_guard", test_guard.test_run_scheduling_guard),
        ("test_run_cannot_conclude_guard", test_guard.test_run_cannot_conclude_guard),
        ("test_unknown_phase", test_guard.test_unknown_phase),
        ("test_safety_boundary_present", test_guard.test_safety_boundary_present),
    ]
    
    passed = 0
    failed = 0
    
    for name, method in test_methods:
        try:
            method()
            print(f"✓ {name}")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
