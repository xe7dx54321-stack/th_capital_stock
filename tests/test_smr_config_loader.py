"""
测试通用配置加载器

运行方式：
python -m pytest test_smr_config_loader.py -v
或
python test_smr_config_loader.py
"""

import pytest
from pathlib import Path
import sys
import os

# 添加 lib 目录到路径
lib_path = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
sys.path.insert(0, str(lib_path))
print(f"添加路径: {lib_path}")

from smr_config_loader import ConfigLoader, load_config, get_pipeline_order


class TestConfigLoader:
    """测试配置加载器的各项功能"""
    
    def setup_method(self):
        """测试前清空缓存"""
        ConfigLoader.clear_cache()
    
    def teardown_method(self):
        """测试后清空缓存"""
        ConfigLoader.clear_cache()
    
    def test_get_config_dir(self):
        """测试获取配置目录路径"""
        config_dir = ConfigLoader._get_config_dir()
        assert config_dir.exists(), f"配置目录不存在: {config_dir}"
        assert config_dir.is_dir(), f"不是目录: {config_dir}"
    
    def test_get_config_with_valid_phase(self):
        """测试加载有效的 phase 配置"""
        # 使用存在的配置文件（如果不存在则跳过）
        config_path = ConfigLoader.get_config_path(100)
        if config_path.exists():
            cfg = ConfigLoader.get_config("phase100", "phase100_continuous_production.json")
            assert isinstance(cfg, dict), "配置应该是字典类型"
    
    def test_get_phase_config_with_valid_number(self):
        """测试通过编号加载配置"""
        config_path = ConfigLoader.get_config_path(100)
        if config_path.exists():
            cfg = ConfigLoader.get_phase_config(100)
            assert isinstance(cfg, dict), "配置应该是字典类型"
    
    def test_config_map_has_entries(self):
        """测试配置映射表有内容"""
        assert len(ConfigLoader._config_map) > 0, "配置映射表不应为空"
    
    def test_cache_works(self):
        """测试缓存机制"""
        config_path = ConfigLoader.get_config_path(100)
        if config_path.exists():
            # 第一次加载（通过编号）
            cfg1 = ConfigLoader.get_phase_config(100)
            
            # 第二次加载（同样通过编号，应该使用缓存）
            cfg2 = ConfigLoader.get_phase_config(100)
            
            # 验证是同一个对象（缓存生效）
            assert cfg1 is cfg2, "缓存未生效"
    
    def test_clear_cache(self):
        """测试清空缓存"""
        config_path = ConfigLoader.get_config_path(100)
        if config_path.exists():
            # 加载配置
            cfg1 = ConfigLoader.get_phase_config(100)
            
            # 清空缓存
            ConfigLoader.clear_cache()
            
            # 重新加载
            cfg2 = ConfigLoader.get_phase_config(100)
            
            # 验证不是同一个对象
            assert cfg1 is not cfg2, "缓存未被清空"
    
    def test_file_not_found_raises_error(self):
        """测试加载不存在的配置文件"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.get_config("phase9999")
    
    def test_compat_load_config(self):
        """测试兼容函数 load_config"""
        # 这个函数需要从正确的调用上下文执行
        # 这里仅测试基本功能
        cfg = load_config()
        assert isinstance(cfg, dict), "load_config 应该返回字典"
    
    def test_compat_get_pipeline_order(self):
        """测试兼容函数 get_pipeline_order"""
        result = get_pipeline_order()
        # 结果应该是 None（如果文件不存在）或列表
        assert result is None or isinstance(result, list), \
            f"get_pipeline_order 应该返回 None 或列表，实际返回: {type(result)}"


if __name__ == "__main__":
    """直接运行测试"""
    print("=" * 60)
    print("运行 ConfigLoader 测试")
    print("=" * 60)
    
    test_loader = TestConfigLoader()
    
    # 运行测试
    test_methods = [
        ("test_get_config_dir", test_loader.test_get_config_dir),
        ("test_config_map_has_entries", test_loader.test_config_map_has_entries),
        ("test_cache_works", test_loader.test_cache_works),
        ("test_clear_cache", test_loader.test_clear_cache),
        ("test_compat_load_config", test_loader.test_compat_load_config),
        ("test_compat_get_pipeline_order", test_loader.test_compat_get_pipeline_order),
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
