# Phase 编号制重构 - 下一步优化计划

> 本文档详细规划两个后续优化任务：
> - 任务一：迁移现有 run_phase*.py 文件
> - 任务三：按业务域重组 lib 目录
> 
> 请仔细审阅后再开始执行。

---

## 任务一：迁移现有 run_phase*.py 文件

### 1.1 目标

将 200+ 个 `run_phase*.py` 文件迁移到使用新的 `smr_pipeline_runner.py` 模块，减少重复代码，统一运行框架。

### 1.2 迁移策略

采用**渐进式迁移**，分三批进行：

| 批次 | Phase 范围 | 数量 | 复杂度 | 优先级 |
|------|-----------|------|--------|--------|
| 第一批 | 150-165 | ~16 个 | 低 | 高 |
| 第二批 | 100-149 | ~50 个 | 中 | 中 |
| 第三批 | 67-99, 166-207 | ~134 个 | 高 | 低 |

### 1.3 第一批迁移计划（Phase 150-165）

这些是最常用的核心 pipeline，结构简单，适合作为试点。

#### 1.3.1 迁移清单

| Phase | 原文件 | 新实现方式 |
|-------|--------|-----------|
| 150 | `run_phase150_tiering_pipeline.py` | `create_pipeline(phase_num=150, build_module="build_phase150_tiering_dashboard")` |
| 151 | `run_phase151_discovery_pipeline.py` | `create_pipeline(phase_num=151, build_module="build_phase151_discovery_dashboard")` |
| 152 | `run_phase152_admission_scoring_pipeline.py` | `create_pipeline(phase_num=152, build_module="build_phase152_admission_dashboard")` |
| 153 | `run_phase153_onboarding_review_pipeline.py` | `create_pipeline(phase_num=153, build_module="build_phase153_onboarding_dashboard")` |
| 154 | `run_phase154_multi_agent_loop_pipeline.py` | `create_pipeline(phase_num=154, build_module="build_phase154_multi_agent_dashboard")` |
| 155 | `run_phase155_loop_scheduling_pipeline.py` | `create_pipeline(phase_num=155, build_module="build_phase155_scheduling_dashboard")` |
| 156 | `run_phase156_activation_review_pipeline.py` | `create_pipeline(phase_num=156, build_module="build_phase156_activation_dashboard")` |
| 157 | `run_phase157_decision_input_pipeline.py` | `create_pipeline(phase_num=157, build_module="build_phase157_decision_dashboard")` |
| 158 | `run_phase158_decision_ui_pipeline.py` | `create_pipeline(phase_num=158, build_module="build_phase158_ui_dashboard")` |
| 159 | `run_phase159_submission_pipeline.py` | `create_pipeline(phase_num=159, build_module="build_phase159_submission_dashboard")` |
| 160 | `run_phase160_example_pack_pipeline.py` | `create_pipeline(phase_num=160, build_module="build_phase160_example_dashboard")` |
| 161 | `run_phase161_ui_feedback_pipeline.py` | `create_pipeline(phase_num=161, build_module="build_phase161_feedback_dashboard")` |
| 162 | `run_phase162_candidate_hydration_pipeline.py` | `create_pipeline(phase_num=162, build_module="build_phase162_hydration_dashboard")` |
| 163 | `run_phase163_live_hydration_pipeline.py` | `create_pipeline(phase_num=163, build_module="build_phase163_live_dashboard")` |
| 164 | `run_phase164_hydration_console_pipeline.py` | `create_pipeline(phase_num=164, build_module="build_phase164_console_dashboard")` |
| 165 | `run_phase165_readiness_repair_pipeline.py` | `create_pipeline(phase_num=165, build_module="build_phase165_repair_dashboard")` |

#### 1.3.2 迁移步骤（每个 Phase）

```
步骤 1：读取原文件，确认 build 模块名和输出结构
步骤 2：创建新的简化文件（使用 create_pipeline）
步骤 3：运行测试验证输出一致
步骤 4：备份原文件（重命名为 .bak）
步骤 5：确认新文件正常工作
```

#### 1.3.3 新文件模板

