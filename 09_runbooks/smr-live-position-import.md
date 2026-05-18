# SMR 真实持仓最小字段导入 Runbook

## 目标

把“当前真实持仓名单”安全接到 `position` 主表里，让系统可以从 `reference_only` 升级到 `live_positions`。

注意：

- 这条链只用于承接“系统外已有持仓”。
- 以后新增开仓，仍然优先走 `08_scripts/portfolio/entry.py` 的正式门禁。
- 如果你还不准备录入真实持仓，就停在模板和校验阶段，不要执行最终导入。

## Step 1：生成模板

```bash
python3 08_scripts/portfolio/build_live_position_template.py
```

产物：

- `04_portfolio/intake/YYYY-MM-DD_live_position_template.md`
- `04_portfolio/intake/YYYY-MM-DD_live_position_template.json`

## Step 2：填写最小字段

每只票至少补齐：

- `entry_date`
- `entry_price`
- `size_input_type`
- `size_input_value`
- `target_price`
- `stop_loss`
- `thesis`

填写规则：

- `size_input_type=shares`：
  `size_input_value` 填真实股数
- `size_input_type=market_value`：
  `size_input_value` 填建仓成本口径的金额

## Step 3：做导入前校验

```bash
python3 08_scripts/portfolio/validate_live_position_intake.py
```

产物：

- `04_portfolio/intake/YYYY-MM-DD_live_position_validation.md`
- `04_portfolio/intake/YYYY-MM-DD_live_position_validation.json`

校验会检查：

- 日期和价格格式
- `stop_loss < entry_price < target_price`
- `shares / market_value` 是否可推导
- 当前库里是否已有重复 open position
- 当前库里是否有最新行情
- 导入后单票 / 行业 / 总暴露是否超策略线

说明：

- 对“已有真实持仓”来说，`not recommended` 和策略超线会给 warning（警告），但不直接阻塞。
- 真正阻塞的是数据不完整、价格不合法、缺少行情、重复 open position 这类硬问题。

## Step 4：先 dry-run（空跑）

```bash
python3 08_scripts/portfolio/import_live_positions.py --allow-partial
```

默认不写库，只会生成一份 dry-run 导入批次说明。

## Step 5：正式导入

确保下面 3 件事都成立后再执行：

- `position` 主表当前还是空仓
- 校验报告里没有你不能接受的 blocker（阻塞项）
- 你确认这批最小字段就是要写进正式主表的版本

执行：

```bash
python3 08_scripts/portfolio/import_live_positions.py --execute --allow-partial
```

产物：

- `04_portfolio/positions/*.md`
- `04_portfolio/positions/imports/*_live_position_import.md`
- `04_portfolio/positions/imports/*_live_position_import.json`

## Step 6：导入后立刻跑主链

```bash
python3 08_scripts/portfolio/pnl.py
python3 08_scripts/risk_engine/monitor.py
python3 08_scripts/reporting/snapshot_daily_reporting.py
```

如果要继续刷新 agent（代理）侧说明稿和调度预览，再跑：

```bash
python3 08_scripts/agents/run_agent_control_loop.py --build-dispatch
```

## 当前边界

- 只要 `position` 还没写入，`rotation_execution_plan_snapshot` 和 `portfolio_action_memo_snapshot` 就都会停在 `reference_only`。
- 一旦真实持仓导入完成，再重跑执行方案和组合动作建议稿，它们就能切到 `live_positions`。
- 如果要做“全链路沙盒冒烟测试”，优先设置 `SMR_ROOT=/tmp/...`；这样数据库、产物目录、handoff（交接）目录和 workspace（工作区）会一起切到沙盒根目录，而不是只切 DB（数据库）路径。
