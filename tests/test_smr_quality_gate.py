"""
测试通用 Quality Gate 模块

运行方式：
python test_smr_quality_gate.py
或
python -m pytest test_smr_quality_gate.py -v
"""

import pytest
from pathlib import Path
import sys
import os

# 添加 lib 目录到路径
lib_path = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
sys.path.insert(0, str(lib_path))
print(f"添加路径: {lib_path}")

from smr_quality_gate import QualityGate, run_quality_gate, run_phase_gate


class TestQualityGate:
    """测试 QualityGate 类的各项功能"""
    
    def test_static_gate_phase150(self):
        """测试静态检查模式（Phase 150）"""
        gate = QualityGate(phase_num=150)
        result = gate.run()
        
        assert "phase150_quality_gate" in result
        assert result["phase150_quality_gate"]["overall_status"] == "pass"
        assert result["phase150_quality_gate"]["all_pass"] is True
        assert "tiers_defined" in result["phase150_quality_gate"]["checks"]
    
    def test_static_gate_phase151(self):
        """测试静态检查模式（Phase 151）"""
        gate = QualityGate(phase_num=151)
        result = gate.run()
        
        assert "phase151_quality_gate" in result
        assert result["phase151_quality_gate"]["overall_status"] == "pass"
        assert "sources_defined" in result["phase151_quality_gate"]["checks"]
    
    def test_static_gate_phase155(self):
        """测试静态检查模式（Phase 155 - 复杂检查）"""
        gate = QualityGate(phase_num=155)
        result = gate.run()
        
        assert "phase155_quality_gate" in result
        assert result["phase155_quality_gate"]["overall_status"] == "pass"
        assert len(result["phase155_quality_gate"]["checks"]) > 10  # 应该有大量检查项
    
    def test_dynamic_gate_phase143_with_pass(self):
        """测试动态检查模式（Phase 143 - 通过）"""
        gate = QualityGate(phase_num=143)
        
        integrity_result = {
            "phase143_link_integrity_check": {
                "overall_status": "pass",
                "files_fail": 0,
                "results": [
                    {"status": "pass"},
                    {"status": "pass"},
                ]
            }
        }
        
        result = gate.run(integrity_result)
        
        assert "phase143_quality_gate" in result
        assert result["phase143_quality_gate"]["overall_status"] == "pass"
        assert result["phase143_quality_gate"]["all_pass"] is True
    
    def test_dynamic_gate_phase143_with_fail(self):
        """测试动态检查模式（Phase 143 - 失败）"""
        gate = QualityGate(phase_num=143)
        
        integrity_result = {
            "phase143_link_integrity_check": {
                "overall_status": "fail",
                "files_fail": 5,
                "results": [
                    {"status": "fail"},
                ]
            }
        }
        
        result = gate.run(integrity_result)
        
        assert "phase143_quality_gate" in result
        assert result["phase143_quality_gate"]["overall_status"] == "fail"
        assert result["phase143_quality_gate"]["all_pass"] is False
    
    def test_unknown_phase(self):
        """测试未知 Phase（使用默认静态检查）"""
        gate = QualityGate(phase_num=999)
        result = gate.run()
        
        assert "phase999_quality_gate" in result
        assert "all_checks_pass" in result["phase999_quality_gate"]["checks"]
    
    def test_run_quality_gate_function(self):
        """测试 run_quality_gate 便捷函数"""
        result = run_quality_gate(phase_num=150)
        
        assert "phase150_quality_gate" in result
    
    def test_run_phase_gate_function(self):
        """测试 run_phase_gate 函数"""
        result = run_phase_gate(phase_num=150)
        
        assert "phase150_quality_gate" in result
    
    def test_phase_name_custom(self):
        """测试自定义 Phase 名称"""
        gate = QualityGate(phase_num=150, phase_name="custom_name")
        result = gate.run()
        
        assert "custom_name_quality_gate" in result


if __name__ == "__main__":
    """直接运行测试"""
    print("=" * 60)
    print("运行 QualityGate 测试")
    print("=" * 60)
    
    test_gate = TestQualityGate()
    
    # 运行测试
    test_methods = [
        ("test_static_gate_phase150", test_gate.test_static_gate_phase150),
        ("test_static_gate_phase151", test_gate.test_static_gate_phase151),
        ("test_static_gate_phase155", test_gate.test_static_gate_phase155),
        ("test_dynamic_gate_phase143_with_pass", test_gate.test_dynamic_gate_phase143_with_pass),
        ("test_dynamic_gate_phase143_with_fail", test_gate.test_dynamic_gate_phase143_with_fail),
        ("test_unknown_phase", test_gate.test_unknown_phase),
        ("test_run_quality_gate_function", test_gate.test_run_quality_gate_function),
        ("test_run_phase_gate_function", test_gate.test_run_phase_gate_function),
        ("test_phase_name_custom", test_gate.test_phase_name_custom),
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