```python
# run_phase150_tiering_pipeline.py（迁移后）
"""
Phase 150: Watchlist Tiering Pipeline

使用 smr_pipeline_runner 统一框架
"""
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from smr_pipeline_runner import create_pipeline

# 创建 pipeline
run_phase150_tiering_pipeline = create_pipeline(
    phase_num=150,
    build_module="build_phase150_tiering_dashboard",
    result_extractor=lambda r: {
        "tiers": r["phase150_tiering_dashboard"]["tier_assignments"]["tier_counts"],
        "total_tracked": r["phase150_tiering_dashboard"]["tier_assignments"]["total"],
        "quality_gate": r["phase150_tiering_dashboard"]["quality_gate"]["overall_status"],
        "guard": r["phase150_tiering_dashboard"]["guard"]["overall_status"],
    },
    output_name="phase150_tiering_pipeline"
)

if __name__ == "__main__":
    run_phase150_tiering_pipeline()
```

#### 1.3.4 验证方法

```bash
# 运行原文件
python 08_scripts/jobs/run_phase150_tiering_pipeline.py --dry-run --json > old_output.json

# 运行新文件
python 08_scripts/jobs/run_phase150_tiering_pipeline.py --dry-run --json > new_output.json

# 对比输出（核心字段应一致）
python -c "
import json
old = json.load(open('old_output.json'))
new = json.load(open('new_output.json'))
print('旧输出键:', list(old.keys()))
print('新输出键:', list(new.keys()))
"
```

### 1.4 第二批迁移计划（Phase 100-149）

这些 pipeline 有中等复杂度，部分有依赖其他 pipeline 的逻辑。

#### 1.4.1 特殊处理

| Phase | 特殊情况 | 处理方式 |
|-------|----------|----------|
| 100 | 调用 phase97/98/99 | 保留原逻辑，不迁移 |
| 117 | Master runner，调用多个子 pipeline | 保留原逻辑，不迁移 |
| 140 | System hardening | 可迁移，需自定义结果提取 |
| 141-149 | Agent 相关 | 可迁移，需验证 build 模块存在 |

#### 1.4.2 迁移优先级

```
高优先级（简单）：
- 140, 141, 142, 143, 144, 145, 146, 147, 148, 149

中优先级（需验证）：
- 120-139（大部分可迁移）

低优先级（复杂）：
- 100, 117（保留原逻辑）
```

### 1.5 第三批迁移计划（Phase 67-99, 166-207）

这些是历史遗留或高度复杂的 pipeline，建议：

- **Phase 67-99**：大部分是数据采集和证据链相关，可按需迁移
- **Phase 166-207**：Owner 决策流程相关，复杂度高，建议保留原逻辑或单独评估

### 1.6 迁移后的文件结构

```
08_scripts/jobs/
├── run_phase150_tiering_pipeline.py      # 简化后（~15行）
├── run_phase151_discovery_pipeline.py    # 简化后（~15行）
├── ...
├── run_phase100_continuous_production_pipeline.py  # 保留原逻辑（复杂）
├── run_phase117_master_daily_runner.py            # 保留原逻辑（复杂）
└── _migrated/                             # 备份目录
    ├── run_phase150_tiering_pipeline.py.bak
    ├── run_phase151_discovery_pipeline.py.bak
    └── ...
```

### 1.7 预期收益

| 指标 | 迁移前 | 迁移后 | 减少 |
|------|--------|--------|------|
| 第一批文件行数 | ~480 行（16×30） | ~240 行（16×15） | -50% |
| 第二批文件行数 | ~1500 行（50×30） | ~750 行（50×15） | -50% |
| 重复代码 | 大量 | 极少 | -80% |
| 维护成本 | 高 | 低 | 显著降低 |

---

## 任务三：按业务域重组 lib 目录

### 3.1 目标

将扁平的 `lib/` 目录（400+ 个 phase 文件）按业务域重组，建立清晰的模块边界。

### 3.2 当前问题

```
lib/
├── smr_phase67_*.py          # 证据链
├── smr_phase85_*.py          # 估值
├── smr_phase100_*.py         # 生产监控
├── smr_phase150_*.py         # 股票池分层
├── smr_phase151_*.py         # 标的发现
├── smr_phase155_*.py         # 调度
├── smr_phase173_*.py         # Owner 决策
├── ...（400+ 个文件混在一起）
```

