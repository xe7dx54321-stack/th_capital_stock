"""
测试通用 Pipeline Runner 模块

运行方式：
python test_smr_pipeline_runner.py
"""

import pytest
from pathlib import Path
import sys
import json

# 添加 lib 目录到路径
lib_path = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
sys.path.insert(0, str(lib_path))
print(f"添加路径: {lib_path}")

from smr_pipeline_runner import PipelineRunner, create_pipeline


class TestPipelineRunner:
    """测试 PipelineRunner 类的各项功能"""
    
    def test_runner_initialization(self):
        """测试 Runner 初始化"""
        runner = PipelineRunner(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
        )
        
        assert runner.phase_num == 150
        assert runner.build_module == "build_phase150_tiering_dashboard"
        assert runner.output_name == "phase150_pipeline"
    
    def test_runner_custom_output_name(self):
        """测试自定义输出名称"""
        runner = PipelineRunner(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
            output_name="phase150_tiering_pipeline"
        )
        
        assert runner.output_name == "phase150_tiering_pipeline"
    
    def test_runner_result_extractor(self):
        """测试结果提取器"""
        def extractor(r):
            d = r.get("phase150_tiering_dashboard", {})
            return {
                "tiers": d.get("tier_assignments", {}).get("tier_counts", {}),
                "total": d.get("tier_assignments", {}).get("total", 0),
            }
        
        runner = PipelineRunner(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
            result_extractor=extractor,
        )
        
        assert callable(runner.result_extractor)
    
    def test_runner_paths(self):
        """测试路径设置"""
        runner = PipelineRunner(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
        )
        
        assert runner.base_lib.exists()
        assert runner.base_lib.name == "lib"
    
    def test_create_pipeline_function(self):
        """测试 create_pipeline 函数"""
        run_pipeline = create_pipeline(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
            output_name="phase150_tiering_pipeline"
        )
        
        assert callable(run_pipeline)
        assert run_pipeline.__name__ == "run_phase150_pipeline"
    
    def test_run_with_mock_build(self):
        """测试 run 方法（使用 mock build 模块）"""
        # 创建一个临时的 mock build 模块
        import types
        mock_module = types.ModuleType("mock_build")
        mock_module.build = lambda: {
            "phase150_tiering_dashboard": {
                "tier_assignments": {
                    "tier_counts": {"core": 3, "watch": 5, "candidate": 2},
                    "total": 10
                }
            }
        }
        
        # 将 mock 模块注入到 sys.modules
        sys.modules["mock_build"] = mock_module
        
        runner = PipelineRunner(
            phase_num=150,
            build_module="mock_build",
            result_extractor=lambda r: r.get("phase150_tiering_dashboard", {}),
            output_name="phase150_tiering_pipeline"
        )
        
        result = runner.run(mode="dry-run")
        
        # 清理
        del sys.modules["mock_build"]
        
        assert "phase150_tiering_pipeline" in result
        assert result["phase150_tiering_pipeline"]["mode"] == "dry-run"
        assert result["phase150_tiering_pipeline"]["build_success"] is True
    
    def test_run_with_error(self):
        """测试 run 方法（构建失败）"""
        import types
        mock_module = types.ModuleType("mock_error_build")
        mock_module.build = lambda: 1/0  # 模拟错误
        
        sys.modules["mock_error_build"] = mock_module
        
        runner = PipelineRunner(
            phase_num=150,
            build_module="mock_error_build",
            output_name="phase150_pipeline"
        )
        
        result = runner.run(mode="dry-run")
        
        del sys.modules["mock_error_build"]
        
        assert "phase150_pipeline" in result
        assert result["phase150_pipeline"]["build_success"] is False
        assert "error" in result["phase150_pipeline"]
    
    def test_mode_switching(self):
        """测试模式切换"""
        runner = PipelineRunner(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
        )
        
        # 测试 dry-run
        result_dry = runner.run(mode="dry-run")
        assert result_dry["phase150_pipeline"]["mode"] == "dry-run"
        
        # 测试 execute
        result_exec = runner.run(mode="execute")
        assert result_exec["phase150_pipeline"]["mode"] == "execute"
        
        # 测试 skip-network
        result_skip = runner.run(mode="skip-network")
        assert result_skip["phase150_pipeline"]["mode"] == "skip-network"


class TestCreatePipeline:
    """测试 create_pipeline 函数"""
    
    def test_basic_pipeline(self):
        """测试基本 pipeline 创建"""
        run_p = create_pipeline(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
        )
        
        assert callable(run_p)
    
    def test_pipeline_with_extractor(self):
        """测试带提取器的 pipeline"""
        run_p = create_pipeline(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
            result_extractor=lambda r: {"custom": "data"},
            output_name="custom_pipeline"
        )
        
        assert callable(run_p)
    
    def test_multiple_pipelines(self):
        """测试创建多个 pipeline"""
        pipelines = [
            create_pipeline(phase_num=150, build_module="build_phase150_tiering_dashboard"),
            create_pipeline(phase_num=151, build_module="build_phase151_discovery_dashboard"),
            create_pipeline(phase_num=155, build_module="build_phase155_scheduling_dashboard"),
        ]
        
        assert len(pipelines) == 3
        assert all(callable(p) for p in pipelines)


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_create_tiering_pipeline(self):
        """测试 create_tiering_pipeline"""
        from smr_pipeline_runner import create_tiering_pipeline
        
        run_tiering = create_tiering_pipeline()
        assert callable(run_tiering)
    
    def test_create_discovery_pipeline(self):
        """测试 create_discovery_pipeline"""
        from smr_pipeline_runner import create_discovery_pipeline
        
        run_discovery = create_discovery_pipeline()
        assert callable(run_discovery)
    
    def test_create_scheduling_pipeline(self):
        """测试 create_scheduling_pipeline"""
        from smr_pipeline_runner import create_scheduling_pipeline
        
        run_scheduling = create_scheduling_pipeline()
        assert callable(run_scheduling)


if __name__ == "__main__":
    """直接运行测试"""
    print("=" * 60)
    print("运行 PipelineRunner 测试")
    print("=" * 60)
    
    test_runner = TestPipelineRunner()
    test_create = TestCreatePipeline()
    test_convenience = TestConvenienceFunctions()
    
    # 运行测试
    test_methods = [
        # PipelineRunner 测试
        ("test_runner_initialization", test_runner.test_runner_initialization),
        ("test_runner_custom_output_name", test_runner.test_runner_custom_output_name),
        ("test_runner_result_extractor", test_runner.test_runner_result_extractor),
        ("test_runner_paths", test_runner.test_runner_paths),
        ("test_create_pipeline_function", test_runner.test_create_pipeline_function),
        ("test_run_with_mock_build", test_runner.test_run_with_mock_build),
        ("test_run_with_error", test_runner.test_run_with_error),
        ("test_mode_switching", test_runner.test_mode_switching),
        
        # CreatePipeline 测试
        ("test_basic_pipeline", test_create.test_basic_pipeline),
        ("test_pipeline_with_extractor", test_create.test_pipeline_with_extractor),
        ("test_multiple_pipelines", test_create.test_multiple_pipelines),
        
        # 便捷函数测试
        ("test_create_tiering_pipeline", test_convenience.test_create_tiering_pipeline),
        ("test_create_discovery_pipeline", test_convenience.test_create_discovery_pipeline),
        ("test_create_scheduling_pipeline", test_convenience.test_create_scheduling_pipeline),
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
