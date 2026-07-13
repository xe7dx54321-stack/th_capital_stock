#!/usr/bin/env python3
"""Deploy Phase 5: Runbooks, backtest, weekly template, prompt-packs, US signal harvester."""

import os

SMR_ROOT = "/Users/apple/Documents/同行资本二级市场"
OPENCLAW_ROOT = "/Users/apple/.openclaw"

files = {}

# ============================================================
# Runbook execution docs (Agent reads these to know what to do)
# ============================================================

files["09_runbooks/smr-morning-data-pipeline.md"] = """# SMR 晨间数据管道 Runbook

## 执行时间
每日 06:00-07:00（美股收盘后）

## 执行步骤

### Step 1: 采集美股行情
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --us-only
```
等待完成，检查输出中是否有 ERROR。

### Step 2: 采集美股信号
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/us_signal_harvester/earnings_monitor.py
```
检查 01_data/us_signals/ 目录是否有新的信号文件。

### Step 3: 计算联动因子
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py
```

### Step 4: 汇报结果
- 美股核心标的涨跌情况
- 是否有重大信号（财报/指引/评级变动）
- 对A+H的预期影响

## 异常处理
- 网络超时：等待30秒后重试，最多3次
- 数据缺失：记录到日志，跳过该标的
- API限流：增加间隔到3秒，继续采集
"""

files["09_runbooks/smr-afternoon-data-pipeline.md"] = """# SMR 午后数据管道 Runbook

## 执行时间
每日 15:30-17:00（A股收盘后）

## 执行步骤

### Step 1: 采集A股行情
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --a-only
```

### Step 2: 采集H股行情
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/data_harvester/ah_daily_bar.py --days 5 --hk-only
```

### Step 3: 计算趋势因子
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/trend.py
```

### Step 4: 计算联动因子
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/factor_engine/us_linkage.py
```

### Step 5: 汇报结果
- A股SMR标的涨跌概况
- 因子计算是否成功
- 是否有趋势信号变化

## 异常处理
- 同晨间管道
"""

files["09_runbooks/smr-portfolio-review.md"] = """# SMR 持仓复盘 Runbook

## 执行时间
每日 19:30

## 执行步骤

### Step 1: 更新盈亏
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/portfolio/pnl.py
```

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

### Step 5: 保存复盘报告
保存到: 04_portfolio/performance/daily_{date}.md
"""

files["09_runbooks/smr-risk-check.md"] = """# SMR 风控检查 Runbook

## 执行时间
每日 21:00

## 执行步骤

### Step 1: 运行风控引擎
```bash
python3 /Users/apple/Documents/同行资本二级市场/08_scripts/risk_engine/monitor.py
```

### Step 2: 检查预警
读取 05_risk/alerts/ 目录，检查是否有新的预警文件。

### Step 3: 检查风控规则
- 单票仓位是否超过25%？
- 组合回撤是否超过15%/20%？
- 行业集中度是否超过50%？
- 是否有thesis证伪的持仓？

### Step 4: 产出风控日报
- 如果有预警：详细说明预警内容和建议动作
- 如果无预警：确认各项指标在安全范围内

### Step 5: 升级处理
- warning级别预警：24小时内未处理则升级为critical
- critical级别预警：4小时内未处理则重新发送
"""

files["09_runbooks/smr-daily-brief-workflow.md"] = """# SMR 日报撰写 Runbook

## 执行时间
每日 20:30

## 执行步骤

### Step 1: 收集数据
1. 读取美股信号: 01_data/us_signals/
2. 读取A股行情: 从数据库查询当日SMR标的表现
3. 读取持仓盈亏: 04_portfolio/performance/
4. 读取风控状态: 05_risk/alerts/
5. 读取研究进展: 02_research/

### Step 2: 撰写日报
按照 smr-daily-brief Skill 的要求，撰写包含以下章节的日报：
1. 美股隔夜动态
2. A股+H股市场概况
3. 持仓盈亏
4. 风控状态
5. 研究进展
6. 明日关注

### Step 3: 附加免责声明
每份日报必须包含风险提示与免责声明。

### Step 4: 保存日报
保存到: 06_reports/daily/daily_brief_{date}.md

### Step 5: 入发布队列（如需推送）
如需推送到微信公众号，复制到: 07_publish/queue/
"""

