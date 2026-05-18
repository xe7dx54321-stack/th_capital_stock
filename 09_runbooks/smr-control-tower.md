# SMR 业务看板 Runbook

## 目标

把看板从“系统监控台”改成“业务结果看板”。

新的原则是：

- 不展示系统状态
- 不展示 `registry` 时间线
- 不展示脚本运行日志
- 不把所有信息堆在一个页面
- 一个页面只看一类业务结果

---

## 启动方式

推荐用服务脚本：

```bash
python3 08_scripts/dashboard/control_tower_service.py start --host 127.0.0.1 --port 8877
```

查看状态：

```bash
python3 08_scripts/dashboard/control_tower_service.py status --host 127.0.0.1 --port 8877
```

重启：

```bash
python3 08_scripts/dashboard/control_tower_service.py restart --host 127.0.0.1 --port 8877
```

停止：

```bash
python3 08_scripts/dashboard/control_tower_service.py stop --host 127.0.0.1 --port 8877
```

默认地址：

```text
http://127.0.0.1:8877
```

服务日志：

```text
10_logs/control_tower/control_tower_8877.log
```

进程号文件（pid 文件）：

```text
10_logs/control_tower/control_tower_8877.pid
```

结构化状态接口：

```text
http://127.0.0.1:8877/api/state
```

查看某个产物原文：

```text
http://127.0.0.1:8877/artifact?path=04_portfolio/actions/2026-04-16_portfolio_action_memo.md
```

---

## 页面结构

### `/`

业务导航页。

这里不展开细节，只做分类入口和极简提示。

### `/reports`

日报页。

只看：

- 最新日报
- 今日最重要的结论
- 组合动作主张入口
- 官方一手材料
- 公开电话会文字稿
- 公开卖方参照

### `/research`

研究观察页。

只看：

- 当前高优先级盯盘对象
- 继续观察对象
- 官方一手跟踪
- 电话会文字跟踪
- 策略观察原文入口

### `/portfolio`

调仓动作页。

只看：

- 组合动作主张
- 优先动作
- 优先轮动对
- 调入候选
- 调出参照

### `/risk`

风险结果页。

只看：

- 当前风险结论
- 如果有预警，就只展示预警本身

### `/capital-flow`

资金流页。

只看：

- 两融快照
- 互联互通快照

### `/events`

事件页。

只看：

- 最新事件流
- 事件分布
- 事件日历原文入口

---

## 设计原则

### 1. 业务优先

用户打开页面的目标是看业务结果，不是看系统自己有没有动。

所以页面不再展示：

- `系统脉搏`
- `关键链路状态`
- `today_registry_counts`
- `script_runs`
- `health / freshness` 这类系统面信息

### 2. 分类呈现

不同业务结果拆成不同页面：

- 日报
- 研究
- 调仓
- 风险
- 资金流
- 事件

这样可以避免一页里信息过密、视角混乱。

### 3. 仍保留统一数据底座

虽然前台不再展示系统状态，但底层仍然复用统一聚合状态：

- `task_registry`
- SQLite
- Markdown 产物
- 业务快照 payload

也就是说：

- 前台只看业务结果
- 后台仍保留统一状态出口给后续推送和二次开发

---

## 当前覆盖的数据面

- `daily_reporting_snapshot`
- `strategy_watch_batch`
- `rotation_candidate_snapshot`
- `rotation_execution_plan_snapshot`
- `portfolio_action_memo_snapshot`
- `risk_monitor_snapshot`
- `margin_balance_snapshot`
- `stock_connect_flow_snapshot`
- `market_event_snapshot`
- `event_calendar_snapshot`

---

## 后续增强方向

### P1

- 给研究页加 `ts_code / 主题` 筛选
- 给调仓页加“只看 ready / watch_only”切换
- 给事件页加按标的过滤

### P2

- 把 `/api/state` 里的业务结果直接接到飞书推送
- 每个页面都补“只推送这一类结果”的摘要模板

### P3

- 如果页面复杂度继续上升，再考虑更完整的前端框架
- 但前提仍然是先保证分类清晰、业务结果可读

---

## 故障排查

如果 `Safari` 提示无法连接 `127.0.0.1:8877`，先不要判断成网页坏了，按这个顺序查：

1. 看服务状态

```bash
python3 08_scripts/dashboard/control_tower_service.py status --host 127.0.0.1 --port 8877
```

2. 如果没起来，直接拉起

```bash
python3 08_scripts/dashboard/control_tower_service.py start --host 127.0.0.1 --port 8877
```

3. 如果怀疑端口卡住，直接重启

```bash
python3 08_scripts/dashboard/control_tower_service.py restart --host 127.0.0.1 --port 8877
```

4. 用健康检查确认

```bash
curl http://127.0.0.1:8877/healthz
```

预期返回：

```text
ok
```
