# SMR-D2 Dashboard 信号流施工报告

## 1. 执行时间

- 2026-07
- 基线分支：`feature/smr-d1-dashboard-today-overview`

## 2. Base Commit

- base branch: `feature/smr-d1-dashboard-today-overview`
- base commit: `8590079` — feat(dashboard): add today overview workbench

## 3. Branch

- work branch: `feature/smr-d2-dashboard-signal-flow`

## 4. 当前 Dashboard 启动方式

```bash
cd /Users/apple/Documents/同行资本二级市场
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

访问地址：
- 今日总览：`http://127.0.0.1:8877/`
- 信号流：`http://127.0.0.1:8877/signals`

## 5. 新增/修改文件

### 新增

| 文件 | 用途 |
|---|---|
| `08_scripts/dashboard/signal_flow_view_model.py` | 信号流 view model，把原始 state 转为页面展示结构 |
| `tests/test_dashboard_signal_flow.py` | 信号流页面测试（31 个用例） |
| `docs/smr_d2_dashboard_signal_flow_report.md` | 本报告 |

### 修改

| 文件 | 变更说明 |
|---|---|
| `08_scripts/dashboard/run_control_tower.py` | 新增 signal_flow import、信号流专属 CSS、`render_signal_flow` 渲染函数及辅助函数、`/signals` 路由 query 参数解析、更新 `PAGE_RENDERERS` |
| `docs/smr_d0_dashboard_product_blueprint.md` | 补充 D2 信号流施工状态标记 |
| `docs/smr_d0_dashboard_data_mapping.md` | 补充 D2 信号流实际数据映射状态 |

## 6. Page 3 信号流实现范围

| 模块 | 实现状态 | 说明 |
|---|---|---|
| 5 页主导航 | ✅ 实现 | 信号流高亮，其余保持不变 |
| 顶部筛选栏 | ✅ 实现 | 时间范围 / 来源类型 / 关联对象 / 证据强度 / 关键词搜索 / 重置筛选 |
| 信号时间线 | ✅ 实现 | 左侧时间点 + 信号卡片，最多 20 条，8 条以上显示「加载更多」占位 |
| 今日信号摘要 | ✅ 实现 | 4 张小卡片：新增信号数 / 重点公司数 / 高强度证据数 / 需复核数 |
| 热门关联对象 | ✅ 实现 | chip 形式，公司 + 主题混合，从信号聚合 |
| 信号来源分布 | ✅ 实现 | 轻量 CSS 水平条形图，7 种来源类型 |
| 底部免责声明 | ✅ 实现 | 「系统仅展示证据与信号，不直接给出投资建议。」 |
| 空态设计 | ✅ 实现 | 无信号时显示空态文案 |

## 7. 筛选栏实现情况

| 筛选项 | 实现状态 | URL 参数 | 说明 |
|---|---|---|---|
| 时间范围 | ✅ | `time_range` | 24h / 7d / 30d / all |
| 来源类型 | ✅ | `source_type` | 全部 / 官方披露 / 公司 IR / 公开研究 / 媒体摘录 / 电话会纪要 / Foundation / 风险监控 |
| 关联对象 | ✅ | `entity` | 全部 / 公司 / 行业 / 主题 |
| 证据强度 | ✅ | `strength` | 全部 / 高 / 中 / 低 / 待确认 |
| 关键词搜索 | ✅ | `q` | 匹配标题 / 摘要 / 关联对象 / 主题 |
| 重置筛选 | ✅ | 跳转 `/signals` | 清除所有筛选条件 |
| 异常参数处理 | ✅ | — | fail-soft，不导致 500 |

## 8. 信号时间线实现情况

每条信号包含字段：
- `time_label` — 相对时间标签
- `title` — 信号标题
- `summary` — 1 行摘要（≤80 字）
- `source_type` + `source_label` — 来源类型 badge
- `related_entities` — 关联公司 badge
- `related_topics` — 关联主题 badge
- `evidence_strength` — 证据强度 badge（高/中/低/待确认，颜色区分）
- `review_status` — 复核状态 badge
- `source_url` — 查看原文按钮（无则 disabled）
- `evidence_url` — 查看证据包按钮（无则 disabled）

视觉结构：
- 左侧蓝色时间节点 + 连接线
- 右侧白色卡片
- 操作按钮置底

## 9. 右侧摘要模块实现情况

| 模块 | 状态 | 数据来源 |
|---|---|---|
| 今日信号摘要（4 卡片） | ✅ | signals 聚合统计 |
| 热门关联对象（chips） | ✅ | signals related_entities + related_topics 聚合 |
| 信号来源分布（条形图） | ✅ | signals source_type 聚合 |

## 10. 数据来源映射

