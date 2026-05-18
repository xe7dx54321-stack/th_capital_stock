# SMR 业务驱动系统自进化 Runbook

**更新日期**：2026-04-17  
**目标**：让系统能根据业务运行中暴露出来的缺口，自动生成工程任务，并在受控门禁下推进开发、审查、验证与提交候选。

---

## 1. 先说结论

这件事可以做，但不能一上来就让系统裸奔去自动改代码。

正确做法是分成 5 层：

1. 业务运行先暴露缺口
2. 缺口先被编译成 `system_change_request`
3. 再交给系统施工执行代理生成 `task spec / patch candidate / validation plan`
4. 再经过测试与审查
5. 最后才允许进入 `commit candidate`

当前第一版已经按这个口径开工：

- 新增了 `system_change_request` 这类 registry（注册表）对象
- 新增了 `hermes_engineering_planner -> openclaw_system_exec` 这条交接链
- 新增了系统自进化门禁策略文件：
  - `00_control/engineering_autonomy_policy.json`
- 截至 2026-04-17，已经能真实生成：
  - `12_smr_agents/workspaces/hermes_engineering_planner/requests/*.md`
  - `12_smr_agents/workspaces/openclaw_system_exec/task_specs/*.md`
  - `12_smr_agents/workspaces/openclaw_system_exec/patch_candidates/*.md`
  - `12_smr_agents/workspaces/openclaw_system_exec/test_runs/*.md`
- 同时会注册：
  - `system_change_request`
  - `system_patch_candidate`
  - `system_validation_snapshot`

---

## 2. 为什么要做

SMR 不是静态系统。

随着业务运行，股票池会动态变化，而新票进来往往会带来新的系统缺口：

- 当前没有覆盖这个票的高价值信息源
- 现有抓取器能抓，但匹配不准
- 新票需要新的 parser（解析器）或 target registry（目标注册表）配置
- 前台面板需要同步增加新类结果展示
- 下游快照、事件层、日报解释链也要补齐

如果这些动作全靠人工盯，就会越来越慢。

所以系统必须具备：

- 自己发现缺口
- 自己生成任务
- 自己拆施工范围
- 自己准备测试与验证计划
- 但仍然在关键门禁上受控

---

## 3. 角色分工

### `hermes_engineering_planner`

负责把业务缺口整理成工程任务单。

它更像“系统产品经理 / 技术规划代理”。

主要产物：

- `system_change_request`

### `openclaw_system_exec`

负责把工程任务落成执行候选物。

它更像“系统施工执行代理”。

主要产物：

- `task spec`
- `patch candidate`
- `validation plan`
- `verification summary`
- `commit candidate`

---

## 4. 当前门禁

当前正式门禁在：

- `00_control/engineering_autonomy_policy.json`

第一版明确限制：

- 允许自动生成工程任务与施工候选
- 允许自动跑安全测试
- 不允许自动提交主分支
- 不允许未经人工审核直接 commit（提交）代码
- 不允许为了单点缺口做无边界重构

一句话说：

- **可以自驱规划和准备施工**
- **不能直接无门禁写正式代码并自动上线**

---

## 5. 最小闭环

```mermaid
flowchart LR
    A["业务运行暴露缺口"] --> B["system_change_request"]
    B --> C["hermes_engineering_planner"]
    C --> D["engineering_execution handoff"]
    D --> E["openclaw_system_exec"]
    E --> F["task_spec / patch_candidate / validation_plan"]
    F --> G["测试与审查"]
    G --> H["commit_candidate (提交候选)"]
```

---

## 6. 第一版落地范围

第一版不追求“自动改代码”，先把下面三件事做扎实：

### 6.1 自动发现缺口

当前优先发现三类缺口：

- 当前股票池或重点跟踪对象，没有进入高价值源 target registry（目标注册表）
- 已经进入 target registry，但 source manifest（源清单）还没有真实覆盖
- 最新抓取任务已经报失败，需要 parser（解析器）或 fetcher（抓取器）修复

### 6.2 自动生成工程任务

每次生成 `system_change_request` 时，要明确：

- 哪个标的
- 哪条能力线
- 为什么触发
- 该改哪些文件
- 该跑哪些测试
- 风险和回滚点是什么

### 6.3 自动生成施工候选

`openclaw_system_exec` 当前只负责生成：

- `task_specs/`
- `patch_candidates/`
- `test_runs/`

不直接改真相层。

这一步的意义不是“系统已经会自己写代码”，而是：

- 它已经会把业务缺口翻译成工程任务
- 会把文件边界、验证命令和验收口径先准备好
- 后面如果真要放开自动改代码，也只能在这层之后、并且继续加门禁

---

## 7. 后续阶段

### P1

- 让 `system_change_request` 能从研究上下文和风险上下文里自动触发
- 让模型 shadow（影子执行）参与任务拆解和 patch 候选补写
- 让本机 `Codex CLI` 作为受控工程执行器接进来，但先只开 `read-only shadow`（只读影子执行）
- 截至 2026-04-17 的实测结论：
  - `Codex CLI shadow` 已能真实拉起和留痕
  - 但 inline（内联）同步执行延迟偏高，当前默认不放进主业务链同步阻塞
  - 下一步更适合做成异步队列或定时批处理能力

### P2

- 新增 `engineering_review`
- 新增 `system_validation_snapshot`
- 把“测试通过”和“代码准备好”拆成两层对象

### P3

- 允许在受控分支上自动 commit candidate（提交候选）
- 但仍不允许自动 merge（合并）主分支

---

## 8. 当前边界

如果你看到系统已经能自动生成工程任务，不要误判成它已经能自主管理整个代码库。

截至当前版本，真实边界是：

- 已具备业务驱动工程任务生成能力
- 已具备系统施工候选链的 runtime（运行时）骨架
- 还没有放开自动 commit 和自动 merge

这不是保守，而是必要门禁。
