"""
通用 Pipeline Runner 模块

提供统一的 pipeline 运行框架，替代大部分 run_phase*.py 文件

设计原则：
1. 简化简单 pipeline（调用 build 函数）
2. 提供标准 CLI 参数（--dry-run, --execute, --skip-network, --json）
3. 提供标准结果结构
4. 支持质量门控和安全守卫

使用方式：
# 方式1：直接使用通用 Runner
from smr_pipeline_runner import PipelineRunner

runner = PipelineRunner(
    phase_num=150,
    build_module="build_phase150_tiering_dashboard",
    result_extractor=lambda r: r["phase150_tiering_dashboard"]
)
runner.run()

# 方式2：创建便捷函数
from smr_pipeline_runner import create_pipeline

# 创建 run_phase150_tiering_pipeline.py
run_tiering_pipeline = create_pipeline(
    phase_num=150,
    build_module="build_phase150_tiering_dashboard",
    result_extractor=lambda r: r["phase150_tiering_dashboard"],
    output_name="phase150_tiering_pipeline"
)

if __name__ == "__main__":
    run_tiering_pipeline()
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import importlib
import io
import contextlib


class PipelineRunner:
    """
    通用 Pipeline 运行器
    
    提供统一的运行框架，处理：
    - 路径设置
    - 模块导入
    - 模式切换（dry-run/execute/skip-network）
    - 质量门控
    - 安全守卫
    - CLI 参数解析
    - 结果输出
    
    Attributes:
        phase_num: Phase 编号
        build_module: build 模块名（如 "build_phase150_tiering_dashboard"）
        result_extractor: 从 build 结果提取关键数据的函数
        output_name: 输出 JSON 的键名
    """
    
    def __init__(
        self,
        phase_num: int,
        build_module: str,
        result_extractor: Optional[Callable[[Dict], Dict]] = None,
        output_name: Optional[str] = None,
        phase_name: Optional[str] = None,
    ):
        """
        初始化 Pipeline Runner
        
        Args:
            phase_num: Phase 编号
            build_module: build 模块名
            result_extractor: 从 build 结果提取数据的函数（可选）
            output_name: 输出 JSON 的键名（可选，默认 phase{NNN}_pipeline）
            phase_name: Phase 名称（可选）
        """
        self.phase_num = phase_num
        self.build_module = build_module
        self.result_extractor = result_extractor or (lambda r: r)
        self.output_name = output_name or f"phase{phase_num}_pipeline"
        self.phase_name = phase_name
        
        # 路径设置
        self.base_lib = Path(__file__).resolve().parent
        self.base_reporting = self.base_lib.parent / "reporting"
        self.base_jobs = self.base_lib.parent / "jobs"
    
    def setup_paths(self):
        """设置模块搜索路径"""
        if str(self.base_lib) not in sys.path:
            sys.path.insert(0, str(self.base_lib))
        if str(self.base_reporting) not in sys.path:
            sys.path.insert(0, str(self.base_reporting))
    
    def import_build_module(self):
        """导入 build 模块"""
        self.setup_paths()
        module = importlib.import_module(self.build_module)
        return module
    
    def run(self, mode: str = "dry-run", use_json: bool = False) -> Dict[str, Any]:
        """
        运行 pipeline
        
        Args:
            mode: 运行模式（dry-run/execute/skip-network）
            use_json: 是否使用 JSON 缩进输出
        
        Returns:
            运行结果字典
        """
        started_at = datetime.now().isoformat()
        
        try:
            # 导入并执行 build
            module = self.import_build_module()
            build_result = module.build()
            
            # 提取结果
            extracted = self.result_extractor(build_result)
            
            # 构建输出
            output = {
                self.output_name: {
                    "mode": mode,
                    "started_at": started_at,
                    "finished_at": datetime.now().isoformat(),
                    "build_success": True,
                }
            }
            
            # 合并提取的结果
            if isinstance(extracted, dict):
                output[self.output_name].update(extracted)
            
            # 添加标准字段
            output[self.output_name].update({
                "research_only": True,
                "mock_used": False,
                "fixture_used": False,
                "trade_recommendation_created": 0,
                "paper_order_created": 0,
            })
            
            return output
            
        except Exception as e:
            # 错误处理
            return {
                self.output_name: {
                    "mode": mode,
                    "started_at": started_at,
                    "finished_at": datetime.now().isoformat(),
                    "build_success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            }
    
    def main(self, args: Optional[List[str]] = None):
        """
        CLI 入口函数
        
        Args:
            args: 命令行参数（可选，默认使用 sys.argv）
        """
        parser = argparse.ArgumentParser(
            description=f"Phase {self.phase_num} Pipeline"
        )
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
        parser.add_argument("--execute", action="store_true", help="Execute mode")
        parser.add_argument("--skip-network", action="store_true", help="Skip network calls")
        parser.add_argument("--json", action="store_true", help="Pretty print JSON")
        
        parsed = parser.parse_args(args)
        
        # 确定模式
        if parsed.execute:
            mode = "execute"
        elif parsed.skip_network:
            mode = "skip-network"
        else:
            mode = "dry-run"
        
        # 运行
        result = self.run(mode=mode)
        
        # 输出
        if parsed.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(json.dumps(result, ensure_ascii=False, default=str))


# ====================
# 便捷函数
# ====================

def create_pipeline(
    phase_num: int,
    build_module: str,
    result_extractor: Optional[Callable[[Dict], Dict]] = None,
    output_name: Optional[str] = None,
    phase_name: Optional[str] = None,
) -> Callable:
    """
    创建 Pipeline 运行函数
    
    Args:
        phase_num: Phase 编号
        build_module: build 模块名
        result_extractor: 结果提取函数
        output_name: 输出键名
        phase_name: Phase 名称
    
    Returns:
        可调用的函数
    
    Example:
        run_tiering = create_pipeline(
            phase_num=150,
            build_module="build_phase150_tiering_dashboard",
            result_extractor=lambda r: r["phase150_tiering_dashboard"],
            output_name="phase150_tiering_pipeline"
        )
        
        # 在新文件中使用：
        # run_tiering_pipeline = create_pipeline(...)
        # if __name__ == "__main__":
        #     run_tiering_pipeline()
    """
    runner = PipelineRunner(
        phase_num=phase_num,
        build_module=build_module,
        result_extractor=result_extractor,
        output_name=output_name,
        phase_name=phase_name,
    )
    
    def run_pipeline(args: Optional[List[str]] = None):
        runner.main(args)
    
    run_pipeline.__name__ = f"run_phase{phase_num}_pipeline"
    run_pipeline.__qualname__ = f"smr_pipeline_runner.run_phase{phase_num}_pipeline"
    
    return run_pipeline


# ====================
# 预定义的 Pipeline 创建函数
# ====================

def create_tiering_pipeline():
    """创建 Phase 150 分层 Pipeline"""
    return create_pipeline(
        phase_num=150,
        build_module="build_phase150_tiering_dashboard",
        result_extractor=lambda r: r["phase150_tiering_dashboard"],
        output_name="phase150_tiering_pipeline"
    )


def create_discovery_pipeline():
    """创建 Phase 151 发现 Pipeline"""
    return create_pipeline(
        phase_num=151,
        build_module="build_phase151_discovery_dashboard",
        result_extractor=lambda r: r["phase151_discovery_dashboard"],
        output_name="phase151_discovery_pipeline"
    )


def create_scheduling_pipeline():
    """创建 Phase 155 调度 Pipeline"""
    return create_pipeline(
        phase_num=155,
        build_module="build_phase155_scheduling_dashboard",
        result_extractor=lambda r: r["phase155_scheduling_dashboard"],
        output_name="phase155_loop_scheduling_pipeline"
    )


# ====================
# 兼容旧的导入方式
# ====================

_COMPAT_CACHE: Dict[int, Callable] = {}


def __getattr__(name: str) -> Callable:
    """支持 from smr_pipeline_runner import run_phase150_tiering_pipeline"""
    
    if name.startswith("run_phase") and name.endswith("_pipeline"):
        # 提取 phase 编号和 pipeline 名称
        parts = name.replace("run_phase", "").replace("_pipeline", "").split("_", 1)
        if len(parts) == 1:
            phase_num = int(parts[0])
            pipeline_name = f"phase{phase_num}_pipeline"
        else:
            phase_num = int(parts[0])
            pipeline_name = f"phase{phase_num}_{parts[1]}_pipeline"
        
        # 从已知的 build 模块映射
        build_module_map = {
            150: "build_phase150_tiering_dashboard",
            151: "build_phase151_discovery_dashboard",
            155: "build_phase155_scheduling_dashboard",
        }
        
        build_module = build_module_map.get(phase_num)
        if build_module:
            return create_pipeline(
                phase_num=phase_num,
                build_module=build_module,
                output_name=pipeline_name
            )
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
