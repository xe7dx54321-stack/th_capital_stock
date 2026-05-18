# SMR 晨间数据管道 Runbook

## 执行时间
每日 06:00-07:00（美股收盘后）

## 执行步骤

### Step 1: 同步种子 universe
```bash
python3 08_scripts/stock_pool/sync_watchlist.py
```

### Step 2: 采集美股行情
```bash
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only
```
等待完成，检查输出中是否有 ERROR。

### Step 3: 采集美股信号
```bash
python3 08_scripts/us_signal_harvester/earnings_monitor.py
```
检查 01_data/us_signals/ 目录是否有新的信号文件。

### Step 4: 计算联动因子
```bash
python3 08_scripts/factor_engine/us_linkage.py
```

### Step 5: 重建动态股票池
- 晨间只在美股信号足够强或昨夜研究更新后触发：
```bash
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
```

### Step 6: 新鲜度检查
```bash
python3 08_scripts/verification/check_data_freshness.py --mode morning
```

### Step 7: 汇报结果
- 美股核心标的涨跌情况
- 是否有重大信号（财报/指引/评级变动）
- 对A+H的预期影响
- 动态池是否有新的 `watchlist / candidate / recommended` 变化

## 异常处理
- 网络超时：等待30秒后重试，最多3次
- 数据缺失：记录到日志，跳过该标的
- API限流：增加间隔到3秒，继续采集