# ============================================================
# Backtest script
# ============================================================

files["08_scripts/backtest/simple_backtest.py"] = '''#!/usr/bin/env python3
"""SMR Simple Backtest - Validates medium/long-term strategies on historical data."""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db")
REPORT_DIR = Path("/Users/apple/Documents/同行资本二级市场/04_portfolio/performance")


def run_momentum_backtest(conn, ts_code, ma_period=60, hold_days=20):
    import pandas as pd
    df = pd.read_sql(
        "SELECT trade_date, close FROM daily_bar WHERE ts_code=? ORDER BY trade_date",
        conn, params=(ts_code,),
    )
    if len(df) < ma_period + hold_days:
        return None

    df["ma"] = df["close"].rolling(ma_period).mean()
    df["signal"] = (df["close"] > df["ma"]).astype(int)
    df["future_return"] = df["close"].pct_change(hold_days).shift(-hold_days)

    trades = df[df["signal"] == 1].dropna(subset=["future_return"])
    if len(trades) == 0:
        return None

    win_rate = (trades["future_return"] > 0).mean()
    avg_return = trades["future_return"].mean()
    total_trades = len(trades)
    avg_win = trades[trades["future_return"] > 0]["future_return"].mean() if win_rate > 0 else 0
    avg_loss = abs(trades[trades["future_return"] <= 0]["future_return"].mean()) if (1 - win_rate) > 0 else 0.01
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float("inf")

    return {
        "ts_code": ts_code,
        "strategy": f"MA{ma_period}_momentum_hold{hold_days}d",
        "total_trades": total_trades,
        "win_rate": round(win_rate, 4),
        "avg_return": round(avg_return, 4),
        "profit_factor": round(profit_factor, 2),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="SMR Simple Backtest")
    parser.add_argument("--ts-code", help="Specific stock code")
    parser.add_argument("--ma", type=int, default=60, help="MA period")
    parser.add_argument("--hold", type=int, default=20, help="Holding days")
    parser.add_argument("--all", action="store_true", help="Run for all stocks with data")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.ts_code:
        codes = [args.ts_code]
    elif args.all:
        codes = [r[0] for r in conn.execute("SELECT DISTINCT ts_code FROM daily_bar").fetchall()]
    else:
        print("Specify --ts-code or --all")
        return

    results = []
    for code in codes:
        r = run_momentum_backtest(conn, code, args.ma, args.hold)
        if r:
            results.append(r)
            print(f"  {r['ts_code']:12s} trades={r['total_trades']:3d} win={r['win_rate']:.1%} avg_ret={r['avg_return']:.2%} pf={r['profit_factor']:.2f}")

    conn.close()

    if results:
        report_path = REPORT_DIR / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# Backtest Report - {datetime.now().strftime('%Y-%m-%d')}\\n\\n")
            f.write(f"Strategy: MA{args.ma} momentum, hold {args.hold} days\\n\\n")
            f.write("| Stock | Trades | Win Rate | Avg Return | Profit Factor |\\n")
            f.write("|-------|--------|----------|------------|---------------|\\n")
            for r in sorted(results, key=lambda x: x["avg_return"], reverse=True):
                f.write(f"| {r['ts_code']} | {r['total_trades']} | {r['win_rate']:.1%} | {r['avg_return']:.2%} | {r['profit_factor']:.2f} |\\n")
        print(f"\\nReport saved to {report_path}")
    else:
        print("No valid backtest results")


if __name__ == "__main__":
    main()
'''

# ============================================================
# US Signal Harvester script
# ============================================================

