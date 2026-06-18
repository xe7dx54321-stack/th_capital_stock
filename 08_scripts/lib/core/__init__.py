"""
lib/core 包初始化文件

核心基础设施模块，包含：
- smr_config_loader: 配置加载
- smr_quality_gate: 质量门控
- smr_guard: 安全守卫
- smr_pipeline_runner: Pipeline 运行器
"""

# 导入核心模块，使其可通过 lib.core 包访问
import sys
from pathlib import Path

# 添加父目录到路径，使转发文件能导入原模块
_parent_lib = str(Path(__file__).resolve().parent.parent)
if _parent_lib not in sys.path:
    sys.path.insert(0, _parent_lib)
