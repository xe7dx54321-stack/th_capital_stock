# SMR 放大量级研究覆盖 Runbook

**更新日期**：2026-04-15  
**适用范围**：`00_control/research_amplification_registry.md`、外部采集脚本、客观监控扩量运行

---

## 1. 这份文档解决什么问题

这份 runbook（运行手册）解决的是：

- 之前很多外部采集脚本默认只盯 `candidate / recommended`
- 当前真实活跃池只有 `4` 只，最小链能跑，但信息面太窄
- 进入“放大量级”后，需要把采集范围、跟踪范围、分析范围放大，但又不能把正式主链搞乱

所以这一版的做法不是“脚本全部改成全量抓”，而是：

- 先把覆盖策略写进注册表
- 再让脚本统一支持 `--profile / --pool-type / --limit`
- 再用单独标签产出“放大量级观察稿”

---

## 2. 当前三档覆盖策略

注册表文件：

- `00_control/research_amplification_registry.md`

截至 `2026-04-15` 当前解析结果：

| Profile | 当前范围 | 说明 |
|---------|----------|------|
| `standard_external` | `4` 只 A 股 | 历史默认口径，适合低成本日常巡检 |
| `amplified_external` | `34` 只 A 股 | 放大量级采集口径，覆盖 `portfolio_seed + recommended + candidate + watchlist + seed` |
| `amplified_analysis` | `24` 只 A/H 标的 | 放大量级分析口径，适合客观监控和策略观察 |

---

## 3. 统一参数

下面这些脚本现在统一支持：

- `--profile`
  - 从 `research_amplification_registry.md` 读取覆盖策略
- `--pool-type`
  - 手动覆盖池类型，可重复传
- `--limit`
  - 控制本次最多处理多少只标的

当前已接入这组参数的脚本：

- `08_scripts/wiki/fetch_eastmoney_stock_reports.py`
- `08_scripts/wiki/fetch_eastmoney_report_articles.py`
- `08_scripts/wiki/extract_eastmoney_report_pdf_text.py`
- `08_scripts/wiki/extract_eastmoney_report_structured.py`
- `08_scripts/wiki/extract_eastmoney_report_table_structured.py`
- `08_scripts/wiki/fetch_eastmoney_news_search.py`
- `08_scripts/wiki/fetch_eastmoney_news_articles.py`
- `08_scripts/wiki/fetch_cninfo_announcements.py`
- `08_scripts/research/snapshot_stock_objective_monitor.py`

---

## 4. 放大量级采集的正确顺序

这里有一个关键点：

- 搜索页快照先只会落 `raw external`（原始外部来源）
- 下游正文 / PDF / 结构化脚本读取的是 `source_manifest`
- 所以搜索层和详情层之间，必须插一次 `build_source_manifest.py`

推荐顺序：

1. 先抓研报搜索页
2. 先抓资讯搜索页
3. 先抓公告
4. 跑 `build_source_manifest.py`
5. 再抓研报正文 / PDF
6. 再抓资讯正文
7. 再跑一次 `build_source_manifest.py`
8. 再跑 PDF 文本抽取和结构化层
9. 最后再跑客观监控扩量稿

---

## 5. 推荐命令

### 5.1 放大量级外部采集

```bash
python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py --profile amplified_external
python3 08_scripts/wiki/fetch_eastmoney_news_search.py --profile amplified_external --sort time
python3 08_scripts/wiki/fetch_cninfo_announcements.py --profile amplified_external --days-back 30 --per-symbol-limit 2
python3 08_scripts/wiki/build_source_manifest.py
python3 08_scripts/wiki/fetch_eastmoney_report_articles.py --profile amplified_external --report-limit 2
python3 08_scripts/wiki/fetch_eastmoney_news_articles.py --profile amplified_external --article-limit 2
python3 08_scripts/wiki/build_source_manifest.py
python3 08_scripts/wiki/extract_eastmoney_report_pdf_text.py --profile amplified_external --pdf-limit 2
python3 08_scripts/wiki/extract_eastmoney_report_structured.py --profile amplified_external --report-limit 2
python3 08_scripts/wiki/extract_eastmoney_report_table_structured.py --profile amplified_external --report-limit 2
python3 08_scripts/wiki/build_source_manifest.py
```

### 5.2 小规模冒烟

如果只是想先试放大量级，不要一口气全量跑，可以这样：

```bash
python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py --profile amplified_external --limit 4 --per-symbol-limit 1
python3 08_scripts/wiki/fetch_eastmoney_news_search.py --profile amplified_external --limit 3 --per-symbol-limit 1
python3 08_scripts/wiki/build_source_manifest.py
python3 08_scripts/wiki/fetch_eastmoney_news_articles.py --profile amplified_external --limit 2 --article-limit 1
```

### 5.3 放大量级客观监控

如果想单独做更宽范围观察，但不覆盖正式日报主链，可以这样：

```bash
python3 08_scripts/research/snapshot_stock_objective_monitor.py \
  --profile amplified_analysis \
  --limit 24 \
  --label amplified_analysis \
  --skip-handoff
```

这样会新增一个单独文件，例如：

- `02_research/objective_monitor/2026-04-15__amplified_analysis_stock_objective_monitor.md`

而不会覆盖：

- `02_research/objective_monitor/2026-04-15_stock_objective_monitor.md`

---

## 6. 什么时候用哪一档

- 日常轻量巡检：
  - 用 `standard_external`
- 进入放大量级采集：
  - 用 `amplified_external`
- 做更宽范围客观观察和预选：
  - 用 `amplified_analysis`
- 某次只想盯一类池：
  - 直接传 `--pool-type portfolio_seed`
  - 或 `--pool-type recommended --pool-type candidate`

---

## 7. 当前已完成的真实冒烟

截至 `2026-04-15 17:21`，这条扩量链已经有真实冒烟样本：

- `fetch_eastmoney_stock_reports.py --profile amplified_external --limit 4`
  - 成功落 `4` 条研报搜索快照
- `fetch_eastmoney_news_search.py --profile amplified_external --limit 3`
  - 成功落 `3` 条资讯搜索快照
- `build_source_manifest.py`
  - 最新来源清单已更新到 `176` 条
- `fetch_eastmoney_news_articles.py --profile amplified_external --limit 2`
  - 成功落 `2` 条资讯正文快照
- `snapshot_stock_objective_monitor.py --profile amplified_analysis --limit 6 --label amplified_smoke --skip-handoff`
  - 成功落一份单独的放大量级客观监控稿

---

## 8. 当前边界

- 这套扩量只放大“采集范围 / 观察范围 / 分析范围”
- 不直接改 `stock_pool_current`
- 不直接改真实持仓
- 不自动触发更大范围 handoff（交接），除非显式不加 `--skip-handoff`
- 表格结构化这层已经接上，但对个别 PDF 仍可能返回 `table_not_found`

所以当前正确理解是：

- **放大量级已经起步**
- **采集和分析范围已经能按配置放大**
- **但还没有等于“所有扩大量级链路都完全跑满”**
