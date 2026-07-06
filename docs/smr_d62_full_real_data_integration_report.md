# SMR-D6.2 Dashboard Full Real Data Integration 报告

## 1. 执行信息

- **执行时间**: 2026-07-07
- **base branch**: main
- **base commit**: 309b80c
- **work branch**: feature/smr-d62-full-real-data-integration
- **执行阶段**: SMR-D6.2

## 2. 背景与目标

### 背景
Dashboard 已具备 5 页前台形态和 backend read model，但真实有价值的数据接入还不充分。多数 data_status 仍是 partial_snapshot，部分页面仍存在 lightweight/default fallback。

### 目标
把当前系统中真正有价值的数据接口接入 Dashboard，建立 real_data_registry 和 evidence_provenance_resolver，系统性降低默认占位数据比例，确保所有进入页面的数据都有 provenance。

### 核心原则
- 有来源才展示，有证据优先展示
- 无证据生成摘要不进主信号流
- 默认占位不冒充真实数据
- 所有进入页面的数据都要有 provenance
- 不写后台，只读展示
- 不接 opc-foundation

## 3. 真实数据接口复核结果

详见 [smr_d62_real_data_interface_reaudit.md](./smr_d62_real_data_interface_reaudit.md)

| 接口 | 优先级 | 是否有来源 | 是否有证据 | 接入页面 | 处理结果 |
|---|---|---|---|---|---|
| source_registry | P0 | 是 | 部分 | coverage, signals, health | 已注册，可用 |
| daily_report | P0 | 是 | 部分 | today, signals, research | 已注册，可用 |
| evidence_gaps | P0 | 是 | 是 | signals, research, coverage | 已注册，可用 |
| strategy_watch | P0 | 是 | 部分 | today, coverage, research | 已注册，可用 |
| overview | P0 | 是 | 部分 | today, health | 已注册，可用 |
| run_log | P0 | 是 | 否 | health | 已注册，可用 |
| opportunity_engine | P1 | 是 | 部分 | signals, research | 已注册，可用 |
| market_events | P1 | 是 | 部分 | signals, today | 已注册，可用 |
| risk_monitor | P2 | 部分 | 低 | signals, health | 已注册，部分可用 |
| risk_decision | P2 | 部分 | 低 | signals | 已注册，部分可用 |
| foundation_input_stream | pending | 否 | 否 | N/A | 待接入 D7 |

## 4. 新增能力

### 4.1 real_data_registry
- **文件**: [real_data_registry.py](../08_scripts/dashboard/real_data_registry.py)
- **功能**:
  - 统一管理 Dashboard 可使用的真实数据接口
  - 支持 P0/P1/P2 优先级分类
  - 提供 page_source_plan 按页面规划数据源
  - 支持 provenance 验证
  - 提供 real_data_coverage 汇总统计
- **接口**:
  - `list_available_real_sources()`
  - `classify_source_priority()`
  - `get_page_source_plan(page_name)`
  - `validate_source_has_provenance(item)`
  - `summarize_real_data_coverage()`
- **特性**: 只读、不联网、不写文件、不引入外部依赖

### 4.2 evidence_provenance_resolver
- **文件**: [evidence_provenance_resolver.py](../08_scripts/dashboard/evidence_provenance_resolver.py)
- **功能**:
  - 为进入 Dashboard 的数据项补充来源字段
  - 评估 provenance_confidence (high/medium/low/none)
  - 识别 generated_summary/default_fallback/placeholder
  - 过滤主信号流
- **标准字段**:
  - source_type, source_name, source_url, report_path
  - evidence_id, evidence_packet_id
  - published_at, observed_at, generated_at
  - truth_status, data_status
  - provenance_confidence
  - can_enter_main_flow
- **判定规则**:
  - **high**: 有 source_url/evidence_packet_id/report_path + 明确时间 + 非 generated_summary
  - **medium**: 有 source_name/source_type + 后台 snapshot + 缺完整 evidence packet
  - **low**: 真实 snapshot 但缺 source_url/evidence/report_path
  - **none**: default/placeholder/generated_summary/unknown