| UI 模块 | 当前数据来源 | 缺失时处理 | 后续 Foundation 输入 |
|---|---|---|---|
| 信号列表 | risk.decision.sell_candidates → 风险监控信号<br>current_state.evidence_gaps → 待补证据信号<br>strategy_watch.top_focus_items → 策略研究信号<br>opportunity.markets → 机会雷达信号<br>risk.monitor.alerts → 风险监控信号<br>daily_report.highlights → 日报摘要信号 | 空态卡片 | EvidencePacket 统一证据流 |
| 今日信号摘要 | 从 signals 聚合：total / focus_company / high_strength / needs_review | 全部为 0 | Foundation 侧统一计数 |
| 热门关联对象 | 从 signals related_entities + related_topics 聚合计数，取前 12 | 空态提示 | Foundation 侧 trending entities |
| 信号来源分布 | 从 signals source_type 聚合，7 种固定类型 | 全部为 0 | Foundation 侧 source type 统计 |
| 筛选能力 | 服务端内存过滤，支持 5 个维度 | 不匹配即空 | Foundation API 查询参数 |

## 11. 空态设计

- **信号时间线空态**：显示「暂无信号 / 当前筛选条件下没有可展示的证据或事件。请调整筛选条件，或查看数据健康。」
- **热门关联对象空态**：显示「暂无热门关联对象」
- **来源分布空态**：显示「暂无来源分布数据」
- **摘要卡片空态**：所有计数显示 0

技术保证：`build_signal_flow_view_model(None)` 和 `build_signal_flow_view_model({})` 均不抛出异常。

## 12. 是否接入 opc-foundation

**否**。本阶段未接入 `opc-foundation`。所有数据均来自现有 `build_dashboard_state` 输出的 SQLite / JSON snapshot，通过轻量映射转为信号格式。

## 13. 是否修改投资业务逻辑

**否**。未修改以下任何模块：

- 估值模型
- 预期差模型
- 投资组合 / 仓位 / 风控 / 交易信号逻辑
- 自动化任务

仅修改了 Dashboard 前端渲染层和新增 view model 适配层。

## 14. 是否输出 target price / 买卖建议 / 组合建议

**否**。已通过测试验证以下禁用词不出现在页面渲染中：

- target price / 目标价
- 买入 / 卖出 / 建仓
- 仓位建议 / 组合建议
- position_size / trade_signal / expected_return / valuation_upside / portfolio_action

页面底部保留免责声明：「系统仅展示证据与信号，不直接给出投资建议。」

## 15. 测试结果

### compileall

```bash
python3 -m compileall 08_scripts
```

✅ 通过，无语法错误。

### 新增测试

```bash
python3 -m pytest tests/test_dashboard_today_overview.py tests/test_dashboard_signal_flow.py -v
```

✅ **50 passed**（D1 19 + D2 31）

D2 测试覆盖：
- view model 空态不崩溃（None / {}）
- summary 4 卡片结构完整性
- signals 数量限制（≤20）
- hot_entities 聚合逻辑
- source_distribution 聚合逻辑
- 5 个筛选维度（time_range / source_type / entity / strength / q）
- 异常 filter 值不崩溃
- 每条信号字段完整性
- 渲染函数空态正常
- 5 个导航标签全部存在
- 禁用词不出现在渲染 HTML 中
- 筛选栏 5 个筛选项 + 重置按钮存在
- 信号时间线 / 摘要 / 热门对象 / 来源分布 全部存在
- 底部免责声明存在
- 空态文案存在
- 带 filters 参数渲染正常
- 其余 3 个占位页仍然正常
- 今日总览页面仍然正常
- PAGE_RENDERERS 正好 5 个

### 本地启动验证

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

✅ 启动成功：
- `/signals` → HTTP 200，所有模块正常渲染
- `/signals?time_range=24h&source_type=risk_monitor&q=test` → HTTP 200，筛选参数正常解析
- `/` → HTTP 200，今日总览正常
- 导航中「信号流」高亮
- 控制台无异常

### known unrelated failures

- 无（仅运行了 dashboard 相关测试）

## 16. 下一步建议

1. **确认信号流视觉**：建议人工打开 `http://127.0.0.1:8877/signals` 查看视觉效果，确认是否符合效果图预期。
2. **继续 Page 2「覆盖池」或 Page 4「研究队列」**：若信号流确认通过，可选择下一个优先级高的页面施工。
3. **暂缓 Foundation 接入**：当前 view model 已预留清晰的数据输入边界，建议等 5 页 UI 全部稳定后再统一接入 Foundation。
4. **筛选交互增强**：当前筛选需手动提交，后续可考虑改为表单自动提交或 URL 跳转，提升交互体验。
