# SMR 午后数据管道 Runbook

## 执行时间
每日 15:30-17:00（A股收盘后）

## 执行步骤

### Step 1: 同步种子 universe
```bash
python3 08_scripts/stock_pool/sync_watchlist.py
```

### Step 2: 采集A股行情
```bash
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only
```

### Step 3: 采集H股行情
```bash
python3 08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only
```

### Step 4: 计算趋势因子
```bash
python3 08_scripts/factor_engine/trend.py
```

### Step 5: 计算轻量基本面
```bash
python3 08_scripts/factor_engine/fundamental.py
```

### Step 6: 计算联动因子
```bash
python3 08_scripts/factor_engine/us_linkage.py
```

### Step 7: 生成动态趋势研究
```bash
python3 08_scripts/research/generate_trend_batch.py
```

### Step 8: 重建动态股票池
```bash
python3 08_scripts/stock_pool/reconcile_dynamic_pool.py
```

### Step 9: 新鲜度检查
```bash
python3 08_scripts/verification/check_data_freshness.py --mode afternoon
```

### Step 10: 汇报结果
- A股SMR标的涨跌概况
- 因子计算是否成功
- 是否有趋势信号变化
- 哪些标的进入 / 退出 `watchlist / candidate / recommended`

## 异常处理
- 同晨间管道