- **重要规则**: provenance_confidence = none 的内容不得进入主信号流

### 4.3 backend_state real_data_inventory
- **位置**: backend_state.real_data_inventory
- **字段**:
  - available_sources: 可用真实数据源列表
  - partial_sources: 部分可用数据源
  - missing_sources: 缺失数据源
  - pending_integrations: 待接入数据源 (含 foundation_input_stream)
  - total_sources, available_count, partial_count, missing_count, pending_count
  - p0_available, p1_available, p2_available

### 4.4 evidence_provenance_summary
- **位置**: backend_state.evidence_provenance_summary
- **字段**:
  - total_count, high_confidence_count, medium_confidence_count
  - low_confidence_count, none_confidence_count
  - evidence_backed_count, source_backed_count
  - generated_summary_count, default_fallback_count, placeholder_count
  - main_flow_eligible_count, filtered_out_count

## 5. 5 页接入情况

| 页面 | 真实接入来源 | real_item_count | fallback_item_count | data_status | pending |
|---|---|---|---|---|---|
| 今日总览 | daily_report, strategy_watch, overview, evidence_gaps | 动态 | 最低化 | real_snapshot | 更深层 evidence 数据接入 |
| 覆盖池 | source_registry, strategy_watch, watchlist, evidence_gaps | 动态 | 0 (无真实不展示) | partial_snapshot | 独立 coverage object store |
| 信号流 | daily_report, source_registry, evidence_gaps, market_events | 动态 | 0 (主信号流无 fallback) | partial_snapshot | 更多 evidence-backed 来源 |
| 研究队列 | evidence_gaps, daily_report, strategy_watch, opportunity | 动态 | 0 (无 gap 不生成默认项) | partial_snapshot | task store backend integration |
| 数据健康 | source_registry, run_log, overview, pipeline summary | 动态 | 已移除默认 84% | partial_snapshot | 真实 source health 统计 |

### 5.1 今日总览改进
- 今日最重要的 3 件事优先来自 daily_report / strategy_watch / evidence_gaps
- 每条都显示来源 badge
- 若有 report_path / source_url，显示"查看来源"
- 没有来源的 generated_summary 不进入"三件事"
- fallback 默认文案减少到最低

### 5.2 覆盖池改进
- 覆盖对象列表优先来自 watchlist / universe / source_registry
- 每个对象显示真实数据来源数量、最新证据时间、evidence_gap_count、source_count
- 没有真实来源的默认对象不再展示
- 明确说明数据聚合来源

### 5.3 信号流改进
- 主信号流只允许 evidence_backed_real 和 real_snapshot_with_source
- real_snapshot_no_evidence 进入低可信候选区
- generated_summary/default_fallback/placeholder/historical_residual/unknown 不得进入主信号流
- 每条信号都有 source_type, source_name, source_url/report_path/evidence_id
- 展示主信号数、evidence-backed 数、source-backed 数、filtered 数

### 5.4 研究队列改进
- 待研究项来自真实 gap / theme / watch item
- 每个研究项显示证据缺口来源
- 没有 evidence_gap 时不用默认研究项填充
- 操作按钮只读，不写后台
- 标记 "task store pending_backend_integration"

### 5.5 数据健康改进
- **重要**: 移除了默认 84% 信息源可用率的假数据
- 有真实 source_registry 数据时展示真实 counts
- 没有时展示"暂无真实 source health 统计"
- Foundation 输入流继续显示待接入
- 新增 real_data_coverage 模块展示数据源清单

## 6. 信号流质量

- **主信号流准入**: evidence_backed_real + real_snapshot_with_source
- **低可信候选区**: real_snapshot_no_evidence
- **过滤类别**:
  - generated_summary
  - default_fallback
  - placeholder
  - historical_residual
  - unknown
- **D6.1 truth gate 保持**: 机械式风险模板、LLM 生成摘要、无证据风险提示继续被过滤

## 7. 默认占位数据清理

### 已移除/降级
- ✅ 数据健康页默认 84% 信息源可用率 → 改为"暂无真实 source health 统计"
- ✅ 无真实来源的默认覆盖对象 → 不再展示
- ✅ 无 evidence_gap 的默认研究项 → 不再生成
- ✅ 信号流默认假信号 → 不再进入主信号流

