# SMR-D1 Dashboard 今日总览施工报告

## 1. 执行时间

- 开始：2026-05
- 分支创建基线：`feature/smr-d0-dashboard-audit-blueprint`

## 2. Base Commit

- base branch: `feature/smr-d0-dashboard-audit-blueprint`
- base commit: `916288b` — docs(dashboard): audit and blueprint investment dashboard

## 3. Branch

- work branch: `feature/smr-d1-dashboard-today-overview`

## 4. 当前 Dashboard 启动方式

```bash
cd /Users/apple/Documents/同行资本二级市场
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

访问地址：`http://127.0.0.1:8877/`

## 5. 新增/修改文件

### 新增

| 文件 | 用途 |
|---|---|
| `08_scripts/dashboard/today_overview_view_model.py` | 今日总览 view model，把原始 state 转为页面展示结构 |
| `tests/test_dashboard_today_overview.py` | 今日总览页面测试（19 个用例） |
| `docs/smr_d1_dashboard_today_overview_report.md` | 本报告 |

### 修改

| 文件 | 变更说明 |
|---|---|
| `08_scripts/dashboard/run_control_tower.py` | 更新主导航为 5 页、新增 `render_today_overview` 渲染函数、新增占位页、新增今日总览专属 CSS、更新 `PAGE_RENDERERS` 映射 |
| `docs/smr_d0_dashboard_product_blueprint.md` | 补充 D1 首页施工状态标记 |
| `docs/smr_d0_dashboard_data_mapping.md` | 补充 D1 首页实际数据映射状态 |

## 6. Page 1 今日总览实现范围

| 模块 | 实现状态 | 说明 |
|---|---|---|
| 顶部导航（5 页） | ✅ 实现 | 今日总览 / 覆盖池 / 信号流 / 研究队列 / 数据健康 |
| 页面标题区 | ✅ 实现 | 主标题「今日总览」+ 副标题 |
| 顶部 KPI 4 卡片 | ✅ 实现 | 今日重点变化 / 待判断事项 / 高优先级公司 / 风险提示 |
| 今日最重要的 3 件事 | ✅ 实现 | 左侧主模块，最多 3 条，含空态 |
| 今日待判断 | ✅ 实现 | 右上模块，最多 3 条，含空态 |
| 覆盖池异动 | ✅ 实现 | 右中模块，表格形式，含空态 |
| 数据健康提醒 | ✅ 实现 | 右下模块，3 个小状态，含空态 |
| 页脚更新时间 | ✅ 实现 | 取 state generated_at，fallback 当前时间 |
| 其余 4 页占位 | ✅ 实现 | 返回简洁占位页，提示后续阶段施工 |

## 7. 数据来源映射

| UI 模块 | 当前数据来源 | 缺失时处理 | 后续 Foundation 输入 |
|---|---|---|---|
| 今日重点变化 (KPI) | `state["risk"]["decision"]["sell_candidates"]` 长度 + 风险事件计数 | 显示 0 + 空态副标题 | Foundation: evidence / signals 聚合 |
| 待判断事项 (KPI) | `state["current_state"]["evidence_gaps"]` 长度 | 显示 0 + 空态副标题 | Foundation: review_queue / evidence_gap |
| 高优先级公司 (KPI) | `state["strategy_watch"]["top_focus_items"]` 长度（若存在），或 overview watchlist 估算 | 显示 0 + 空态副标题 | Foundation: coverage priority |
| 风险提示 (KPI) | `state["risk"]["monitor"]` 中风险事件计数（若存在） | 显示 0 + 空态副标题 | Foundation: risk_alerts |
| 今日最重要的 3 件事 | 优先从 sell_candidates + evidence_gaps + risk monitor 聚合排序，最多 3 条 | 空态卡片 + 引导语 | Foundation: top_signals / daily_brief |
| 今日待判断 | evidence_gaps 前 3 条，状态默认「待补证据」 | 空态卡片 | Foundation: review_queue |
| 覆盖池异动 | 从 watchlist / focus items 轻量映射，状态根据现有标签推断 | 空态表格 | Foundation: coverage_status_changes |
| 数据健康提醒 | 固定 3 项（行情新鲜度 / 信息源状态 / Pipeline 状态），当前缺数据显示「暂无数据」 | 全部「暂无数据」badge | Foundation: data_health_metrics |
| 更新时间 | `state["overview"]["generated_at"]` → `state["current_state"]["as_of"]` → 当前时间 | 当前系统时间 fallback | Foundation: snapshot_timestamp |

