# SMR 日报撰写 Runbook

## 执行时间
每日 20:30

## 执行步骤

### Step 1: 收集数据
1. 读取美股信号: 01_data/us_signals/
2. 读取A股行情: 从数据库查询当日SMR标的表现
3. 读取持仓盈亏: 04_portfolio/performance/
4. 读取风控状态: 05_risk/alerts/
5. 读取研究进展: 02_research/
6. 读取实时股票池: `stock_pool_current`

### Step 2: 生成日报候选层
先刷新日报快照和候选稿：

```bash
python3 08_scripts/reporting/snapshot_daily_reporting.py
```

这一步会：

1. 读取最新策略观察、轮动、组合动作、研究摘要
2. 注册 `daily_reporting_snapshot`
3. 生成 `daily_report_candidate`

### Step 3: 物化正式日报
把候选稿编译成正式人类可读日报：

```bash
python3 08_scripts/reporting/materialize_daily_report.py
```

如需指定日期：

```bash
python3 08_scripts/reporting/materialize_daily_report.py --date 2026-04-19
```

如需同时放入发布队列：

```bash
python3 08_scripts/reporting/materialize_daily_report.py --enqueue-publish
```

### Step 4: 刷新日报快照与源清单
正式日报写入后，再刷新一次快照和 source manifest（源清单）：

```bash
python3 08_scripts/reporting/snapshot_daily_reporting.py
python3 08_scripts/wiki/build_source_manifest.py
```

### Step 5: 附加免责声明
正式日报必须包含风险提示与免责声明。

### Step 6: 正式日报位置
正式日报保存到：

```text
06_reports/daily/YYYY-MM-DD_盘前简报.md
```

### Step 7: 入发布队列（如需推送）
如需推送到微信公众号或其他外部渠道，复制到：

```text
07_publish/queue/
```
