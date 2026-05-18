# SMR 持仓复盘 Runbook

## 执行时间
每日 19:30

## 执行步骤

### Step 1: 更新盈亏
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/portfolio/pnl.py
```

### Step 1.5: 新开仓门禁
- 新开仓默认只能来自 `stock_pool_current` 中的 `recommended`
- 录入命令必须显式传 `--confirm-recommendation`
- 组合基线资本当前读取 [portfolio_policy.json](/Users/apple/Documents/同行资本二级市场/00_control/portfolio_policy.json)

### Step 2: 读取持仓状态
从数据库读取所有 open 状态的持仓，检查：
- 每笔持仓的当前盈亏
- 是否触及止损价
- 是否达到目标价

### Step 3: Thesis检查
对每笔持仓，检查其投资逻辑是否仍然成立：
- 行业层面：行业趋势是否如预期发展？
- 公司层面：公司基本面是否有重大变化？
- 美股联动：美股对标标的是否有重大事件影响？

### Step 4: 产出调仓建议
- thesis证伪 → 建议无条件止损
- 触及止损 → 建议止损
- 触及目标 → 建议分批止盈
- thesis减弱 → 建议减仓观察
- thesis完好 → 维持持仓

### Step 4.5: 检查组合约束
- 单票仓位是否仍在 `≤25%`
- 行业集中度是否仍在 `≤50%`
- 总暴露是否仍在 `≤90%`

### Step 5: 保存复盘报告
保存到: 04_portfolio/performance/daily_{date}.md
