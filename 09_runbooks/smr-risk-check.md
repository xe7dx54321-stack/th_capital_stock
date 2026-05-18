# SMR 风控检查 Runbook

## 执行时间
每日 21:00

## 执行步骤

### Step 1: 运行风控引擎
```bash
python3 08_scripts/risk_engine/monitor.py
```

### Step 1.5: 生成买卖决策风控
```bash
python3 08_scripts/risk_engine/build_trade_risk_decision_snapshot.py
```

这一步会把底层报警、执行前检查、策略观察和组合动作收口成老板可读的买卖结论。

### Step 2: 检查预警
读取 05_risk/alerts/ 目录，检查是否有新的预警文件。

同时检查：

- `05_risk/decision/`
- `/risk` 页面

### Step 3: 检查风控规则
- 单票仓位是否超过25%？
- 组合回撤是否超过15%/20%？
- 行业集中度是否超过50%？
- 单周亏损是否超过5%/8%？
- 是否有缺失 thesis / stop / target 的持仓？
- 是否有止损位或目标位被击穿？

### Step 4: 产出风控日报
- 如果有预警：详细说明预警内容和建议动作
- 如果无预警：确认各项指标在安全范围内

### Step 5: 升级处理
- warning级别预警：24小时内未处理则升级为critical
- critical级别预警：4小时内未处理则重新发送

## 沙盒验证

如果要验证“显著真实预警 -> 风险解释 -> reporting 同步 -> dispatch”整条链，而又不污染生产真相层，运行：

```bash
python3 08_scripts/verification/validate_risk_alert_agent_chain.py
```

### 当前风控参数来源
- `00_control/portfolio_policy.json`