## 8. 空态设计

所有模块均实现 fail-soft 空态：

- **KPI 卡片**：count = 0，subtitle 使用空态文案（如「暂无今日重点变化」）
- **今日最重要的 3 件事**：显示空态卡片，文案「暂无今日重点变化 / 系统尚未生成足够证据，建议查看信号流或数据健康。」
- **今日待判断**：显示空态卡片，文案「暂无待判断事项 / 当前没有需要人工确认的关键事项。」
- **覆盖池异动**：显示空态表格行，文案「暂无覆盖池异动数据」
- **数据健康提醒**：3 项均显示「暂无数据」badge，状态 tone = ghost

技术保证：`build_today_overview_view_model` 接受 `None` 或空 dict，从不抛出异常。

## 9. 未施工的 4 个页面

| 页面 | 路由 | 当前状态 | 计划阶段 |
|---|---|---|---|
| 覆盖池 | `/coverage` | 占位页 | 后续阶段 |
| 信号流 | `/signals` | 占位页 | 后续阶段 |
| 研究队列 | `/research` | 占位页 | 后续阶段 |
| 数据健康 | `/health` | 占位页 | 后续阶段 |

旧页面的渲染函数仍保留在 `run_control_tower.py` 中（如 `render_home`、`render_operations_page` 等），但不再被主导航引用。

## 10. 是否接入 opc-foundation

**否**。本阶段未接入 `opc-foundation`。所有数据均来自现有 `build_dashboard_state` 输出的 SQLite / JSON snapshot。

## 11. 是否修改投资业务逻辑

**否**。未修改以下任何模块：

- 估值模型
- 预期差模型
- 投资组合 / 仓位 / 风控 / 交易信号逻辑
- 自动化任务

仅修改了 Dashboard 前端渲染层和新增 view model 适配层。

## 12. 是否输出 target price / 买卖建议 / 组合建议

**否**。已通过测试验证以下禁用词不出现在页面渲染中：

- target price / 目标价
- 买入 / 卖出 / 建仓
- 仓位建议 / position_size / trade_signal

页面仅展示事实性信息和待判断事项，不输出任何投资建议。

## 13. 测试结果

### compileall

```bash
python3 -m compileall 08_scripts
```

✅ 通过，无语法错误。

### 新增测试

```bash
python3 -m pytest tests/test_dashboard_today_overview.py -v
```

✅ **19 passed**，覆盖：

- view model 空态不崩溃（None / {}）
- metrics 4 卡片结构完整
- top_changes 最多 3 条
- pending_decisions 最多 3 条
- 覆盖池异动字段完整性
- 数据健康 3 项结构
- 更新时间字段存在
- 渲染函数空态正常
- 5 个导航标签全部存在
- 禁用词不出现在渲染 HTML 中
- 4 个 KPI 卡片标题存在
- 4 个主模块标题存在
- 空态文案存在
- 4 个占位页均能渲染并返回 200

### 本地启动验证

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

✅ 启动成功，所有 5 个路由均返回 HTTP 200：

- `/` → 今日总览
- `/coverage` → 覆盖池占位页
- `/signals` → 信号流占位页
- `/research` → 研究队列占位页
- `/health` → 数据健康占位页

页面包含所有预期模块和导航元素，无 500 错误。

### 已知 unrelated 失败

- 无（本阶段只运行了新增的 dashboard 测试）

## 14. 下一步建议

1. **确认首页视觉**：建议人工打开 `http://127.0.0.1:8877/` 查看视觉效果，确认是否符合预期。
2. **继续 Page 3 信号流效果图**：若首页视觉确认通过，建议进入「信号流」页面的效果图设计或直接施工。
3. **暂缓其余页面**：覆盖池 / 研究队列 / 数据健康可继续保留占位，待首页迭代稳定后再推进。
4. **Foundation 接入准备**：当前 view model 已预留清晰的数据输入边界，后续接入 `opc-foundation` 只需替换适配层输入，无需改动渲染层。
