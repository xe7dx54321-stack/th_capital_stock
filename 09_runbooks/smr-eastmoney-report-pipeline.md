# SMR 东方财富公开研报快照 Runbook

**更新日期**：2026-04-14  
**适用范围**：A 股公开研报列表快照与原始 JSON 留痕

---

## 1. 这条链做什么

这条链负责把 `东方财富个股研报` 的公开列表抓下来，落到：

- `11_smr_wiki/raw/external/`

并保存：

- 东方财富研报列表原始 JSON
- 研报列表摘要快照
- 查询参数和命中结果元数据

它的定位不是抓单篇研报全文，而是先把“公开研报入口页 / 列表页”变成当前机器可复核来源。

---

## 2. 默认抓取对象

默认抓当前 `stock_pool_current` 里的：

- `candidate`
- `recommended`

且只抓：

- `*.SZ`
- `*.SH`
- `*.BJ`

---

## 3. 命令

默认跑法：

```bash
python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py
python3 08_scripts/wiki/build_source_manifest.py
```

按指定标的抓取：

```bash
python3 08_scripts/wiki/fetch_eastmoney_stock_reports.py \
  --ts-code 300308.SZ \
  --ts-code 002281.SZ \
  --days-back 365 \
  --per-symbol-limit 5
```

---

## 4. 当前实现口径

- 直接调用东方财富公开研报接口 `report/list2`
- 每个标的一次性保存一份“研报列表快照”
- 原始 JSON 会落到本地
- Markdown 快照里会保留最近几条研报的日期、机构、评级、标题、研究员

---

## 5. 结果如何进入系统

抓完后运行：

```bash
python3 08_scripts/wiki/build_source_manifest.py
```

这些快照会进入 `source_manifest`，类型是：

- `external_source_snapshot`

当前默认不会自动转正式知识草稿。

---

## 6. 当前已知限制

- 这条链当前抓的是“研报列表快照”，不是单篇研报正文
- 如果公开接口没有返回当前股票匹配记录，会记成 `empty`，不会乱落库
- 这条链优先解决“研究卡有公开研报入口来源”问题，不等于已经完成正文抽取
- 单篇研报正文和 PDF 原件链，已经拆到单独 runbook：
  - `09_runbooks/smr-eastmoney-report-article-pipeline.md`
- PDF 文本抽取链，已经拆到单独 runbook：
  - `09_runbooks/smr-eastmoney-report-pdf-text-pipeline.md`
- 结构化快照链，已经拆到单独 runbook：
  - `09_runbooks/smr-eastmoney-report-structured-pipeline.md`
- 表格结构化快照链，已经拆到单独 runbook：
  - `09_runbooks/smr-eastmoney-report-table-structured-pipeline.md`

所以它现在的定位是：

- **先把公开研报入口列表留痕链搭起来**
- **先让研究卡能引用当前机器上的公开研报快照**
- **正文详情页和 PDF 原件另走专用链**
- **PDF 文本抽取另走专用链**
- **结构化快照另走专用链**
- **后续继续扩表格结构化覆盖率与事实校验**