### 保留的 fallback
- 页面结构所需的空态文案（"暂无数据"、"待接入"等）
- "当前无 evidence-backed 信号"

### 验证结果
- 是否仍有默认公司: 主信号流无
- 是否仍有默认风险提示: 主信号流无
- 是否仍有模拟时间: 主信号流无
- 是否仍有默认 84% 可用率: 已移除 ✅
- 无真实数据时是否展示空态: 是

## 8. 边界确认

| 边界项 | 状态 |
|---|---|
| 修改投资业务逻辑 | ❌ 未修改 |
| 接入 opc-foundation | ❌ 未接入，标记 pending |
| 联网 | ❌ 未联网 |
| 调用搜索 API | ❌ 未调用 |
| 写入真实后台状态 | ❌ 只读 |
| 提交 data/db/runtime artifacts | ❌ 未提交 |
| 输出 target price | ❌ 未输出 |
| 输出买卖建议 | ❌ 未输出 |
| 输出组合建议 | ❌ 未输出 |
| 打 tag | ❌ 未打 |
| 修改估值模型 | ❌ 未修改 |
| 修改预期差模型 | ❌ 未修改 |
| 修改组合/仓位/交易/风控决策逻辑 | ❌ 未修改 |

## 9. 测试结果

### 9.1 compileall
```
✅ PASS
```

### 9.2 测试总数
- **旧测试**: 254 passed
- **新增 real_data_registry 测试**: 14 passed
- **新增 evidence_provenance_resolver 测试**: 19 passed
- **新增 full_real_data_integration 测试**: 15 passed
- **总计**: 302 passed, 0 failed

### 9.3 5 页 HTTP 验证
| 页面 | 状态 |
|---|---|
| / (今日总览) | 200 OK |
| /coverage (覆盖池) | 200 OK |
| /signals (信号流) | 200 OK |
| /research (研究队列) | 200 OK |
| /health (数据健康) | 200 OK |

### 9.4 已知不相关失败
无

## 10. 文件清单

### 新增文件
- `08_scripts/dashboard/real_data_registry.py` - 真实数据注册表
- `08_scripts/dashboard/evidence_provenance_resolver.py` - 证据溯源解析器
- `tests/test_dashboard_real_data_registry.py` - real_data_registry 测试
- `tests/test_dashboard_evidence_provenance_resolver.py` - provenance resolver 测试
- `tests/test_dashboard_full_real_data_integration.py` - 完整集成测试
- `docs/smr_d62_real_data_interface_reaudit.md` - 接口复核审计
- `docs/smr_d62_full_real_data_integration_report.md` - 本报告

### 修改文件
- `08_scripts/dashboard/backend_data_provider.py` - 加入 real_data_inventory 和 evidence_provenance_summary
- `08_scripts/dashboard/data_health_view_model.py` - 移除默认 84% 假数据
- `08_scripts/dashboard/run_control_tower.py` - 适配 source_availability None 值

## 11. 仍然 pending_backend_integration 的模块

1. **foundation_input_stream** - Foundation 证据输入流，待 D7 接入
2. **独立 coverage object store** - 独立覆盖池数据库，待后续阶段
3. **research task store** - 研究任务存储后端集成
4. **完整 evidence packet 体系** - 证据包完整接入

## 12. 下一步建议

### 选项 1: D6.3 更深数据接入
- 进一步接入更多 P1/P2 级真实数据源
- 深化各页面的 provenance 展示
- 完善 evidence_gap 到研究队列的完整链路

### 选项 2: 进入 D7 Foundation Evidence Inflow
- 接入 opc-foundation 证据输入流
- 建立 Foundation 证据到 Dashboard 的完整通路
- 大幅提升 evidence-backed 信号比例

### 选项 3: 清理 quarantine
- 检查并清理 quarantine 目录
- 释放存储空间

建议: 如 Foundation 输入流已准备好，优先进入 D7；否则可继续 D6.3 深化现有数据接入。
