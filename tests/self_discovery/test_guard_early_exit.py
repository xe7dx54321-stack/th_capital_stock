"""
Guard 门禁开关 early-exit 机制的单元测试（SPEC 2 AC-6）

覆盖：
    - check_self_discovery_enabled: 门禁开关检查函数
    - main() 的 early-exit 行为：self_discovery_enabled=False 时提前退出
    - main() 的 --force 行为：强制运行忽略门禁
    - 三个 scan 脚本的一致性验证
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# 把项目根目录加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "08_scripts" / "self_discovery"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "08_scripts" / "lib"))

# import 三个 scan 脚本
import scan_theme_extension as theme
import scan_supply_chain_extension as supply
import scan_us_benchmark_extension as benchmark


# ============================================================
# check_self_discovery_enabled 函数测试
# ============================================================

class TestCheckSelfDiscoveryEnabled:
    """测试 check_self_discovery_enabled() 函数"""

    def test_default_returns_false(self):
        """默认状态（self_discovery_enabled=False）应返回 False"""
        # Guard.SAFETY_BOUNDARY["self_discovery_enabled"] 默认是 False
        result = theme.check_self_discovery_enabled()
        assert result is False

    def test_returns_true_when_enabled(self, monkeypatch):
        """当 self_discovery_enabled=True 时应返回 True"""
        # 用 monkeypatch 临时修改 SAFETY_BOUNDARY
        monkeypatch.setitem(
            theme.Guard.SAFETY_BOUNDARY,
            "self_discovery_enabled",
            True,
        )
        assert theme.check_self_discovery_enabled() is True

    def test_returns_false_when_guard_is_none(self, monkeypatch):
        """当 Guard 模块 import 失败（Guard=None）时应返回 False"""
        monkeypatch.setattr(theme, "Guard", None)
        assert theme.check_self_discovery_enabled() is False

    def test_returns_false_when_key_missing(self, monkeypatch):
        """当 SAFETY_BOUNDARY 没有 self_discovery_enabled 键时返回 False"""
        # 创建一个没有该键的 mock
        class FakeGuard:
            SAFETY_BOUNDARY = {"other_key": True}

        monkeypatch.setattr(theme, "Guard", FakeGuard)
        assert theme.check_self_discovery_enabled() is False

    def test_supply_chain_imports_check_function(self):
        """供应链脚本应能从 theme_extension import check 函数"""
        assert hasattr(supply, "check_self_discovery_enabled")
        assert supply.check_self_discovery_enabled is theme.check_self_discovery_enabled

    def test_us_benchmark_imports_check_function(self):
        """美股对标脚本应能从 theme_extension import check 函数"""
        assert hasattr(benchmark, "check_self_discovery_enabled")
        assert benchmark.check_self_discovery_enabled is theme.check_self_discovery_enabled


# ============================================================
# main() 的 early-exit 行为测试
# ============================================================

class TestMainEarlyExit:
    """测试 main() 函数的 early-exit 行为"""

    def test_theme_main_early_exit_when_disabled(self, monkeypatch, capsys):
        """theme_extension: 门禁关闭时 main() 应 early-exit，不调用 run_scan"""
        # 确保门禁关闭
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: False)
        # mock run_scan，如果被调用说明 early-exit 失败
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        # mock sys.argv：不加 --force
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py"])

        result = theme.main()

        assert result == 0
        assert called == [], "run_scan 不应被调用"
        captured = capsys.readouterr()
        assert "early-exit" in captured.out
        assert "self_discovery_enabled=False" in captured.out

    def test_supply_main_early_exit_when_disabled(self, monkeypatch, capsys):
        """supply_chain: 门禁关闭时 main() 应 early-exit"""
        monkeypatch.setattr(supply, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(supply, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_supply_chain_extension.py"])

        result = supply.main()

        assert result == 0
        assert called == []
        captured = capsys.readouterr()
        assert "early-exit" in captured.out
        assert "供应链扩展扫描未执行" in captured.out

    def test_benchmark_main_early_exit_when_disabled(self, monkeypatch, capsys):
        """us_benchmark: 门禁关闭时 main() 应 early-exit"""
        monkeypatch.setattr(benchmark, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(benchmark, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_us_benchmark_extension.py"])

        result = benchmark.main()

        assert result == 0
        assert called == []
        captured = capsys.readouterr()
        assert "early-exit" in captured.out
        assert "美股对标扩展扫描未执行" in captured.out


# ============================================================
# main() 的 --force 行为测试
# ============================================================

class TestMainForceFlag:
    """测试 main() 函数的 --force 行为"""

    def test_theme_force_runs_scan_when_disabled(self, monkeypatch, capsys):
        """theme_extension: --force 应忽略门禁并调用 run_scan"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {"status": "ok"})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py", "--force"])

        result = theme.main()

        assert result == 0
        assert called == [False], "run_scan 应被调用一次，dry_run=False"
        captured = capsys.readouterr()
        assert "--force 模式" in captured.out

    def test_theme_force_dry_run(self, monkeypatch):
        """theme_extension: --force --dry-run 应以 dry_run=True 调用 run_scan"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py", "--force", "--dry-run"])

        result = theme.main()

        assert result == 0
        assert called == [True], "run_scan 应以 dry_run=True 被调用"

    def test_supply_force_runs_scan(self, monkeypatch):
        """supply_chain: --force 应调用 run_scan"""
        monkeypatch.setattr(supply, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(supply, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_supply_chain_extension.py", "--force"])

        result = supply.main()

        assert result == 0
        assert called == [False]

    def test_benchmark_force_runs_scan(self, monkeypatch):
        """us_benchmark: --force 应调用 run_scan"""
        monkeypatch.setattr(benchmark, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(benchmark, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_us_benchmark_extension.py", "--force"])

        result = benchmark.main()

        assert result == 0
        assert called == [False]


# ============================================================
# 门禁启用时的行为测试
# ============================================================

class TestMainWhenEnabled:
    """测试门禁启用（self_discovery_enabled=True）时的行为"""

    def test_theme_runs_without_force_when_enabled(self, monkeypatch, capsys):
        """theme_extension: 门禁启用时，不加 --force 也能运行"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: True)
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py"])

        result = theme.main()

        assert result == 0
        assert called == [False], "门禁启用时 run_scan 应被调用"
        captured = capsys.readouterr()
        # 不应出现 early-exit
        assert "early-exit" not in captured.out
        # 也不应出现 --force 提示（因为没加 --force）
        assert "--force 模式" not in captured.out

    def test_supply_runs_without_force_when_enabled(self, monkeypatch):
        """supply_chain: 门禁启用时正常运行"""
        monkeypatch.setattr(supply, "check_self_discovery_enabled", lambda: True)
        called = []
        monkeypatch.setattr(supply, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_supply_chain_extension.py"])

        result = supply.main()

        assert result == 0
        assert called == [False]

    def test_benchmark_runs_without_force_when_enabled(self, monkeypatch):
        """us_benchmark: 门禁启用时正常运行"""
        monkeypatch.setattr(benchmark, "check_self_discovery_enabled", lambda: True)
        called = []
        monkeypatch.setattr(benchmark, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_us_benchmark_extension.py"])

        result = benchmark.main()

        assert result == 0
        assert called == [False]


# ============================================================
# argparse 参数测试
# ============================================================

class TestArgparseFlags:
    """测试 --force 和 --dry-run 参数解析"""

    def test_theme_force_flag_exists(self, monkeypatch):
        """theme_extension: main() 应接受 --force 参数"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: False)
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: {})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py", "--force"])
        # 不应抛出 SystemExit（参数解析错误会抛 SystemExit）
        result = theme.main()
        assert result == 0

    def test_theme_dry_run_flag_exists(self, monkeypatch):
        """theme_extension: main() 应接受 --dry-run 参数"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: True)
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py", "--dry-run"])
        theme.main()
        assert called == [True]

    def test_theme_force_and_dry_run_combined(self, monkeypatch):
        """theme_extension: --force --dry-run 可同时使用"""
        monkeypatch.setattr(theme, "check_self_discovery_enabled", lambda: False)
        called = []
        monkeypatch.setattr(theme, "run_scan", lambda dry_run=False: called.append(dry_run) or {})
        monkeypatch.setattr(sys, "argv", ["scan_theme_extension.py", "--force", "--dry-run"])
        theme.main()
        assert called == [True]