files["08_scripts/us_signal_harvester/earnings_monitor.py"] = '''#!/usr/bin/env python3
"""SMR US Earnings Monitor - Checks for new earnings reports and significant events."""

import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db")
SIGNAL_DIR = Path("/Users/apple/Documents/同行资本二级市场/01_data/us_signals")

US_BENCHMARKS = {
    "NVDA": "英伟达", "AMD": "超微半导体", "INTC": "英特尔", "AVGO": "博通",
    "TSLA": "特斯拉", "MU": "美光", "MSFT": "微软",
    "LITE": "Lumentum", "MRVL": "Marvell", "COHR": "Coherent",
    "IONQ": "IonQ", "RGTI": "Rigetti", "QBTS": "D-Wave",
    "CRM": "Salesforce", "NOW": "ServiceNow",
}


def check_price_signals(conn):
    import yfinance as yf
    alerts = []
    for symbol, name in US_BENCHMARKS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if len(hist) < 2:
                continue
            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            pct_chg = (latest["Close"] - prev["Close"]) / prev["Close"] * 100

            if abs(pct_chg) > 3:
                signal_type = "price_surge" if pct_chg > 0 else "price_drop"
                alerts.append({
                    "symbol": symbol,
                    "name": name,
                    "signal_type": signal_type,
                    "title": f"{name}({symbol}) {'大涨' if pct_chg > 0 else '大跌'} {pct_chg:.1f}%",
                    "summary": f"收盘价: ${latest['Close']:.2f}, 成交量: {latest['Volume']:,.0f}",
                    "pct_chg": round(pct_chg, 2),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"  {symbol} {name}: ERROR - {e}")
            time.sleep(1)
    return alerts


def save_signals(conn, alerts):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    SIGNAL_DIR.mkdir(parents=True, exist_ok=True)

    for alert in alerts:
        conn.execute(
            "INSERT INTO us_signal (signal_time, symbol, signal_type, title, summary, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (now, alert["symbol"], alert["signal_type"], alert["title"], alert["summary"], now),
        )

    signal_file = SIGNAL_DIR / f"{datetime.now().strftime('%Y%m%d')}.md"
    with open(signal_file, "a", encoding="utf-8") as f:
        f.write(f"\\n## {now}\\n\\n")
        for a in alerts:
            emoji = "🔴" if a.get("pct_chg", 0) < 0 else "🟢"
            f.write(f"- {emoji} **{a['title']}** — {a['summary']}\\n")

    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    print("Checking US benchmark price signals...")
    alerts = check_price_signals(conn)

    if alerts:
        save_signals(conn, alerts)
        print(f"Found {len(alerts)} significant signals:")
        for a in alerts:
            emoji = "🔴" if a.get("pct_chg", 0) < 0 else "🟢"
            print(f"  {emoji} {a['title']}")
    else:
        print("No significant price signals detected")

    conn.close()


if __name__ == "__main__":
    main()
'''

# ============================================================
# Weekly brief template
# ============================================================

files["09_runbooks/templates/weekly_brief.md"] = """---
report_type: weekly_brief
week_ending: {date}
created_at: {datetime}
---

# 同行资本二级市场周报 — 第{week_number}周（{date_range}）

## 一、本周组合表现

| 指标 | 数值 |
|------|------|
| 组合周收益 | % |
| 同期上证指数 | % |
| 同期科创50 | % |
| 超额收益 | % |
| 持仓数量 | |
| 本周交易次数 | |

## 二、最佳/最差持仓

| 类型 | 股票 | 周涨跌 | 原因 |
|------|------|--------|------|
| 最佳 | | | |
| 最差 | | | |

## 三、Thesis回顾

| 股票 | Thesis | 状态 | 变化 |
|------|--------|------|------|
| | | INTACT/WEAKENED/BROKEN | |

### 本周Thesis变化详情

- 

## 四、行业板块轮动

| 板块 | 本周涨跌 | 趋势判断 | 下周展望 |
|------|---------|---------|---------|
| 具身智能 | | | |
| 半导体/算力 | | | |
| 光模块/CPO | | | |
| AI应用 | | | |
| 量子 | | | |

## 五、美股联动回顾

| 美股标的 | 本周涨跌 | 对A+H影响 |
|---------|---------|-----------|
| NVDA | | |
| TSLA | | |
| AMD | | |

## 六、研究管线

### 本周完成的研究
- 

### 进行中的研究
- 

### 待触发的研究
- 

## 七、下周展望

### 关键事件日历

| 日期 | 事件 | 影响标的 |
|------|------|---------|
| | | |

### 研究优先级
1. 
2. 
3. 

### 持仓调整考虑
- 

---

⚠️ 风险提示与免责声明

本内容仅供研究参考，不构成任何投资建议。股市有风险，投资需谨慎。
过往业绩不代表未来表现。请根据自身风险承受能力独立做出投资决策。
作者及同行资本不对因参考本内容造成的任何投资损失承担责任。
"""

