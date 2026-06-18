"""
lib/core/smr_config_loader.py

转发文件：实际实现在 lib/smr_config_loader.py
此文件保持向后兼容，允许 from core.smr_config_loader import ... 的导入方式
"""
# 导入实际实现
from smr_config_loader import (
    ConfigLoader,
    load_config,
    get_pipeline_order,
    get_reports_dir,
    is_reports_gitignored,
    is_manual_assignment_only,
)

__all__ = [
    'ConfigLoader',
    'load_config',
    'get_pipeline_order',
    'get_reports_dir',
    'is_reports_gitignored',
    'is_manual_assignment_only',
]