**问题**：
- 无模块边界，难以理解
- 改一个功能要跨多个 phase 文件
- 新人无法快速定位

### 3.3 目标结构

```
lib/
├── core/                          # 核心基础设施
│   ├── smr_config_loader.py       # 配置加载（已完成）
│   ├── smr_quality_gate.py        # 质量门控（已完成）
│   ├── smr_guard.py               # 安全守卫（已完成）
│   ├── smr_pipeline_runner.py     # Pipeline 运行器（已完成）
│   ├── smr_registry.py            # Registry（保留）
│   ├── smr_paths.py               # 路径工具（保留）
│   ├── smr_llm.py                 # LLM 调用（保留）
│   └── smr_runlog.py              # 运行日志（保留）
│
├── market_data/                   # 市场数据模块
│   ├── smr_data_harvester.py      # 数据采集（保留）
│   ├── smr_daily_bar.py           # 日 K 线（保留）
│   ├── smr_us_bar.py              # 美股数据（保留）
│   └── smr_news_ingestion.py      # 新闻摄入（保留）
│
├── fundamentals/                  # 基本面模块
│   ├── smr_financial_loader.py    # 财务数据（保留）
│   ├── smr_cninfo_adapter.py      # 巨潮资讯（保留）
│   └── smr_filings_ingestion.py   # 公告摄入（保留）
│
├── valuation/                     # 估值模块
│   ├── smr_valuation_adapter.py   # 估值适配器（保留）
│   ├── smr_pe_pb.py               # PE/PB（保留）
│   └── smr_valuation_quality.py   # 估值质量（保留）
│
├── stock_pool/                    # 股票池模块
│   ├── tiering.py                 # 分层逻辑（从 phase150 合并）
│   ├── discovery.py               # 发现逻辑（从 phase151 合并）
│   ├── admission.py               # 入池逻辑（从 phase152 合并）
│   └── onboarding.py              # 入池审查（从 phase153 合并）
│
├── portfolio/                     # 组合模块
│   ├── pnl.py                     # 盈亏计算（保留）
│   ├── entry.py                   # 建仓逻辑（保留）
│   └── position_tracker.py        # 持仓跟踪（保留）
│
├── risk/                          # 风控模块
│   ├── monitor.py                 # 风控监控（保留）
│   ├── constraint_checker.py      # 约束检查（保留）
│   └── alert_handler.py           # 告警处理（保留）
│
├── research/                      # 研究模块
│   ├── thesis_checker.py          # Thesis 检查（保留）
│   ├── evidence_chain.py          # 证据链（保留）
│   └── deep_dive.py               # 深度研究（保留）
│
├── agents/                        # Agent 模块
│   ├── smr_agents.py              # Agent 核心（保留，后续可能删除）
│   ├── orchestration.py           # Agent 编排（从 phase145 合并）
│   └ memory_queue.py              # Agent 内存（从 phase146 合并）
│
├── wiki/                          # Wiki 模块
│   ├── smr_wiki_ingestion.py      # Wiki 摄入（保留）
│   ├── smr_wiki_promotion.py      # Wiki 提升（保留）
│   └── smr_wiki_quality.py        # Wiki 质量（保留）
│
├── reporting/                     # 报告模块
│   ├── build_phase150_tiering_dashboard.py  # Dashboard 构建（保留）
│   ├── build_phase151_discovery_dashboard.py
│   └── ...
│
└── _legacy/                       # 旧文件备份
    ├── smr_phase67_*.py
    ├── smr_phase85_*.py
    └── ...（所有旧 phase 文件）
```

### 3.4 重组策略

采用**渐进式重组**，分三步：

#### 步骤 1：创建新目录结构

```bash
# 创建目录
mkdir -p lib/core
mkdir -p lib/market_data
mkdir -p lib/fundamentals
mkdir -p lib/valuation
mkdir -p lib/stock_pool
mkdir -p lib/portfolio
mkdir -p lib/risk
mkdir -p lib/research
mkdir -p lib/agents
mkdir -p lib/wiki
mkdir -p lib/reporting
mkdir -p lib/_legacy
```