# ============================================================
# Prompt-pack files for key agents
# ============================================================

files["__promptpack_smr_lead__AGENTS.md"] = """# SMR Lead 补充行为规范

## 调度纪律
1. 每日22:00制定次日计划，写入 00_control/dispatch_board.md
2. 研究触发优先级：thesis证伪 > 美股重大信号 > VCR变化 > 用户指定
3. 不在盘前（09:00前）触发任何交易操作
4. 不在盘中（09:30-15:00）干扰其他agent

## 跨业务线交互
- 可以读取 VCR 的 project_cards 和 subsector_strategy_cards（只读）
- 不可以写入 VCR 或 MCT 的任何目录
- 不可以与 VCR/MCT agent 直接通信

## 中长线纪律
- 任何持仓周期建议不得短于1周
- 不因单日涨跌3%以内触发调仓建议
- 趋势判断必须基于周线级别，不看日线
"""

files["__promptpack_smr_researcher__AGENTS.md"] = """# SMR Researcher 补充行为规范

## 研究质量标准
1. 每份研报必须有明确的thesis（投资逻辑），不超过3句话
2. 每份研报必须包含thesis-breaking scenarios（什么会证伪这个逻辑）
3. 美股联动分析必须明确传导路径，不能只说"有影响"
4. 数据来源必须标注，不使用来源不明的数据

## VCR认知复用规则
1. 读取 VCR project_cards 时，只取行业判断和公司定位信息
2. VCR的一级市场估值不直接适用于二级市场定价
3. VCR的thesis变化是研究触发信号，不是研究结论

## 研究边界
- 只研究：具身智能、AI、半导体、量子
- 不研究：能源、消费、家电、金属、地产、银行
- 不产出：K线分析、技术面研报、短线策略
"""

files["__promptpack_smr_advisor__AGENTS.md"] = """# SMR Advisor 补充行为规范

## 推荐纪律
1. 无thesis不推荐 — 每个推荐必须有2-3句话的投资逻辑
2. 无研究不推荐 — 必须有已完成的研报支撑
3. 无趋势不推荐 — 必须有3+因子确认的趋势判断
4. 风控不过不推荐 — critical预警未处理时不开新仓

## 分批建仓规则
- 第一批30%：当前价位
- 第二批40%：回调至支撑位
- 第三批30%：趋势确认后
- 不允许一次性满仓

## 止损规则
- thesis止损优先于技术止损
- thesis证伪 → 无条件止损
- 跌破MA60 → 评估止损
- 跌破MA120 → 建议止损
- 个股亏损>15% → 评估止损

## 禁止词汇
- "保证"、"稳赚"、"确定"、"必然"
- "满仓"、"全仓"、"梭哈"
- "短线"、"打板"、"日内"
"""

files["__promptpack_smr_risk_controller__AGENTS.md"] = """# SMR Risk Controller 补充行为规范

## 独立性原则
1. 风控判断独立于投资决策
2. 不因潜在收益而放松风控规则
3. 不因其他agent的建议而降低预警级别
4. 预警一旦发出，只有用户可以取消

## 预警升级规则
- warning → 24小时未处理 → critical
- critical → 4小时未处理 → 重新发送+紧急标记
- 连续3天同一warning → 自动升级为critical

## 中长线适配
- 回撤容忍度高于短线策略（20% vs 10%）
- 不因单日波动触发预警
- 关注周线级别的趋势破坏，而非日线
- thesis证伪是最高优先级预警
"""

# ============================================================
# Deploy all files
# ============================================================

deployed = 0
for rel_path, content in files.items():
    if rel_path.startswith("__promptpack_"):
        parts = rel_path.replace("__promptpack_", "").split("__")
        agent_id = parts[0].replace("_", "-")
        filename = parts[1]
        target = os.path.join(OPENCLAW_ROOT, f"workspace-{agent_id}", "prompt-pack", filename)
    else:
        target = os.path.join(SMR_ROOT, rel_path)

    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    deployed += 1
    print(f"  ✅ {os.path.relpath(target, '/Users/apple')}")

print(f"\nDeployed {deployed} files")