#### 步骤 2：移动已完成的核心模块

```bash
# 移动已创建的通用模块
mv lib/smr_config_loader.py lib/core/
mv lib/smr_quality_gate.py lib/core/
mv lib/smr_guard.py lib/core/
mv lib/smr_pipeline_runner.py lib/core/
```

#### 步骤 3：按业务域分类移动

| 业务域 | Phase 范围 | 移动策略 |
|--------|-----------|----------|
| 市场数据 | 67-72, 90-98 | 移动到 market_data/ |
| 基本面 | 73-84 | 移动到 fundamentals/ |
| 估值 | 85-86 | 移动到 valuation/ |
| 股票池 | 150-165 | 合并到 stock_pool/ |
| 组合 | 120-125 | 移动到 portfolio/ |
| 风控 | 103-106 | 移动到 risk/ |
| 研究 | 136-138 | 移动到 research/ |
| Agent | 145-155 | 移动到 agents/ |
| Wiki | 143-144 | 移动到 wiki/ |

### 3.5 兼容性保障

为保持向后兼容，在 `lib/` 根目录创建**转发文件**：

```python
# lib/smr_phase150_config.py（转发文件）
"""
兼容性转发文件
原文件已移动到 lib/core/smr_config_loader.py
"""
from core.smr_config_loader import ConfigLoader, load_config, get_pipeline_order

# 导出所有原有接口
__all__ = ['ConfigLoader', 'load_config', 'get_pipeline_order']
```

### 3.6 导入路径更新

| 原导入 | 新导入 | 兼容方式 |
|--------|--------|----------|
| `from smr_config_loader import ...` | `from core.smr_config_loader import ...` | 转发文件 |
| `from smr_phase150_config import ...` | `from core.smr_config_loader import ...` | 转发文件 |
| `from smr_quality_gate import ...` | `from core.smr_quality_gate import ...` | 转发文件 |

### 3.7 重组后的测试验证

```bash
# 运行所有测试
python tests/test_smr_config_loader.py
python tests/test_smr_quality_gate.py
python tests/test_smr_guard.py
python tests/test_smr_pipeline_runner.py

# 验证导入路径
python -c "from core.smr_config_loader import ConfigLoader; print('OK')"
python -c "from smr_config_loader import ConfigLoader; print('OK')"  # 兼容导入
```

### 3.8 预期收益

| 指标 | 重组前 | 重组后 | 改善 |
|------|--------|--------|------|
| 目录文件数 | 400+ 个 | ~50 个/目录 | 清晰 |
| 模块边界 | 无 | 有 | 明确 |
| 新人理解时间 | 数小时 | 数分钟 | 显著降低 |
| 改功能跨文件数 | 5-10 个 | 1-3 个 | 减少 |

---

## 执行顺序建议

### 推荐顺序

```
1. 任务一第一批迁移（Phase 150-165）
   ↓ 验证通过
2. 任务三步骤 1-2（创建目录 + 移动核心模块）
   ↓ 验证通过
3. 任务一第二批迁移（Phase 100-149）
   ↓ 验证通过
4. 任务三步骤 3（按业务域分类移动）
   ↓ 验证通过
5. 任务一第三批迁移（Phase 67-99, 166-207）
   ↓ 验证通过
6. 清理旧文件
```

### 时间估算

| 任务 | 预计时间 |
|------|----------|
| 任务一第一批 | 2 天 |
| 任务三步骤 1-2 | 0.5 天 |
| 任务一第二批 | 3 天 |
| 任务三步骤 3 | 2 天 |
| 任务一第三批 | 3 天 |
| 清理旧文件 | 1 天 |
| **总计** | **11.5 天** |

---

## 风险控制

| 风险 | 缓解措施 |
|------|----------|
| 迁移后功能不一致 | 每个文件迁移后运行对比测试 |
| 导入路径中断 | 创建转发文件保持兼容 |
| 测试覆盖不足 | 迁移后运行原有测试 |
| 复杂 pipeline 迁移失败 | 保留原逻辑，不强制迁移 |

---

*文档版本：1.0*
*生成时间：2026-06-18*